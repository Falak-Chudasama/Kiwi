"""Font-family resolution for PDF -> DOCX/PPTX/HTML conversion.

PDF embeds font names like "ArialMT", "Calibri-Bold", "TimesNewRomanPSMT",
"ABCDEF+Georgia". Downstream targets (Word, PowerPoint, CSS) want a clean
family name plus separate bold/italic flags. Previously this pipeline
hard-coded "Arial" for every run; that silently destroys typography (a
serif document becomes sans-serif) and throws off text width, which cascades
into layout drift. This module maps PDF font names to their real family and
weight/style, so only fonts genuinely unavailable on the system fall back --
and even then, to a metric-compatible relative (serif->Georgia/Times,
sans->Arial/Calibri, mono->Consolas), not unconditionally to Arial.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Fonts virtually guaranteed to be present on Windows/Mac/most Linux desktops
# (either natively or via LibreOffice's bundled metric-compatible set).
_COMMON_SANS = {"arial", "helvetica", "calibri", "segoe ui", "verdana", "tahoma"}
_COMMON_SERIF = {"times new roman", "georgia", "cambria", "garamond", "book antiqua"}
_COMMON_MONO = {"courier new", "consolas", "lucida console"}

# Known PDF subset/alias patterns -> clean family name.
_ALIASES: dict[str, str] = {
    "arialmt": "Arial",
    "arial-boldmt": "Arial",
    "arial-italicmt": "Arial",
    "arial-bolditalicmt": "Arial",
    "timesnewromanpsmt": "Times New Roman",
    "timesnewromanps-boldmt": "Times New Roman",
    "timesnewromanps-italicmt": "Times New Roman",
    "timesnewromanps-bolditalicmt": "Times New Roman",
    "helvetica": "Helvetica",
    "helvetica-bold": "Helvetica",
    "helvetica-oblique": "Helvetica",
    "calibri": "Calibri",
    "calibri-bold": "Calibri",
    "cambria": "Cambria",
    "cambria-bold": "Cambria",
    "georgia": "Georgia",
    "verdana": "Verdana",
    "couriernew": "Courier New",
    "courier": "Courier New",
    "consolas": "Consolas",
}


@dataclass
class ResolvedFont:
    family: str  # family name to write into the output document
    bold: bool
    italic: bool
    original: str  # raw PDF font name, for diagnostics
    substituted: bool  # true if `family` differs from the source's real family


def _strip_subset_prefix(name: str) -> str:
    # Embedded subset fonts are named like "ABCDEF+Georgia".
    return re.sub(r"^[A-Z]{6}\+", "", name)


def _classify(base: str) -> str:
    """Return 'serif', 'sans', or 'mono' based on family name heuristics."""
    lower = base.lower()
    if any(k in lower for k in ("mono", "courier", "consolas", "typewriter")):
        return "mono"
    if any(k in lower for k in ("times", "georgia", "serif", "garamond", "cambria", "book antiqua", "minion", "palatino")):
        return "serif"
    return "sans"


def resolve_font(pdf_font_name: str, flags: int = 0) -> ResolvedFont:
    """Resolve a PDF font name (as reported by PyMuPDF span['font']) into a
    family name plus bold/italic, applying a metric-compatible substitution
    only when the exact family isn't a common system font.

    `flags` is PyMuPDF's span bitfield (bit 0 = superscript, bit 1 = italic,
    bit 4 = bold, ...); when the caller has it, it's more reliable than
    parsing "Bold"/"Italic" out of the name string alone.
    """
    original = pdf_font_name or "Helvetica"
    stripped = _strip_subset_prefix(original)
    lower_key = stripped.lower().replace(" ", "")

    bold = bool(flags & 2**4) if flags else False
    italic = bool(flags & 2**1) if flags else False
    if not bold:
        bold = bool(re.search(r"bold|black|heavy", stripped, re.I))
    if not italic:
        italic = bool(re.search(r"italic|oblique", stripped, re.I))

    # Try direct alias match first (strip weight/style tokens for lookup).
    base_key = re.sub(r"[-, ]?(bold|italic|oblique|regular|mt|ps)+", "", lower_key, flags=re.I)
    mapped = _ALIASES.get(lower_key) or _ALIASES.get(base_key)

    if mapped:
        return ResolvedFont(family=mapped, bold=bold, italic=italic, original=original, substituted=False)

    # Clean the raw name into a plausible family (strip weight/style words).
    clean = re.sub(r"[-_](bold|italic|oblique|regular|light|medium|semibold|black)", "", stripped, flags=re.I)
    clean = clean.strip() or "Helvetica"

    if clean.lower() in _COMMON_SANS | _COMMON_SERIF | _COMMON_MONO:
        return ResolvedFont(family=clean, bold=bold, italic=italic, original=original, substituted=False)

    # Not a known system font -- substitute by classification rather than
    # collapsing everything to Arial. This keeps serif documents serif and
    # monospace documents monospace, which preserves both the visual "feel"
    # and (roughly) the text metrics used for word-wrap width.
    cls = _classify(clean)
    substitute = {"serif": "Times New Roman", "mono": "Courier New", "sans": "Arial"}[cls]
    return ResolvedFont(family=substitute, bold=bold, italic=italic, original=original, substituted=True)
