from __future__ import annotations

import math
from typing import Tuple

import cv2
import numpy as np


def detect_curvature(gray_image: np.ndarray) -> Tuple[bool, float]:
    """Detects if page has noticeable vertical or horizontal curvature.
    
    Returns (has_curvature, curvature_amplitude).
    """
    h, w = gray_image.shape
    if h < 100 or w < 100:
        return False, 0.0

    # Downsample
    small = cv2.resize(gray_image, (300, int(300 * h / w)), interpolation=cv2.INTER_AREA)
    sh, sw = small.shape

    # Morphological gradient to isolate text line baselines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
    grad = cv2.morphologyEx(small, cv2.MORPH_GRADIENT, kernel)
    _, thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # Check horizontal projections across vertical strips
    strip_w = max(10, sw // 10)
    centers: list[float] = []
    for i in range(10):
        strip = thresh[:, i * strip_w : (i + 1) * strip_w]
        row_sums = np.sum(strip, axis=1)
        if np.max(row_sums) > 0:
            centers.append(float(np.argmax(row_sums)))

    if len(centers) >= 8:
        # Measure deviation from linear fit
        x = np.arange(len(centers))
        poly = np.polyfit(x, centers, 2)
        curve_factor = abs(poly[0])  # quadratic curvature coefficient
        if curve_factor > 0.15:
            return True, float(curve_factor)

    return False, 0.0


def unwarp_cylindrical_page(
    image: np.ndarray,
    strength: float = 0.5,
    spine_left: bool = True,
) -> np.ndarray:
    """Applies a cylindrical unwarping remap to flatten curved book pages.
    
    Uses an inverse displacement mesh with bicubic interpolation.
    """
    h, w = image.shape[:2]
    if strength <= 0.01:
        return image

    # Build coordinate grids
    x_indices = np.arange(w, dtype=np.float32)
    y_indices = np.arange(h, dtype=np.float32)
    grid_x, grid_y = np.meshgrid(x_indices, y_indices)

    # Normalized x from 0.0 to 1.0
    norm_x = grid_x / float(w)

    # Model cylindrical compression towards spine
    # If spine is on the left, compression is highest near x=0
    # Displacement map stretches compressed pixels outward
    if spine_left:
        # Arc mapping: theta = arcsin(x)
        # Displacement factor reduces as we move away from spine
        curve_profile = np.sin((1.0 - norm_x) * (math.pi / 2.0))
        displacement_x = strength * 25.0 * (curve_profile ** 2) * (1.0 - norm_x)
        # Vertical bow correction
        displacement_y = strength * 15.0 * np.sin(norm_x * math.pi) * ((grid_y - (h / 2.0)) / (h / 2.0))
        map_x = np.clip(grid_x - displacement_x, 0, w - 1).astype(np.float32)
        map_y = np.clip(grid_y + displacement_y, 0, h - 1).astype(np.float32)
    else:
        # Spine on the right
        curve_profile = np.sin(norm_x * (math.pi / 2.0))
        displacement_x = strength * 25.0 * (curve_profile ** 2) * norm_x
        displacement_y = strength * 15.0 * np.sin(norm_x * math.pi) * ((grid_y - (h / 2.0)) / (h / 2.0))
        map_x = np.clip(grid_x + displacement_x, 0, w - 1).astype(np.float32)
        map_y = np.clip(grid_y + displacement_y, 0, h - 1).astype(np.float32)

    unwarped = cv2.remap(
        image,
        map_x,
        map_y,
        interpolation=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return unwarped


def dewarp_page_image(
    image: np.ndarray,
    force_dewarp: bool = False,
    strength: float = 0.5,
) -> Tuple[np.ndarray, bool]:
    """Inspects and dewarps a page image if curved.
    
    Returns (dewarped_image, was_dewarped).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    has_curve, _ = detect_curvature(gray)

    if has_curve or force_dewarp:
        dewarped = unwarp_cylindrical_page(image, strength=strength, spine_left=True)
        return dewarped, True

    return image, False

