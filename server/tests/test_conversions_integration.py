import io
import tempfile
from pathlib import Path
import pytest
from PIL import Image

from app.services.universal import convert_any
from app.services.compression import compress_file, CompressionLevel
from app.services.archives import create_archive, extract_archive

def test_convert_text_to_images(tmp_path: Path):
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Kiwi Universal Converter\nLine 1\nLine 2\nLine 3", encoding="utf-8")

    out_dir = tmp_path / "out_img"
    results = convert_any(txt_file, "png", out_dir)
    assert len(results) == 1
    assert results[0].exists()
    assert results[0].suffix == ".png"
    assert results[0].stat().st_size > 0

def test_convert_text_to_spreadsheet(tmp_path: Path):
    table_txt = tmp_path / "table.md"
    table_txt.write_text("| Name | Role | Score |\n|---|---|---|\n| Kiwi | Assistant | 100 |\n| User | Lead | 100 |", encoding="utf-8")

    out_dir = tmp_path / "out_sheet"
    results = convert_any(table_txt, "csv", out_dir)
    assert len(results) == 1
    assert results[0].exists()
    assert "Kiwi,Assistant,100" in results[0].read_text(encoding="utf-8-sig")

def test_convert_image_to_pdf(tmp_path: Path):
    img = Image.new("RGB", (100, 100), color="green")
    img_path = tmp_path / "photo.jpg"
    img.save(img_path, format="JPEG")

    out_dir = tmp_path / "out_pdf"
    results = convert_any(img_path, "pdf", out_dir)
    assert len(results) == 1
    assert results[0].exists()
    assert results[0].suffix == ".pdf"
    assert results[0].stat().st_size > 0

def test_compression_png_never_larger(tmp_path: Path):
    img = Image.new("RGB", (200, 200), color="yellow")
    img_path = tmp_path / "compress_me.png"
    img.save(img_path, format="PNG")

    out_dir = tmp_path / "out_comp"
    result = compress_file(img_path, out_dir, CompressionLevel.HIGH)
    assert result.exists()
    assert result.stat().st_size <= img_path.stat().st_size

def test_compression_office_repack(tmp_path: Path):
    # Create a small valid docx using python-docx
    from docx import Document
    doc = Document()
    doc.add_heading("Compression Test", 0)
    doc.add_paragraph("Testing office compression with media and xml.")
    docx_path = tmp_path / "document.docx"
    doc.save(docx_path)

    out_dir = tmp_path / "out_office_comp"
    result = compress_file(docx_path, out_dir, CompressionLevel.EXTREME)
    assert result.exists()
    assert result.stat().st_size <= docx_path.stat().st_size

def test_pdf_to_markdown_and_tables(tmp_path: Path):
    import fitz
    doc = fitz.open()
    page = doc.new_page(width=300, height=300)
    page.insert_text(fitz.Point(30, 50), "Hello Kiwi Structured Markdown")
    pdf_path = tmp_path / "input.pdf"
    doc.save(pdf_path)
    doc.close()

    out_dir = tmp_path / "out_md"
    results = convert_any(pdf_path, "txt", out_dir)
    assert len(results) == 1
    assert "Hello Kiwi Structured Markdown" in results[0].read_text(encoding="utf-8")


def test_convert_sheet_to_docx(tmp_path: Path):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["Item", "Count", "Price"])
    ws.append(["Apples", 10, 2.5])
    xlsx_path = tmp_path / "inventory.xlsx"
    wb.save(xlsx_path)

    out_dir = tmp_path / "out_sheet_docx"
    results = convert_any(xlsx_path, "docx", out_dir)
    assert len(results) == 1
    assert results[0].exists()
    assert results[0].suffix == ".docx"
    assert results[0].stat().st_size > 0

    from docx import Document
    doc = Document(str(results[0]))
    assert len(doc.tables) == 1
    assert doc.tables[0].cell(0, 0).text == "Item"
    assert doc.tables[0].cell(1, 0).text == "Apples"


def test_convert_csv_to_docx(tmp_path: Path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("Month,Visitors\nJan,1000\nFeb,1500\n", encoding="utf-8")

    out_dir = tmp_path / "out_csv_docx"
    results = convert_any(csv_path, "docx", out_dir)
    assert len(results) == 1
    assert results[0].exists()
    assert results[0].suffix == ".docx"
    assert results[0].stat().st_size > 0

