"""HSV color ranges and ball classification for standard pool balls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

# Default felt HSV range (green table)
DEFAULT_FELT_LOWER = np.array([35, 40, 40])
DEFAULT_FELT_UPPER = np.array([85, 255, 255])

# White stripe detection (for ball 9 vs ball 1)
WHITE_LOWER = np.array([0, 0, 180])
WHITE_UPPER = np.array([180, 60, 255])

STRIPE_WHITE_RATIO_THRESHOLD = 0.12
CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.45


@dataclass
class ColorRange:
    """HSV bounds for a ball color group."""

    lower: np.ndarray
    upper: np.ndarray
    ball_numbers: tuple[int, ...]
    label: str


# Standard APA/BCA ball colors in HSV
BALL_COLOR_RANGES: list[ColorRange] = [
    ColorRange(
        lower=np.array([18, 80, 80]),
        upper=np.array([35, 255, 255]),
        ball_numbers=(1, 9),
        label="yellow",
    ),
    ColorRange(
        lower=np.array([100, 80, 80]),
        upper=np.array([130, 255, 255]),
        ball_numbers=(2,),
        label="blue",
    ),
    ColorRange(
        lower=np.array([0, 120, 80]),
        upper=np.array([10, 255, 255]),
        ball_numbers=(3,),
        label="red",
    ),
    ColorRange(
        lower=np.array([125, 50, 50]),
        upper=np.array([155, 255, 255]),
        ball_numbers=(4,),
        label="purple",
    ),
    ColorRange(
        lower=np.array([10, 120, 120]),
        upper=np.array([18, 255, 255]),
        ball_numbers=(5,),
        label="orange",
    ),
    ColorRange(
        lower=np.array([40, 80, 80]),
        upper=np.array([75, 255, 255]),
        ball_numbers=(6,),
        label="green",
    ),
    ColorRange(
        lower=np.array([0, 80, 30]),
        upper=np.array([10, 255, 120]),
        ball_numbers=(7,),
        label="maroon",
    ),
    ColorRange(
        lower=np.array([0, 0, 0]),
        upper=np.array([180, 80, 60]),
        ball_numbers=(8,),
        label="black",
    ),
]


@dataclass
class ClassificationResult:
    ball_number: Optional[int]
    confidence: float
    label: str


def create_felt_mask(hsv: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    """Return binary mask of table felt."""
    return cv2.inRange(hsv, lower, upper)


def _sample_ball_region(
    frame_bgr: np.ndarray,
    hsv: np.ndarray,
    cx: int,
    cy: int,
    radius: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Extract center region of a ball, avoiding edge bleed from felt."""
    sample_r = max(2, int(radius * 0.5))
    h, w = frame_bgr.shape[:2]
    x1 = max(0, cx - sample_r)
    y1 = max(0, cy - sample_r)
    x2 = min(w, cx + sample_r)
    y2 = min(h, cy + sample_r)
    return hsv[y1:y2, x1:x2], frame_bgr[y1:y2, x1:x2]


def _white_band_ratio(bgr_patch: np.ndarray) -> float:
    """Ratio of white pixels in a horizontal band through the ball center."""
    if bgr_patch.size == 0:
        return 0.0
    hsv_patch = cv2.cvtColor(bgr_patch, cv2.COLOR_BGR2HSV)
    white_mask = cv2.inRange(hsv_patch, WHITE_LOWER, WHITE_UPPER)
    mid = white_mask.shape[0] // 2
    band_height = max(1, white_mask.shape[0] // 4)
    y1 = max(0, mid - band_height // 2)
    y2 = min(white_mask.shape[0], mid + band_height // 2)
    band = white_mask[y1:y2, :]
    if band.size == 0:
        return 0.0
    return float(np.count_nonzero(band)) / band.size


def _color_match_score(hsv_patch: np.ndarray, color_range: ColorRange) -> float:
    """Fraction of pixels matching a color range."""
    if hsv_patch.size == 0:
        return 0.0
    mask = cv2.inRange(hsv_patch, color_range.lower, color_range.upper)
    return float(np.count_nonzero(mask)) / mask.size


def classify_ball(
    frame_bgr: np.ndarray,
    hsv: np.ndarray,
    cx: int,
    cy: int,
    radius: int,
) -> ClassificationResult:
    """Classify a detected ball by dominant HSV color in its center."""
    hsv_patch, bgr_patch = _sample_ball_region(frame_bgr, hsv, cx, cy, radius)
    if hsv_patch.size == 0:
        return ClassificationResult(None, 0.0, "Unknown")

    best_range: Optional[ColorRange] = None
    best_score = 0.0
    for color_range in BALL_COLOR_RANGES:
        score = _color_match_score(hsv_patch, color_range)
        if score > best_score:
            best_score = score
            best_range = color_range

    if best_range is None or best_score < CLASSIFICATION_CONFIDENCE_THRESHOLD:
        return ClassificationResult(None, best_score, "Unknown")

    ball_number: Optional[int] = None
    if len(best_range.ball_numbers) == 1:
        ball_number = best_range.ball_numbers[0]
    elif best_range.label == "yellow":
        white_ratio = _white_band_ratio(bgr_patch)
        ball_number = 9 if white_ratio >= STRIPE_WHITE_RATIO_THRESHOLD else 1

    label = str(ball_number) if ball_number is not None else "Unknown"
    return ClassificationResult(ball_number, best_score, label)


def run_calibration(frame_bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Interactive HSV calibration for felt color.
    Adjust sliders, press 's' to save and exit, 'q' to cancel.
    Returns (felt_lower, felt_upper) HSV arrays.
    """
    window = "Felt Calibration"
    cv2.namedWindow(window)

    def nothing(_: int) -> None:
        pass

    cv2.createTrackbar("H Low", window, 35, 179, nothing)
    cv2.createTrackbar("S Low", window, 40, 255, nothing)
    cv2.createTrackbar("V Low", window, 40, 255, nothing)
    cv2.createTrackbar("H High", window, 85, 179, nothing)
    cv2.createTrackbar("S High", window, 255, 255, nothing)
    cv2.createTrackbar("V High", window, 255, 255, nothing)

    felt_lower = DEFAULT_FELT_LOWER.copy()
    felt_upper = DEFAULT_FELT_UPPER.copy()

    while True:
        h_low = cv2.getTrackbarPos("H Low", window)
        s_low = cv2.getTrackbarPos("S Low", window)
        v_low = cv2.getTrackbarPos("V Low", window)
        h_high = cv2.getTrackbarPos("H High", window)
        s_high = cv2.getTrackbarPos("S High", window)
        v_high = cv2.getTrackbarPos("V High", window)

        felt_lower = np.array([h_low, s_low, v_low])
        felt_upper = np.array([h_high, s_high, v_high])

        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        mask = create_felt_mask(hsv, felt_lower, felt_upper)
        preview = cv2.bitwise_and(frame_bgr, frame_bgr, mask=mask)
        cv2.imshow(window, preview)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("s"):
            break
        if key == ord("q"):
            felt_lower = DEFAULT_FELT_LOWER.copy()
            felt_upper = DEFAULT_FELT_UPPER.copy()
            break

    cv2.destroyWindow(window)
    return felt_lower, felt_upper
