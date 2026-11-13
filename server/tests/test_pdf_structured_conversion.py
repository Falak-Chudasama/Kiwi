from pathlib import Path
import fitz
import pytest
from docx import Document

from app.services.document_ir import DocumentIR, PageIR, ParagraphIR, TextSpanIR, TableIR, TableRowIR, TableCellIR
from app.services.pdf_structured_extract import extract_pdf_ir
from app.services.docx_reconstruct import reconstruct_docx
from app.services.conversion_fidelity import validate_docx_fidelity
from app.services.documents import _pdf_to_docx


def test_pdf_structured_extraction_and_reconstruction(tmp_path: Path):
    # 1. Create a PDF with text, headings, and a native table
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Heading
    page.insert_text(fitz.Point(50, 70), "Kiwi Document Intelligence", fontsize=18, color=(0, 0, 0))
    # Body text
    page.insert_text(fitz.Point(50, 110), "This document verifies local offline conversion reliability.", fontsize=11, color=(0.2, 0.2, 0.2))

    # Draw table border lines
    page.draw_rect(fitz.Rect(50, 140, 450, 220), color=(0.4, 0.4, 0.4), width=1)
    page.draw_line(fitz.Point(50, 170), fitz.Point(450, 170), color=(0.4, 0.4, 0.4), width=1)
    page.draw_line(fitz.Point(200, 140), fitz.Point(200, 220), color=(0.4, 0.4, 0.4), width=1)

    # Insert table text
    page.insert_text(fitz.Point(60, 160), "Feature", fontsize=11)
    page.insert_text(fitz.Point(210, 160), "Status", fontsize=11)
    page.insert_text(fitz.Point(60, 200), "Offline PDF-to-DOCX", fontsize=11)
    page.insert_text(fitz.Point(210, 200), "Verified", fontsize=11)

    pdf_path = tmp_path / "sample.pdf"
    doc.save(str(pdf_path))
    doc.close()

    # 2. Extract structured IR
    doc_ir = extract_pdf_ir(pdf_path)
    assert doc_ir.page_count == 1
    assert "Kiwi Document Intelligence" in doc_ir.full_plain_text
    assert "Offline PDF-to-DOCX" in doc_ir.full_plain_text

    # 3. Reconstruct DOCX
    docx_path = tmp_path / "sample.docx"
    reconstruct_docx(doc_ir, docx_path)
    assert docx_path.exists()
    assert docx_path.stat().st_size > 0

    # 4. Check DOCX contents
    docx_doc = Document(str(docx_path))
    docx_texts = [p.text for p in docx_doc.paragraphs if p.text]
    assert any("Kiwi Document Intelligence" in t for t in docx_texts)

    # 5. Validate conversion fidelity
    report = validate_docx_fidelity(pdf_path, docx_path)
    assert report.text_retention >= 0.80
    assert report.passed is True


def test_pdf_to_docx_fallback_and_integration(tmp_path: Path):
    doc = fitz.open()
    page = doc.new_page(width=500, height=500)
    page.insert_text(fitz.Point(40, 60), "Integration Test Document for Kiwi Converter", fontsize=14)
    pdf_path = tmp_path / "integration.pdf"
    doc.save(str(pdf_path))
    doc.close()

    docx_out = tmp_path / "integration.docx"
    result = _pdf_to_docx(pdf_path, docx_out)
    assert result.exists()
    assert result.stat().st_size > 0

    docx_doc = Document(str(result))
    text_content = " ".join(p.text for p in docx_doc.paragraphs)
    assert "Integration Test Document" in text_content

