"""Kiwi-specific conversion exceptions.

Replaces bare `subprocess.CalledProcessError` / generic `RuntimeError`
propagation with a structured error that keeps full diagnostics (command,
exit code, stdout/stderr, engine, source/target) for the server log while
exposing only a short, safe message to the frontend.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("kiwi.conversion")


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
            parts.append(f"source=.{self.source}")
        if self.target:
            parts.append(f"target=.{self.target}")
        if self.filter_name:
            parts.append(f"filter={self.filter_name!r}")
        if self.exit_code is not None:
            parts.append(f"exit={self.exit_code}")
        if self.command:
            parts.append(f"cmd={self.command!r}")
        return " ".join(parts)


class KiwiConversionError(RuntimeError):
    """A conversion failed. `safe_message` is what the frontend sees;
    `diagnostics` (with full stdout/stderr/command) is logged internally
    and never sent to the client.
    """

    def __init__(self, safe_message: str, diagnostics: ConversionDiagnostics | None = None):
        super().__init__(safe_message)
        self.safe_message = safe_message
        self.diagnostics = diagnostics
        if diagnostics is not None:
            logger.error(
                "%s | %s\n--- stdout ---\n%s\n--- stderr ---\n%s",
                safe_message,
                diagnostics.log_line(),
                (diagnostics.stdout or "")[-4000:],
                (diagnostics.stderr or "")[-4000:],
            )
        else:
            logger.error(safe_message)


class UnsupportedConversionError(KiwiConversionError):
    """The requested source -> target pair has no valid strategy at all
    (as opposed to a strategy that exists but failed at runtime)."""


class OutputValidationError(KiwiConversionError):
    """A conversion engine returned success but the output file failed
    validation (missing, wrong extension, empty, or unopenable)."""
