"""Kiwi Professional Offline Document Scanner Subsystem.

Provides modular image analysis, boundary detection, geometric perspective correction,
curved-page dewarping, non-destructive image enhancement, presets, OCR, and searchable PDF generation.
"""

from app.services.scanner.pipeline import scan_pipeline, ScanResult, PageScanRequest

__all__ = ["scan_pipeline", "ScanResult", "PageScanRequest"]

