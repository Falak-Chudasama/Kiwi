"""Kiwi conversion exceptions and log sanitization.

Ensures sensitive data (passwords, raw document text, absolute local paths)
is redacted from internal logs, while the client receives a safe, actionable error.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger("kiwi.conversion")

# Regex to redact passwords in command arguments
_PASSWORD_PATTERNS = [
    re.compile(r"(--password[= ]\s*)([^\s]+)", re.IGNORECASE),
    re.compile(r"(-P[= ]\s*)([^\s]+)", re.IGNORECASE),
    re.compile(r"(password[=:]\s*[\'\"]?)([^\s\'\"]+)", re.IGNORECASE),
    re.compile(r"(-key[= ]\s*)([^\s]+)", re.IGNORECASE),
]

_USER_PATH_PATTERN = re.compile(
    r"(?:[a-zA-Z]:\\(?:Users|Documents and Settings)\\[^\\]+\\)|(?:/(?:home|Users)/[^/]+/)",
    re.IGNORECASE,
)


def sanitize_text(text: str | None) -> str:
    """Redacts passwords and sensitive user home directory paths from strings."""
    if not text:
        return ""
    sanitized = text
    for pattern in _PASSWORD_PATTERNS:
        sanitized = pattern.sub(r"\1[REDACTED]", sanitized)
    sanitized = _USER_PATH_PATTERN.sub("~/", sanitized)
    return sanitized


def sanitize_command(command: list[str] | None) -> list[str]:
    """Redacts passwords from command-line argument lists."""
    if not command:
        return []
    cleaned: list[str] = []
    redact_next = False
    for arg in command:
        if redact_next:
            cleaned.append("[REDACTED]")
            redact_next = False
            continue

        if arg in ("-P", "--password", "-key"):
            cleaned.append(arg)
            redact_next = True
            continue

        sanitized_arg = sanitize_text(arg)
        cleaned.append(sanitized_arg)
    return cleaned


@dataclass
class ConversionDiagnostics:
    engine: str
    source: str | None = None
    target: str | None = None
    command: list[str] | None = None
    filter_name: str | None = None
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    extra: dict = field(default_factory=dict)

    def log_line(self) -> str:
        parts = [f"engine={self.engine}"]
        if self.source:
            parts.append(f"source=.{self.source.lstrip('.')}")
        if self.target:
            parts.append(f"target=.{self.target.lstrip('.')}")
        if self.filter_name:
            parts.append(f"filter={self.filter_name!r}")
        if self.exit_code is not None:
            parts.append(f"exit={self.exit_code}")
        if self.command:
            sanitized_cmd = sanitize_command(self.command)
            parts.append(f"cmd={sanitized_cmd!r}")
        return " ".join(parts)


class KiwiConversionError(RuntimeError):
    """A conversion failed. `safe_message` is what the frontend sees;
    `diagnostics` is sanitized and logged internally.
    """

    def __init__(self, safe_message: str, diagnostics: ConversionDiagnostics | None = None):
        super().__init__(safe_message)
        self.safe_message = safe_message
        self.diagnostics = diagnostics
        if diagnostics is not None:
            sanitized_stdout = sanitize_text(diagnostics.stdout or "")[-500:]
            sanitized_stderr = sanitize_text(diagnostics.stderr or "")[-500:]
            logger.error(
                "%s | %s\n--- stdout ---\n%s\n--- stderr ---\n%s",
                safe_message,
                diagnostics.log_line(),
                sanitized_stdout,
                sanitized_stderr,
            )
        else:
            logger.error(safe_message)


class UnsupportedConversionError(KiwiConversionError):
    """The requested source -> target pair has no valid strategy."""


class OutputValidationError(KiwiConversionError):
    """An engine claimed success but produced an invalid or empty file."""
