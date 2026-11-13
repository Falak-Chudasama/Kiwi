from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import cv2
import numpy as np


@dataclass
class QualityAssessment:
    overall_score: float  # 0.0 to 1.0
    sharpness_score: float  # 0.0 to 1.0
    exposure_score: float  # 0.0 to 1.0
    glare_score: float  # 0.0 to 1.0 (1.0 = no glare)
    uniformity_score: float  # 0.0 to 1.0 (1.0 = very even lighting)
    is_sharp: bool
    is_well_exposed: bool
    has_glare: bool
    has_uneven_light: bool
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(float(self.overall_score), 3),
            "sharpness_score": round(float(self.sharpness_score), 3),
            "exposure_score": round(float(self.exposure_score), 3),
            "glare_score": round(float(self.glare_score), 3),
            "uniformity_score": round(float(self.uniformity_score), 3),
            "is_sharp": bool(self.is_sharp),
            "is_well_exposed": bool(self.is_well_exposed),
            "has_glare": bool(self.has_glare),
            "has_uneven_light": bool(self.has_uneven_light),
            "suggestions": list(self.suggestions),
        }


def assess_image_quality(image_bgr: np.ndarray) -> QualityAssessment:
    """Evaluates image capture quality: blur, exposure, glare, and illumination uniformity."""
    suggestions: List[str] = []

    # Downscale for fast, bounded analysis
    h, w = image_bgr.shape[:2]
    max_dim = 1000
    scale = 1.0
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        small_bgr = cv2.resize(image_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    else:
        small_bgr = image_bgr

    gray = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2GRAY)

    # 1. Sharpness / Blur Assessment (Laplacian variance)
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    # Typically: < 80 is very blurry, 80-250 is moderate, > 300 is crisp
    sharpness_score = min(1.0, max(0.0, lap_var / 350.0))
    is_sharp = lap_var >= 100.0
    if not is_sharp:
        suggestions.append("Image is blurry. Please hold camera steady or focus before capturing.")

    # 2. Exposure Assessment (Luminance histogram)
    mean_lum = float(np.mean(gray))
    # Underexposed if mean < 60, overexposed if mean > 215
    if mean_lum < 65:
        exposure_score = max(0.0, mean_lum / 65.0)
        is_well_exposed = False
        suggestions.append("Document is dark / underexposed. Try adding light.")
    elif mean_lum > 220:
        exposure_score = max(0.0, (255.0 - mean_lum) / 35.0)
        is_well_exposed = False
        suggestions.append("Document is washed out / overexposed.")
    else:
        # Ideal range 100 - 180
        exposure_score = 1.0 - (abs(mean_lum - 140.0) / 140.0) * 0.4
        is_well_exposed = True

    # 3. Glare Detection (Clipped specular highlights)
    # Check pixels with intensity >= 252
    clipped_ratio = float(np.sum(gray >= 252)) / float(gray.size)
    # If more than 3.5% of pixels are pure saturated white (and not an all-white synthetic page)
    has_glare = (clipped_ratio > 0.04) and (mean_lum < 240)
    glare_score = max(0.0, 1.0 - (clipped_ratio * 15.0))
    if has_glare:
        suggestions.append("Specular glare detected. Adjust lighting angle to avoid reflections.")

    # 4. Illumination Uniformity (Quadrant luminance comparison)
    sh, sw = gray.shape
    q1 = np.mean(gray[: sh // 2, : sw // 2])
    q2 = np.mean(gray[: sh // 2, sw // 2 :])
    q3 = np.mean(gray[sh // 2 :, : sw // 2])
    q4 = np.mean(gray[sh // 2 :, sw // 2 :])
    quad_vals = [q1, q2, q3, q4]
    quad_range = max(quad_vals) - min(quad_vals)
    has_uneven_light = quad_range > 60.0
    uniformity_score = max(0.0, 1.0 - (quad_range / 100.0))
    if has_uneven_light:
        suggestions.append("Uneven lighting or strong shadow across the page.")

    # Combined overall score
    overall_score = (
        sharpness_score * 0.40
        + exposure_score * 0.30
        + glare_score * 0.15
        + uniformity_score * 0.15
    )

    if not suggestions:
        suggestions.append("Excellent capture quality.")

    return QualityAssessment(
        overall_score=overall_score,
        sharpness_score=sharpness_score,
        exposure_score=exposure_score,
        glare_score=glare_score,
        uniformity_score=uniformity_score,
        is_sharp=is_sharp,
        is_well_exposed=is_well_exposed,
        has_glare=has_glare,
        has_uneven_light=has_uneven_light,
        suggestions=suggestions,
    )
