from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import fitz

from app.services.document_ir import (
    Alignment,
    BlockIR,
    BlockType,
    DocumentIR,
    DrawingPathIR,
    ImageIR,
    PageIR,
    ParagraphIR,
    TableCellIR,
    TableIR,
    TableRowIR,
    TextSpanIR,
    VectorDrawingIR,
)
from app.services.pdf_analysis import analyze_pdf
from app.services.pdf_fonts import resolve_font
from app.services.pdf_ocr import ocr_available, ocr_lines


def _color_to_hex(color_int: Any) -> str:
    if isinstance(color_int, int):
        return f"#{color_int:06x}"
    if isinstance(color_int, (list, tuple)):
        if len(color_int) >= 3:
            r = int(color_int[0] * 255) if isinstance(color_int[0], float) and color_int[0] <= 1.0 else int(color_int[0])
            g = int(color_int[1] * 255) if isinstance(color_int[1], float) and color_int[1] <= 1.0 else int(color_int[1])
            b = int(color_int[2] * 255) if isinstance(color_int[2], float) and color_int[2] <= 1.0 else int(color_int[2])
            return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"
    return "#000000"


def _bbox_intersects(b1: Tuple[float, float, float, float], b2: Tuple[float, float, float, float], tolerance: float = 2.0) -> bool:
    return not (
        b1[2] < b2[0] - tolerance
        or b1[0] > b2[2] + tolerance
        or b1[3] < b2[1] - tolerance
        or b1[1] > b2[3] + tolerance
    )


def _bbox_inside(inner: Tuple[float, float, float, float], outer: Tuple[float, float, float, float], tolerance: float = 4.0) -> bool:
    return (
        inner[0] >= outer[0] - tolerance
        and inner[1] >= outer[1] - tolerance
        and inner[2] <= outer[2] + tolerance
        and inner[3] <= outer[3] + tolerance
    )


class PdfStructuredExtractor:
    """Extracts a PDF into a high-fidelity DocumentIR representation.
    
    Preserves text spans, exact font properties, colors, bounding boxes,
    reconstructed native tables, raster images with reuse caching,
    vector drawing shapes, and layout structure.
    """

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self._image_cache: Dict[int, Tuple[bytes, str]] = {}

    def extract(self) -> DocumentIR:
        doc = fitz.open(self.pdf_path)
        try:
            analysis = analyze_pdf(self.pdf_path)
            ocr_pages = set(analysis.ocr_page_indices) if (analysis.requires_ocr and ocr_available()) else set()

            metadata = doc.metadata or {}
            doc_ir = DocumentIR(
                title=metadata.get("title"),
                author=metadata.get("author"),
                creator=metadata.get("creator"),
            )

            for page_idx, page in enumerate(doc):
                needs_ocr = page_idx in ocr_pages
                page_ir = self._extract_page(doc, page, page_idx + 1, needs_ocr)
                doc_ir.pages.append(page_ir)

            return doc_ir
        finally:
            doc.close()

    def _extract_page(self, doc: fitz.Document, page: fitz.Page, page_num: int, needs_ocr: bool) -> PageIR:
        rect = page.rect
        width = float(rect.width)
        height = float(rect.height)
        rotation = page.rotation
        orientation = "landscape" if width > height else "portrait"

        page_ir = PageIR(
            page_number=page_num,
            width=width,
            height=height,
            orientation=orientation,
            margin_top=round(height * 0.08, 1),
            margin_bottom=round(height * 0.08, 1),
            margin_left=round(width * 0.08, 1),
            margin_right=round(width * 0.08, 1),
        )

        table_irs, table_bboxes = self._extract_tables(page)
        image_irs, image_bboxes = self._extract_images(doc, page)
        drawing_irs = self._extract_drawings(page, table_bboxes)

        text_blocks = self._extract_text_blocks(page, needs_ocr, table_bboxes)

        # Separate headers and footers
        header_blocks: List[ParagraphIR] = []
        footer_blocks: List[ParagraphIR] = []
        body_blocks: List[BlockIR] = []

        for p_ir in text_blocks:
            top_y = p_ir.bbox[1]
            bot_y = p_ir.bbox[3]
            if bot_y < page_ir.margin_top and len(p_ir.spans) > 0 and len(p_ir.plain_text) < 120:
                header_blocks.append(p_ir)
            elif top_y > (height - page_ir.margin_bottom) and len(p_ir.spans) > 0 and len(p_ir.plain_text) < 120:
                footer_blocks.append(p_ir)
            else:
                body_blocks.append(BlockIR(
                    block_type=BlockType.PARAGRAPH,
                    bbox=p_ir.bbox,
                    paragraph=p_ir,
                ))

        if header_blocks:
            page_ir.header = header_blocks
        if footer_blocks:
            page_ir.footer = footer_blocks

        # Add tables to body blocks
        for tbl in table_irs:
            body_blocks.append(BlockIR(
                block_type=BlockType.TABLE,
                bbox=tbl.bbox,
                table=tbl,
            ))

        # Add images to body blocks
        for img in image_irs:
            body_blocks.append(BlockIR(
                block_type=BlockType.IMAGE,
                bbox=img.bbox,
                image=img,
            ))

        # Add vector drawings to body blocks
        for drw in drawing_irs:
            body_blocks.append(BlockIR(
                block_type=BlockType.DRAWING,
                bbox=drw.bbox,
                drawing=drw,
            ))

        # Sort body blocks in reading order: top-to-bottom, left-to-right
        body_blocks.sort(key=lambda b: (round(b.bbox[1] / 12.0) * 12.0, b.bbox[0]))
        page_ir.blocks = body_blocks

        return page_ir

    def _extract_tables(self, page: fitz.Page) -> Tuple[List[TableIR], List[Tuple[float, float, float, float]]]:
        table_irs: List[TableIR] = []
        bboxes: List[Tuple[float, float, float, float]] = []

        try:
            tab_finder = page.find_tables()
            if tab_finder and tab_finder.tables:
                for tab in tab_finder.tables:
                    t_bbox = (float(tab.bbox[0]), float(tab.bbox[1]), float(tab.bbox[2]), float(tab.bbox[3]))
                    bboxes.append(t_bbox)

                    # Extract rows and cells
                    raw_data = tab.extract()
                    if not raw_data:
                        continue

                    col_count = len(raw_data[0]) if raw_data else 0
                    if col_count == 0:
                        continue

                    table_width = t_bbox[2] - t_bbox[0]
                    col_width = table_width / max(1, col_count)
                    col_widths = [col_width] * col_count

                    rows_ir: List[TableRowIR] = []
                    for r_idx, row_values in enumerate(raw_data):
                        cells_ir: List[TableCellIR] = []
                        for c_idx, val in enumerate(row_values):
                            text_content = str(val or "").strip()
                            span = TextSpanIR(
                                text=text_content,
                                font_family="Calibri",
                                font_size=10.0,
                                bold=(r_idx == 0),
                            )
                            para = ParagraphIR(
                                spans=[span] if text_content else [],
                                alignment=Alignment.LEFT,
                                space_after=2.0,
                            )
                            cell = TableCellIR(
                                row_idx=r_idx,
                                col_idx=c_idx,
                                paragraphs=[para],
                                background_color="#F3F4F6" if r_idx == 0 else None,
                            )
                            cells_ir.append(cell)
                        rows_ir.append(TableRowIR(
                            cells=cells_ir,
                            is_header=(r_idx == 0),
                        ))

                    table_irs.append(TableIR(
                        rows=rows_ir,
                        col_widths=col_widths,
                        bbox=t_bbox,
                        has_borders=True,
                    ))
        except Exception:
            pass

        return table_irs, bboxes

    def _extract_images(self, doc: fitz.Document, page: fitz.Page) -> Tuple[List[ImageIR], List[Tuple[float, float, float, float]]]:
        image_irs: List[ImageIR] = []
        bboxes: List[Tuple[float, float, float, float]] = []

        try:
            infos = page.get_image_info(xrefs=True)
        except Exception:
            infos = []

        for info in infos:
            xref = info.get("xref")
            bbox = info.get("bbox")
            if not bbox or not xref:
                continue
            t_bbox = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
            width = max(10.0, t_bbox[2] - t_bbox[0])
            height = max(10.0, t_bbox[3] - t_bbox[1])

            # Ignore tiny icon artifacts like < 4x4 px
            if width < 4.0 or height < 4.0:
                continue

            bboxes.append(t_bbox)

            if xref in self._image_cache:
                img_bytes, ext = self._image_cache[xref]
            else:
                try:
                    pix = doc.extract_image(xref)
                    img_bytes = pix.get("image")
                    ext = pix.get("ext", "png")
                    if img_bytes:
                        self._image_cache[xref] = (img_bytes, ext)
                    else:
                        continue
                except Exception:
                    continue

            image_irs.append(ImageIR(
                image_bytes=img_bytes,
                ext=ext,
                bbox=t_bbox,
                width=width,
                height=height,
                xref=xref,
            ))

        return image_irs, bboxes

    def _extract_drawings(self, page: fitz.Page, table_bboxes: List[Tuple[float, float, float, float]]) -> List[VectorDrawingIR]:
        drawing_irs: List[VectorDrawingIR] = []
        try:
            drawings = page.get_drawings()
        except Exception:
            drawings = []

        for d in drawings:
            rect = d.get("rect")
            if not rect:
                continue
            d_bbox = (float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))

            # Ignore drawing elements that are part of detected tables
            if any(_bbox_intersects(d_bbox, t_box) for t_box in table_bboxes):
                continue

            # Skip tiny noise or huge page backgrounds
            d_w = d_bbox[2] - d_bbox[0]
            d_h = d_bbox[3] - d_bbox[1]
            if (d_w < 2.0 and d_h < 2.0) or (d_w >= page.rect.width * 0.98 and d_h >= page.rect.height * 0.98):
                continue

            stroke = _color_to_hex(d.get("color")) if d.get("color") else None
            fill = _color_to_hex(d.get("fill")) if d.get("fill") else None

            path_ir = DrawingPathIR(
                stroke_color=stroke,
                fill_color=fill,
                stroke_width=float(d.get("width", 1.0)),
                closed=bool(d.get("closePath", False)),
            )

            drawing_irs.append(VectorDrawingIR(
                paths=[path_ir],
                bbox=d_bbox,
            ))

        return drawing_irs

    def _extract_text_blocks(
        self,
        page: fitz.Page,
        needs_ocr: bool,
        table_bboxes: List[Tuple[float, float, float, float]],
    ) -> List[ParagraphIR]:
        paragraphs: List[ParagraphIR] = []

        text_dict = page.get_text("dict")
        blocks = text_dict.get("blocks", [])

        total_font_size = 0.0
        font_size_count = 0

        for block in blocks:
            if block.get("type") != 0:
                continue
            b_box = tuple(float(x) for x in block.get("bbox", (0, 0, 0, 0)))

            # If inside a table, skip because table extractor handles it
            if any(_bbox_inside(b_box, t_box) for t_box in table_bboxes):
                continue

            for line in block.get("lines", []):
                spans: List[TextSpanIR] = []
                line_box = tuple(float(x) for x in line.get("bbox", (0, 0, 0, 0)))

                for s in line.get("spans", []):
                    text = s.get("text", "")
                    if not text:
                        continue

                    f_size = float(s.get("size", 11.0))
                    total_font_size += f_size
                    font_size_count += 1

                    resolved = resolve_font(s.get("font", ""), s.get("flags", 0))
                    color = _color_to_hex(s.get("color", 0))

                    spans.append(TextSpanIR(
                        text=text,
                        font_family=resolved.family,
                        font_size=f_size,
                        bold=resolved.bold,
                        italic=resolved.italic,
                        color_hex=color,
                        bbox=tuple(float(x) for x in s.get("bbox", (0, 0, 0, 0))),
                        origin=tuple(float(x) for x in s.get("origin", (0, 0))),
                    ))

                if spans:
                    plain = "".join(sp.text for sp in spans).strip()
                    if plain:
                        p_ir = ParagraphIR(
                            spans=spans,
                            bbox=line_box,
                            alignment=self._determine_alignment(line_box, page.rect.width),
                        )
                        paragraphs.append(p_ir)

        # If native text was sparse and OCR is needed, extract via OCR
        if (len(paragraphs) == 0 or needs_ocr) and ocr_available():
            try:
                for line in ocr_lines(page):
                    spans: List[TextSpanIR] = []
                    x0 = min((w.x0 for w in line), default=0.0)
                    y0 = min((w.y0 for w in line), default=0.0)
                    x1 = max((w.x1 for w in line), default=0.0)
                    y1 = max((w.y1 for w in line), default=0.0)

                    for w in line:
                        if not w.text.strip():
                            continue
                        spans.append(TextSpanIR(
                            text=w.text + " ",
                            font_family="Calibri",
                            font_size=max(8.0, float(w.y1 - w.y0) * 0.75),
                            bbox=(float(w.x0), float(w.y0), float(w.x1), float(w.y1)),
                        ))
                    if spans:
                        paragraphs.append(ParagraphIR(
                            spans=spans,
                            bbox=(float(x0), float(y0), float(x1), float(y1)),
                            alignment=Alignment.LEFT,
                        ))
            except Exception:
                pass

        # Calculate average font size to determine headings
        avg_font_size = (total_font_size / max(1, font_size_count)) if font_size_count > 0 else 11.0
        for p in paragraphs:
            if not p.spans:
                continue
            max_p_size = max(s.font_size for s in p.spans)
            is_bold = any(s.bold for s in p.spans)
            plain = p.plain_text.strip()

            if max_p_size >= avg_font_size * 1.5:
                p.is_heading = True
                p.heading_level = 1
                p.space_before = 12.0
                p.space_after = 6.0
            elif max_p_size >= avg_font_size * 1.25 or (max_p_size > avg_font_size and is_bold and len(plain) < 80):
                p.is_heading = True
                p.heading_level = 2
                p.space_before = 8.0
                p.space_after = 4.0
            elif plain.startswith(("•", "-", "–", "—", "*")):
                p.is_list_item = True
                p.list_level = 1

        return paragraphs

    @staticmethod
    def _determine_alignment(bbox: Tuple[float, float, float, float], page_width: float) -> Alignment:
        line_w = bbox[2] - bbox[0]
        left_gap = bbox[0]
        right_gap = page_width - bbox[2]

        if abs(left_gap - right_gap) < 20.0 and line_w < page_width * 0.75:
            return Alignment.CENTER
        if right_gap < left_gap and right_gap < 50.0 and line_w < page_width * 0.6:
            return Alignment.RIGHT
        return Alignment.LEFT


def extract_pdf_ir(pdf_path: Path) -> DocumentIR:
    extractor = PdfStructuredExtractor(pdf_path)
    return extractor.extract()

