from __future__ import annotations

import math
from typing import List, Tuple

import cv2
import numpy as np


def order_quad_points(pts: np.ndarray | List[List[float]]) -> np.ndarray:
    """Orders 4 points as: [top-left, top-right, bottom-right, bottom-left]."""
    pts_arr = np.array(pts, dtype=np.float32).reshape((4, 2))
    rect = np.zeros((4, 2), dtype=np.float32)

    # Top-left has smallest sum (x + y), bottom-right has largest sum
    s = pts_arr.sum(axis=1)
    rect[0] = pts_arr[np.argmin(s)]
    rect[2] = pts_arr[np.argmax(s)]

    # Top-right has smallest difference (y - x), bottom-left has largest difference
    diff = np.diff(pts_arr, axis=1)
    rect[1] = pts_arr[np.argmin(diff)]
    rect[3] = pts_arr[np.argmax(diff)]

    return rect


def calculate_target_dimensions(ordered_pts: np.ndarray) -> Tuple[int, int]:
    """Calculates optimal output width and height for a quad crop."""
    (tl, tr, br, bl) = ordered_pts

    # Width: max of bottom width and top width
    width_a = math.hypot(br[0] - bl[0], br[1] - bl[1])
    width_b = math.hypot(tr[0] - tl[0], tr[1] - tl[1])
    max_w = max(int(width_a), int(width_b))

    # Height: max of right height and left height
    height_a = math.hypot(tr[0] - br[0], tr[1] - br[1])
    height_b = math.hypot(tl[0] - bl[0], tl[1] - bl[1])
    max_h = max(int(height_a), int(height_b))

    # Guard minimum dimensions
    max_w = max(50, max_w)
    max_h = max(50, max_h)

    return max_w, max_h


def warp_perspective_crop(
    image: np.ndarray,
    quad_pts: np.ndarray | List[List[float]],
    target_dim: Tuple[int, int] | None = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Warps a 4-point quadrilateral into an upright rectified rectangle.
    
    Returns (warped_image, homography_matrix).
    """
    ordered = order_quad_points(quad_pts)

    if target_dim is not None:
        max_w, max_h = target_dim
    else:
        max_w, max_h = calculate_target_dimensions(ordered)

    dst = np.array(
        [
            [0, 0],
            [max_w - 1, 0],
            [max_w - 1, max_h - 1],
            [0, max_h - 1],
        ],
        dtype=np.float32,
    )

    matrix = cv2.getPerspectiveTransform(ordered, dst)
    warped = cv2.warpPerspective(
        image,
        matrix,
        (max_w, max_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return warped, matrix


def transform_points(points: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Transforms 2D points using a 3x3 homography matrix."""
    pts_reshaped = points.reshape(-1, 1, 2).astype(np.float32)
    transformed = cv2.perspectiveTransform(pts_reshaped, matrix)
    return transformed.reshape(-1, 2)

