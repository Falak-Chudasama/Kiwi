from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

import cv2
import numpy as np


class OutputFilterMode(str, Enum):
    COLOR = "color"
    GRAYSCALE = "grayscale"
    BW = "bw"
    PHOTO = "photo"


@dataclass
class EnhancementConfig:
    filter_mode: OutputFilterMode = OutputFilterMode.COLOR
    brightness: float = 0.0  # -100 to +100
    contrast: float = 0.0  # -100 to +100
    exposure: float = 0.0  # -2.0 to +2.0 EV
    shadows: float = 0.0  # 0 to 100 (shadow lift)
    highlights: float = 0.0  # -100 to 100
    whites: float = 0.0  # 0 to 100 (paper whitening)
    blacks: float = 0.0  # 0 to 100 (deepen dark text)
    gamma: float = 1.0  # 0.5 to 2.5
    sharpen: float = 0.3  # 0.0 to 1.0
    denoise: float = 0.2  # 0.0 to 1.0
    remove_shadows: bool = True
    preserve_color_stamps: bool = True


def _remove_page_shadows(bgr: np.ndarray) -> np.ndarray:
    """Removes non-uniform illumination and dark shadows using background division."""
    # Split channels to process luminance
    rgb_planes = cv2.split(bgr)
    result_planes = []

    for plane in rgb_planes:
        # Morphological dilation with a large kernel estimates local background illumination
        dilated = cv2.dilate(plane, np.ones((7, 7), np.uint8))
        bg_img = cv2.medianBlur(dilated, 21)
        # Background division: (plane / bg_img) * 255
        diff = 255 - cv2.absdiff(plane, bg_img)
        norm_plane = cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        result_planes.append(norm_plane)

    return cv2.merge(result_planes)


def _detect_colored_ink_mask(bgr: np.ndarray) -> np.ndarray:
    """Identifies pixels with noticeable color saturation (stamps, signatures, colored annotations)."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    # Pixels that have color (saturation > 40) and are not extremely dark (< 30) or washed out
    colored_mask = (saturation > 42) & (value > 40) & (value < 240)
    return colored_mask.astype(np.uint8) * 255


def _apply_gamma(img: np.ndarray, gamma: float) -> np.ndarray:
    if abs(gamma - 1.0) < 0.01:
        return img
    inv_gamma = 1.0 / max(0.1, gamma)
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(img, table)


def _sharpen_text(img: np.ndarray, amount: float) -> np.ndarray:
    if amount <= 0.05:
        return img
    # Unsharp mask
    blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=2.0)
    alpha = 1.0 + amount
    beta = -amount
    sharpened = cv2.addWeighted(img, alpha, blurred, beta, 0)
    return sharpened


def enhance_scanned_image(
    image_bgr: np.ndarray,
    config: EnhancementConfig | None = None,
) -> np.ndarray:
    """Applies high-fidelity non-destructive document enhancement."""
    if config is None:
        config = EnhancementConfig()

    work = image_bgr.copy()

    # If photo mode, preserve natural tones with minimal touching
    if config.filter_mode == OutputFilterMode.PHOTO:
        if config.brightness != 0 or config.contrast != 0:
            alpha = max(0.1, 1.0 + (config.contrast / 100.0))
            beta = config.brightness * 1.5
            work = cv2.convertScaleAbs(work, alpha=alpha, beta=beta)
        if config.gamma != 1.0:
            work = _apply_gamma(work, config.gamma)
        if config.sharpen > 0.1:
            work = _sharpen_text(work, config.sharpen * 0.5)
        return work

    # 1. Shadow removal and illumination normalization
    color_ink_mask = None
    if config.preserve_color_stamps and config.filter_mode in (OutputFilterMode.COLOR, OutputFilterMode.BW):
        color_ink_mask = _detect_colored_ink_mask(work)

    if config.remove_shadows:
        work = _remove_page_shadows(work)

    # 2. Denoising
    if config.denoise > 0.05:
        h_param = max(2, int(config.denoise * 7))
        work = cv2.fastNlMeansDenoisingColored(work, None, h_param, h_param, 7, 21)

    # 3. Paper Whitening (Whites slider) & Black Deepening (Blacks slider)
    if config.whites > 0 or config.blacks > 0 or config.contrast != 0 or config.brightness != 0:
        # Scale range [in_black, in_white] -> [0, 255]
        in_black = int(min(60, config.blacks * 0.6))
        in_white = int(max(180, 255 - (config.whites * 0.85)))
        if in_white > in_black:
            lut = np.zeros(256, dtype=np.uint8)
            for i in range(256):
                val = (i - in_black) * 255.0 / (in_white - in_black)
                lut[i] = int(np.clip(val, 0, 255))
            work = cv2.LUT(work, lut)

        if config.brightness != 0 or config.contrast != 0:
            alpha = max(0.2, 1.0 + (config.contrast / 100.0))
            beta = config.brightness * 1.2
            work = cv2.convertScaleAbs(work, alpha=alpha, beta=beta)

    # 4. Gamma
    if config.gamma != 1.0:
        work = _apply_gamma(work, config.gamma)

    # 5. Text sharpening
    if config.sharpen > 0.05:
        work = _sharpen_text(work, config.sharpen)

    # 6. Apply Selected Output Filter Mode
    if config.filter_mode == OutputFilterMode.GRAYSCALE:
        gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    elif config.filter_mode == OutputFilterMode.BW:
        gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        # Adaptive Gaussian thresholding for crisp text
        bw = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 11
        )
        bw_bgr = cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)

        # Re-composite colored ink stamps if enabled
        if config.preserve_color_stamps and color_ink_mask is not None and np.any(color_ink_mask):
            mask_3c = cv2.cvtColor(color_ink_mask, cv2.COLOR_GRAY2BGR)
            np.copyto(bw_bgr, work, where=(mask_3c > 0))

        return bw_bgr

    # Default COLOR mode: crisp text, white paper, vivid ink
    if config.preserve_color_stamps and color_ink_mask is not None and np.any(color_ink_mask):
        # Slightly boost saturation on ink areas
        hsv = cv2.cvtColor(work, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1].astype(np.int16) + 15, 0, 255).astype(np.uint8)
        boosted = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        mask_3c = cv2.cvtColor(color_ink_mask, cv2.COLOR_GRAY2BGR)
        np.copyto(work, boosted, where=(mask_3c > 0))

    return work

