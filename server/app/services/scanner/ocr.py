from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import cv2
import numpy as np
from PIL import Image
import pytesseract

from app.services.pdf_ocr import ocr_available


@dataclass
class OcrWord:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    confidence: float  # 0.0 to 100.0
    line_num: int
    word_num: int


@dataclass
class OcrResult:
    full_text: str
    words: List[OcrWord]
    mean_confidence: float
    language: str


def run_scanner_ocr(
    image_bgr: np.ndarray,
    language: str = "eng",
) -> OcrResult:
    """Performs optical character recognition on an enhanced scanned image.
    
    Coordinates are 1:1 aligned with the input image dimensions.
    """
    if not ocr_available():
        return OcrResult(full_text="", words=[], mean_confidence=0.0, language=language)

    # Convert BGR to RGB for PIL / Tesseract
    rgb_img = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_img)

    try:
        data = pytesseract.image_to_data(
            pil_img,
            lang=language,
            output_type=pytesseract.Output.DICT,
            config="--oem 1 --psm 3",
        )
    except Exception:
        # Fallback to standard config if specific psm fails
        try:
            data = pytesseract.image_to_data(
                pil_img,
                lang=language,
                output_type=pytesseract.Output.DICT,
            )
        except Exception:
            return OcrResult(full_text="", words=[], mean_confidence=0.0, language=language)

    words: List[OcrWord] = []
    text_pieces: List[str] = []
    confidences: List[float] = []

    n_boxes = len(data["text"])
    current_line = -1

    for i in range(n_boxes):
        text = str(data["text"][i]).strip()
        conf = float(data["conf"][i])

        if not text or conf < 0:
            continue

        x = float(data["left"][i])
        y = float(data["top"][i])
        w = float(data["width"][i])
        h = float(data["height"][i])
        line_num = int(data["line_num"][i])
        word_num = int(data["word_num"][i])

        if current_line != line_num and current_line != -1:
            text_pieces.append("\n")
        elif text_pieces and not text_pieces[-1].endswith("\n"):
            text_pieces.append(" ")

        text_pieces.append(text)
        current_line = line_num
        confidences.append(conf)

        words.append(
            OcrWord(
                text=text,
                x0=x,
                y0=y,
                x1=x + w,
                y1=y + h,
                confidence=conf,
                line_num=line_num,
                word_num=word_num,
            )
        )

    full_text = "".join(text_pieces).strip()
    mean_conf = (sum(confidences) / max(1, len(confidences))) if confidences else 0.0

    return OcrResult(
        full_text=full_text,
        words=words,
        mean_confidence=mean_conf,
        language=language,
    )

