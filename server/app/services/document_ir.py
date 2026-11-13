from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Tuple


class BlockType(str, Enum):
    PARAGRAPH = "paragraph"
    TABLE = "table"
    IMAGE = "image"
    DRAWING = "drawing"
    HEADER = "header"
    FOOTER = "footer"


class Alignment(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


@dataclass
class TextSpanIR:
    text: str
    font_family: str = "Calibri"
    font_size: float = 11.0
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color_hex: str = "#000000"
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # x0, y0, x1, y1
    origin: Tuple[float, float] = (0.0, 0.0)


@dataclass
class ParagraphIR:
    spans: List[TextSpanIR] = field(default_factory=list)
    alignment: Alignment = Alignment.LEFT
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    line_spacing: float = 1.15
    space_before: float = 0.0
    space_after: float = 4.0
    is_heading: bool = False
    heading_level: int = 0
    is_list_item: bool = False
    list_level: int = 0

    @property
    def plain_text(self) -> str:
        return "".join(s.text for s in self.spans)


@dataclass
class TableCellIR:
    row_idx: int
    col_idx: int
    row_span: int = 1
    col_span: int = 1
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    background_color: Optional[str] = None  # hex, e.g. "#F0F0F0"
    paragraphs: List[ParagraphIR] = field(default_factory=list)
    border_top: bool = True
    border_bottom: bool = True
    border_left: bool = True
    border_right: bool = True


@dataclass
class TableRowIR:
    cells: List[TableCellIR] = field(default_factory=list)
    height: float = 20.0
    is_header: bool = False


@dataclass
class TableIR:
    rows: List[TableRowIR] = field(default_factory=list)
    col_widths: List[float] = field(default_factory=list)  # in points
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    has_borders: bool = True


@dataclass
class ImageIR:
    image_bytes: bytes
    ext: str = "png"
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    width: float = 100.0
    height: float = 100.0
    is_inline: bool = True
    xref: Optional[int] = None
    caption: Optional[str] = None


@dataclass
class DrawingPathIR:
    points: List[Tuple[float, float]] = field(default_factory=list)
    stroke_color: Optional[str] = None
    fill_color: Optional[str] = None
    stroke_width: float = 1.0
    closed: bool = False


@dataclass
class VectorDrawingIR:
    paths: List[DrawingPathIR] = field(default_factory=list)
    bbox: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)


@dataclass
class BlockIR:
    block_type: BlockType
    bbox: Tuple[float, float, float, float]
    paragraph: Optional[ParagraphIR] = None
    table: Optional[TableIR] = None
    image: Optional[ImageIR] = None
    drawing: Optional[VectorDrawingIR] = None


@dataclass
class PageIR:
    page_number: int
    width: float  # points (1/72 in)
    height: float
    orientation: str = "portrait"  # "portrait" or "landscape"
    margin_top: float = 72.0
    margin_bottom: float = 72.0
    margin_left: float = 72.0
    margin_right: float = 72.0
    blocks: List[BlockIR] = field(default_factory=list)
    header: Optional[List[ParagraphIR]] = None
    footer: Optional[List[ParagraphIR]] = None

    @property
    def plain_text(self) -> str:
        texts = []
        for b in self.blocks:
            if b.paragraph:
                texts.append(b.paragraph.plain_text)
            elif b.table:
                for r in b.table.rows:
                    row_txt = "\t".join(
                        "".join(p.plain_text for p in c.paragraphs) for c in r.cells
                    )
                    texts.append(row_txt)
        return "\n".join(texts)


@dataclass
class DocumentIR:
    title: Optional[str] = None
    author: Optional[str] = None
    creator: Optional[str] = None
    pages: List[PageIR] = field(default_factory=list)

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def full_plain_text(self) -> str:
        return "\n\n".join(p.plain_text for p in self.pages)

