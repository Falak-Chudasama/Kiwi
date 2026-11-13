from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np

from app.services.scanner.geometry import order_quad_points


@dataclass
class DocumentBounds:
    corners: List[List[float]]  # 4 points: [TL, TR, BR, BL] as [x, y]
    confidence: float  # 0.0 to 1.0
    detected_auto: bool  # True if found via computer vision, False if fallback
    aspect_ratio: float
    document_type_hint: str  # "document", "card", "receipt", "photo"


def _quad_angle(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
    """Calculates angle in degrees at p2 between p1-p2 and p3-p2."""
    v1 = p1 - p2
    v2 = p3 - p2
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    cosine = np.dot(v1, v2) / (norm1 * norm2)
    cosine = np.clip(cosine, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def detect_document_bounds(image_bgr: np.ndarray) -> DocumentBounds:
    """Detects the 4 corners of a document on a background using OpenCV."""
    h, w = image_bgr.shape[:2]
    total_area = float(w * h)

    # Downscale for fast, robust contour analysis
    max_dim = 1200
    scale = 1.0
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        work_img = cv2.resize(image_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    else:
        work_img = image_bgr

    wh, ww = work_img.shape[:2]

    # Preprocessing
    gray = cv2.cvtColor(work_img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Try multi-scale Canny edge detection
    best_quad: Optional[np.ndarray] = None
    best_score = 0.0

    for low_th, high_th in [(30, 100), (50, 150), (75, 200)]:
        edges = cv2.Canny(blurred, low_th, high_th)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Must occupy at least 8% of work image area
            if area < (ww * wh * 0.08):
                continue

            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

            # If 4 points and convex
            if len(approx) == 4 and cv2.isContourConvex(approx):
                quad_pts = approx.reshape(4, 2).astype(np.float32)
                ordered = order_quad_points(quad_pts)

                # Check corner angles: document corners should be roughly 70-110 deg
                angles = [
                    _quad_angle(ordered[3], ordered[0], ordered[1]),
                    _quad_angle(ordered[0], ordered[1], ordered[2]),
                    _quad_angle(ordered[1], ordered[2], ordered[3]),
                    _quad_angle(ordered[2], ordered[3], ordered[0]),
                ]
                angle_deviation = sum(abs(a - 90.0) for a in angles) / 4.0

                if angle_deviation < 35.0:
                    area_ratio = area / float(ww * wh)
                    score = area_ratio * (1.0 - (angle_deviation / 45.0))
                    if score > best_score:
                        best_score = score
                        best_quad = ordered
                        break

        if best_quad is not None and best_score > 0.4:
            break

    # If detection found a strong quad, scale points back to full image coordinate space
    if best_quad is not None:
        scaled_corners = (best_quad / scale).tolist()
        ordered_full = order_quad_points(scaled_corners)

        top_w = math.hypot(ordered_full[1][0] - ordered_full[0][0], ordered_full[1][1] - ordered_full[0][1])
        left_h = math.hypot(ordered_full[3][0] - ordered_full[0][0], ordered_full[3][1] - ordered_full[0][1])
        aspect = (left_h / max(1.0, top_w)) if top_w > 0 else 1.414

        # Guess document type
        if aspect > 2.2:
            hint = "receipt"
        elif 1.45 <= (top_w / max(1.0, left_h)) <= 1.70:
            hint = "card"
        elif 1.15 <= aspect <= 1.6:
            hint = "document"
        else:
            hint = "document"

        confidence = min(0.98, max(0.65, float(best_score + 0.3)))
        return DocumentBounds(
            corners=[[round(float(pt[0]), 1), round(float(pt[1]), 1)] for pt in ordered_full],
            confidence=confidence,
            detected_auto=True,
            aspect_ratio=round(aspect, 3),
            document_type_hint=hint,
        )

    # Fallback: Safe 2% inset box around full image
    inset_x = w * 0.02
    inset_y = h * 0.02
    fallback_corners = [
        [inset_x, inset_y],
        [w - inset_x, inset_y],
        [w - inset_x, h - inset_y],
        [inset_x, h - inset_y],
    ]
    aspect = (h / max(1.0, w))

    return DocumentBounds(
        corners=[[round(float(pt[0]), 1), round(float(pt[1]), 1)] for pt in fallback_corners],
        confidence=0.40,
        detected_auto=False,
        aspect_ratio=round(aspect, 3),
        document_type_hint="document",
    )

