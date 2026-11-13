from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

from app.services.document_ir import (
    Alignment,
    BlockType,
    DocumentIR,
    ImageIR,
    PageIR,
    ParagraphIR,
    TableIR,
)


def _apply_shading(cell, color_hex: str) -> None:
    color = color_hex.lstrip("#").upper()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}"/>')
    cell._tc.get_or_add_tcPr().append(shd)


def _apply_cell_borders(cell, top: bool, bottom: bool, left: bool, right: bool, color: str = "D1D5DB") -> None:
    top_val = "single" if top else "none"
    bot_val = "single" if bottom else "none"
    left_val = "single" if left else "none"
    right_val = "single" if right else "none"
    xml = (
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="{top_val}" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{left_val}" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{bot_val}" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{right_val}" w:sz="4" w:space="0" w:color="{color}"/>'
        f'</w:tcBorders>'
    )
    cell._tc.get_or_add_tcPr().append(parse_xml(xml))


def _set_cell_margins(cell, top: int = 100, bottom: int = 100, left: int = 150, right: int = 150) -> None:
    xml = (
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    cell._tc.get_or_add_tcPr().append(parse_xml(xml))


class DocxReconstructor:
    """Reconstructs a Microsoft Word (.docx) document from a DocumentIR.
    
    Produces genuine editable elements:
    - Real Word tables with proper cell borders, background shading, and column widths
    - True fonts, weights, colors, and paragraph alignments
    - Scaled and embedded images
    - Precise page dimensions and orientation matching the original
    - Native headers and footers
    """

    def __init__(self, doc_ir: DocumentIR):
        self.doc_ir = doc_ir
        self.docx = Document()

    def build(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.doc_ir.pages:
            self.docx.add_paragraph()
            self.docx.save(str(output_path))
            return output_path

        for page_idx, page in enumerate(self.doc_ir.pages):
            section = self.docx.sections[0] if page_idx == 0 else self.docx.add_section(WD_SECTION.NEW_PAGE)

            # Set section geometry
            section.page_width = Pt(page.width)
            section.page_height = Pt(page.height)
            section.orientation = WD_ORIENT.LANDSCAPE if page.orientation == "landscape" else WD_ORIENT.PORTRAIT
            section.top_margin = Pt(max(18.0, min(72.0, page.margin_top)))
            section.bottom_margin = Pt(max(18.0, min(72.0, page.margin_bottom)))
            section.left_margin = Pt(max(18.0, min(72.0, page.margin_left)))
            section.right_margin = Pt(max(18.0, min(72.0, page.margin_right)))

            # Populate header/footer if present
            if page.header:
                hdr_p = section.header.paragraphs[0]
                self._populate_paragraph(hdr_p, page.header[0])
                for extra_p in page.header[1:]:
                    new_p = section.header.add_paragraph()
                    self._populate_paragraph(new_p, extra_p)

            if page.footer:
                ftr_p = section.footer.paragraphs[0]
                self._populate_paragraph(ftr_p, page.footer[0])
                for extra_p in page.footer[1:]:
                    new_p = section.footer.add_paragraph()
                    self._populate_paragraph(new_p, extra_p)

            # Usable page width for placing tables and images
            usable_width_pts = page.width - (section.left_margin.pt + section.right_margin.pt)

            # Populate page body blocks
            for block in page.blocks:
                if block.block_type == BlockType.PARAGRAPH and block.paragraph:
                    p = self.docx.add_paragraph()
                    self._populate_paragraph(p, block.paragraph)

                elif block.block_type == BlockType.TABLE and block.table:
                    self._render_table(block.table, usable_width_pts)

                elif block.block_type == BlockType.IMAGE and block.image:
                    self._render_image(block.image, usable_width_pts)

        self.docx.save(str(output_path))
        return output_path

    def _populate_paragraph(self, docx_p, p_ir: ParagraphIR) -> None:
        if p_ir.alignment == Alignment.CENTER:
            docx_p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif p_ir.alignment == Alignment.RIGHT:
            docx_p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif p_ir.alignment == Alignment.JUSTIFY:
            docx_p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        else:
            docx_p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

        docx_p.paragraph_format.space_before = Pt(p_ir.space_before)
        docx_p.paragraph_format.space_after = Pt(p_ir.space_after)
        docx_p.paragraph_format.line_spacing = p_ir.line_spacing

        for span in p_ir.spans:
            run = docx_p.add_run(span.text)
            run.font.name = span.font_family
            run.font.size = Pt(span.font_size)
            run.bold = span.bold
            run.italic = span.italic
            run.underline = span.underline

            if span.color_hex and span.color_hex != "#000000":
                try:
                    c = span.color_hex.lstrip("#")
                    run.font.color.rgb = RGBColor.from_string(c)
                except Exception:
                    pass

    def _render_table(self, tbl_ir: TableIR, usable_width_pts: float) -> None:
        if not tbl_ir.rows:
            return

        col_count = len(tbl_ir.col_widths)
        if col_count == 0:
            col_count = max(len(r.cells) for r in tbl_ir.rows)
            tbl_ir.col_widths = [usable_width_pts / max(1, col_count)] * col_count

        table = self.docx.add_table(rows=len(tbl_ir.rows), cols=col_count)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Scale columns proportionally if they exceed usable page width
        total_tbl_w = sum(tbl_ir.col_widths)
        scale = 1.0
        if total_tbl_w > usable_width_pts and total_tbl_w > 0:
            scale = usable_width_pts / total_tbl_w

        for i, w in enumerate(tbl_ir.col_widths):
            table.columns[i].width = Pt(w * scale)

        for r_idx, row_ir in enumerate(tbl_ir.rows):
            for c_idx, cell_ir in enumerate(row_ir.cells):
                if c_idx >= col_count:
                    continue
                cell = table.cell(r_idx, c_idx)
                cell.width = Pt(tbl_ir.col_widths[c_idx] * scale)
                _set_cell_margins(cell)

                if cell_ir.background_color:
                    _apply_shading(cell, cell_ir.background_color)

                if tbl_ir.has_borders:
                    _apply_cell_borders(
                        cell,
                        cell_ir.border_top,
                        cell_ir.border_bottom,
                        cell_ir.border_left,
                        cell_ir.border_right,
                    )

                # First paragraph in cell already exists
                first = True
                for p_ir in cell_ir.paragraphs:
                    if first:
                        p = cell.paragraphs[0]
                        first = False
                    else:
                        p = cell.add_paragraph()
                    self._populate_paragraph(p, p_ir)

        # Add a light breathing paragraph after the table
        spacer = self.docx.add_paragraph()
        spacer.paragraph_format.space_before = Pt(0)
        spacer.paragraph_format.space_after = Pt(4)

    def _render_image(self, img_ir: ImageIR, usable_width_pts: float) -> None:
        p = self.docx.add_paragraph()
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(6)

        run = p.add_run()
        # Scale image if larger than page
        img_w = img_ir.width
        img_h = img_ir.height
        if img_w > usable_width_pts and img_w > 0:
            ratio = usable_width_pts / img_w
            img_w = usable_width_pts
            img_h = img_h * ratio

        try:
            run.add_picture(
                io.BytesIO(img_ir.image_bytes),
                width=Pt(img_w),
                height=Pt(img_h),
            )
        except Exception:
            pass


def reconstruct_docx(doc_ir: DocumentIR, output_path: Path) -> Path:
    reconstructor = DocxReconstructor(doc_ir)
    return reconstructor.build(output_path)

