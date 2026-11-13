from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz
from docx import Document

from app.core.config import settings
from app.core.files import command_path
from app.services.office_engine import run_soffice_convert


def _has_soffice() -> bool:
    return bool(
        command_path(
            settings.soffice_bin if hasattr(settings, "soffice_bin") else "soffice",
            [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ],
        )
    )


@dataclass
class FidelityReport:
    overall_score: float  # 0.0 to 1.0
    text_retention: float  # 0.0 to 1.0
    image_retention: float  # 0.0 to 1.0
    table_retention: float  # 0.0 to 1.0
    page_count_match: bool
    original_pages: int
    converted_pages: int
    missing_images: int
    passed: bool
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 3),
            "text_retention": round(self.text_retention, 3),
            "image_retention": round(self.image_retention, 3),
            "table_retention": round(self.table_retention, 3),
            "page_count_match": self.page_count_match,
            "original_pages": self.original_pages,
            "converted_pages": self.converted_pages,
            "missing_images": self.missing_images,
            "passed": self.passed,
            "warnings": self.warnings,
            "details": self.details,
        }


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"\b\w{2,}\b", text.lower())
    return set(words)


class ConversionFidelityValidator:
    """Validates that a converted DOCX document faithfully represents the original PDF."""

    def __init__(self, original_pdf: Path, converted_docx: Path):
        self.original_pdf = original_pdf
        self.converted_docx = converted_docx

    def validate(self) -> FidelityReport:
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        # 1. Original PDF extraction
        orig_doc = fitz.open(self.original_pdf)
        orig_pages = len(orig_doc)
        orig_text_parts: List[str] = []
        orig_image_count = 0
        orig_table_count = 0

        for page in orig_doc:
            orig_text_parts.append(page.get_text("text"))
            orig_image_count += len(page.get_images())
            try:
                tables = page.find_tables()
                if tables and tables.tables:
                    orig_table_count += len(tables.tables)
            except Exception:
                pass
        orig_doc.close()

        orig_full_text = " ".join(orig_text_parts).strip()
        orig_tokens = _tokenize(orig_full_text)

        # 2. Converted DOCX extraction
        docx_doc = Document(str(self.converted_docx))
        docx_text_parts: List[str] = []
        for p in docx_doc.paragraphs:
            if p.text.strip():
                docx_text_parts.append(p.text)

        docx_table_count = len(docx_doc.tables)
        for tbl in docx_doc.tables:
            for row in tbl.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        docx_text_parts.append(cell.text)

        # Count images in DOCX package
        docx_image_count = 0
        try:
            for rel in docx_doc.part.rels.values():
                if "image" in rel.target_ref.lower():
                    docx_image_count += 1
        except Exception:
            pass

        docx_full_text = " ".join(docx_text_parts).strip()
        docx_tokens = _tokenize(docx_full_text)

        # 3. Calculate text retention
        if not orig_tokens:
            text_retention = 1.0  # Image-only PDF
        else:
            intersection = orig_tokens.intersection(docx_tokens)
            text_retention = len(intersection) / len(orig_tokens)

        if text_retention < 0.75:
            missing_words = list(orig_tokens - docx_tokens)[:10]
            warnings.append(f"Text retention is {text_retention:.1%}. Potential missing keywords: {missing_words}")

        # 4. Calculate image retention
        if orig_image_count == 0:
            image_retention = 1.0
            missing_images = 0
        else:
            missing_images = max(0, orig_image_count - docx_image_count)
            image_retention = min(1.0, docx_image_count / orig_image_count)
            if missing_images > 0:
                warnings.append(f"{missing_images} embedded image(s) may not have transferred to DOCX.")

        # 5. Calculate table retention
        if orig_table_count == 0:
            table_retention = 1.0
        else:
            table_retention = min(1.0, docx_table_count / orig_table_count)
            if docx_table_count < orig_table_count:
                warnings.append(f"Detected {orig_table_count} tables in source but only {docx_table_count} in DOCX.")

        # 6. Page count comparison via LibreOffice rendering (if available)
        converted_pages = len(docx_doc.sections)
        page_count_match = (converted_pages == orig_pages)

        if _has_soffice():
            try:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    rendered_pdf = Path(tmp_dir) / f"{self.converted_docx.stem}.pdf"
                    run_soffice_convert(self.converted_docx, "pdf", Path(tmp_dir))
                    if rendered_pdf.exists():
                        rend_doc = fitz.open(rendered_pdf)
                        rendered_page_count = len(rend_doc)
                        rend_doc.close()
                        converted_pages = rendered_page_count
                        page_count_match = (rendered_page_count == orig_pages)
                        if not page_count_match:
                            warnings.append(
                                f"Page count mismatch: original has {orig_pages} pages, converted renders {rendered_page_count} pages."
                            )
            except Exception as exc:
                details["rendering_validation_skipped"] = str(exc)

        # 7. Compute weighted overall score
        # 50% text retention, 25% table retention, 15% image retention, 10% page match
        page_score = 1.0 if page_count_match else max(0.5, 1.0 - abs(orig_pages - converted_pages) * 0.1)
        overall_score = (
            text_retention * 0.50
            + table_retention * 0.25
            + image_retention * 0.15
            + page_score * 0.10
        )

        passed = overall_score >= 0.70 and text_retention >= 0.70

        details["orig_word_count"] = len(orig_full_text.split())
        details["docx_word_count"] = len(docx_full_text.split())
        details["orig_image_count"] = orig_image_count
        details["docx_image_count"] = docx_image_count

        return FidelityReport(
            overall_score=overall_score,
            text_retention=text_retention,
            image_retention=image_retention,
            table_retention=table_retention,
            page_count_match=page_count_match,
            original_pages=orig_pages,
            converted_pages=converted_pages,
            missing_images=missing_images,
            passed=passed,
            warnings=warnings,
            details=details,
        )


def validate_docx_fidelity(original_pdf: Path, converted_docx: Path) -> FidelityReport:
    validator = ConversionFidelityValidator(original_pdf, converted_docx)
    return validator.validate()
