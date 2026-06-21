"""Ball detection, tracking, and rack heuristics."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

import cv2
import numpy as np

from ball_colors import (
    CLASSIFICATION_CONFIDENCE_THRESHOLD,
    DEFAULT_FELT_LOWER,
    DEFAULT_FELT_UPPER,
    ClassificationResult,
    classify_ball,
    create_felt_mask,
)

MAX_MISSED_FRAMES = 15
RACK_CLUSTER_MIN_BALLS = 5
RACK_CLUSTER_MAX_DISTANCE_FACTOR = 2.5


@dataclass
class Detection:
    cx: int
    cy: int
    radius: int
    classification: ClassificationResult = field(
        default_factory=lambda: ClassificationResult(None, 0.0, "Unknown")
    )


@dataclass
class Track:
    track_id: int
    cx: int
    cy: int
    radius: int
    ball_number: Optional[int] = None
    label: str = "Unknown"
    confidence: float = 0.0
    missed_frames: int = 0

    def update(
        self,
        detection: Detection,
        persist_label: bool = True,
    ) -> None:
        self.cx = detection.cx
        self.cy = detection.cy
        self.radius = detection.radius
        self.missed_frames = 0

        new_conf = detection.classification.confidence
        new_number = detection.classification.ball_number
        new_label = detection.classification.label

        if new_number is not None and new_conf >= CLASSIFICATION_CONFIDENCE_THRESHOLD:
            if not persist_label or self.ball_number is None or new_conf > self.confidence:
                self.ball_number = new_number
                self.label = new_label
                self.confidence = new_conf
        elif not persist_label or self.ball_number is None:
            self.label = new_label
            self.confidence = new_conf


class BallTracker:
    """Detect pool balls and track them across frames."""

    def __init__(
        self,
        felt_lower: Optional[np.ndarray] = None,
        felt_upper: Optional[np.ndarray] = None,
    ) -> None:
        self.felt_lower = felt_lower if felt_lower is not None else DEFAULT_FELT_LOWER.copy()
        self.felt_upper = felt_upper if felt_upper is not None else DEFAULT_FELT_UPPER.copy()
        self.tracks: list[Track] = []
        self._next_id = 1
        self._frame_width = 0

    def _is_on_table(
        self,
        felt_mask: np.ndarray,
        cx: int,
        cy: int,
        radius: int,
    ) -> bool:
        """Return True when a ball center lies within the felt play area."""
        ys, xs = np.where(felt_mask > 0)
        if len(xs) == 0:
            return True

        margin = radius
        x1, x2 = int(xs.min()), int(xs.max())
        y1, y2 = int(ys.min()), int(ys.max())
        return (
            x1 + margin <= cx <= x2 - margin
            and y1 + margin <= cy <= y2 - margin
        )

    def _radius_bounds(self) -> tuple[int, int]:
        min_r = max(6, int(self._frame_width * 0.015))
        max_r = max(min_r + 2, int(self._frame_width * 0.04))
        return min_r, max_r

    def detect_balls(self, frame_bgr: np.ndarray) -> list[Detection]:
        """Find ball candidates using Hough circles on the felt region."""
        self._frame_width = frame_bgr.shape[1]
        min_radius, max_radius = self._radius_bounds()
        min_dist = max(min_radius * 2, int(min_radius * 1.8))

        hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        felt_mask = create_felt_mask(hsv, self.felt_lower, self.felt_upper)

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (9, 9), 2)

        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=min_dist,
            param1=50,
            param2=28,
            minRadius=min_radius,
            maxRadius=max_radius,
        )

        detections: list[Detection] = []
        if circles is None:
            return detections

        for circle in np.round(circles[0]).astype(int):
            cx, cy, radius = int(circle[0]), int(circle[1]), int(circle[2])
            if not self._is_on_table(felt_mask, cx, cy, radius):
                continue

            classification = classify_ball(frame_bgr, hsv, cx, cy, radius)
            detections.append(
                Detection(cx=cx, cy=cy, radius=radius, classification=classification)
            )

        return self._non_max_suppression(detections)

    def _non_max_suppression(self, detections: list[Detection]) -> list[Detection]:
        """Remove overlapping duplicate detections, keeping higher-confidence ones."""
        if len(detections) <= 1:
            return detections

        detections = sorted(
            detections,
            key=lambda d: d.classification.confidence,
            reverse=True,
        )
        kept: list[Detection] = []
        for det in detections:
            overlap = any(
                np.hypot(det.cx - existing.cx, det.cy - existing.cy)
                < (det.radius + existing.radius) * 0.6
                for existing in kept
            )
            if not overlap:
                kept.append(det)
        return kept

    def _match_distance(self, track: Track, detection: Detection) -> float:
        return float(np.hypot(track.cx - detection.cx, track.cy - detection.cy))

    def _max_match_distance(self, track: Track) -> float:
        return track.radius * 1.5

    def update(self, frame_bgr: np.ndarray) -> list[Track]:
        """Run detection, associate with existing tracks, apply rack heuristics."""
        detections = self.detect_balls(frame_bgr)
        detections = self._apply_rack_heuristics(detections)
        self._associate(detections)
        return [t for t in self.tracks if t.missed_frames == 0]

    def _associate(self, detections: list[Detection]) -> None:
        unmatched_tracks = set(range(len(self.tracks)))
        unmatched_detections = set(range(len(detections)))

        pairs: list[tuple[float, int, int]] = []
        for ti in unmatched_tracks:
            track = self.tracks[ti]
            for di in unmatched_detections:
                detection = detections[di]
                dist = self._match_distance(track, detection)
                if dist <= self._max_match_distance(track):
                    pairs.append((dist, ti, di))

        pairs.sort(key=lambda item: item[0])

        matched_tracks: set[int] = set()
        matched_detections: set[int] = set()
        for _, ti, di in pairs:
            if ti in matched_tracks or di in matched_detections:
                continue
            self.tracks[ti].update(detections[di])
            matched_tracks.add(ti)
            matched_detections.add(di)

        for ti in unmatched_tracks - matched_tracks:
            self.tracks[ti].missed_frames += 1

        for di in unmatched_detections - matched_detections:
            detection = detections[di]
            track = Track(
                track_id=self._next_id,
                cx=detection.cx,
                cy=detection.cy,
                radius=detection.radius,
            )
            track.update(detection, persist_label=False)
            self.tracks.append(track)
            self._next_id += 1

        self.tracks = [t for t in self.tracks if t.missed_frames <= MAX_MISSED_FRAMES]

    def _apply_rack_heuristics(self, detections: list[Detection]) -> list[Detection]:
        """
        When balls form a tight cluster (rack), assign 1 to apex and 9 to center
        for low-confidence classifications.
        """
        if len(detections) < RACK_CLUSTER_MIN_BALLS:
            return detections

        positions = np.array([[d.cx, d.cy] for d in detections])
        centroid = positions.mean(axis=0)
        avg_radius = float(np.mean([d.radius for d in detections]))
        max_dist = avg_radius * RACK_CLUSTER_MAX_DISTANCE_FACTOR

        cluster_indices = [
            i
            for i, det in enumerate(detections)
            if np.hypot(det.cx - centroid[0], det.cy - centroid[1]) <= max_dist * 2
        ]
        if len(cluster_indices) < RACK_CLUSTER_MIN_BALLS:
            return detections

        cluster = [detections[i] for i in cluster_indices]
        apex = min(cluster, key=lambda d: d.cy)
        center = min(
            cluster,
            key=lambda d: np.hypot(d.cx - centroid[0], d.cy - centroid[1]),
        )

        result = list(detections)
        for i, det in enumerate(result):
            if det.classification.confidence >= CLASSIFICATION_CONFIDENCE_THRESHOLD:
                continue
            if det.cx == apex.cx and det.cy == apex.cy:
                result[i] = Detection(
                    det.cx,
                    det.cy,
                    det.radius,
                    ClassificationResult(1, 0.5, "1"),
                )
            elif det.cx == center.cx and det.cy == center.cy:
                result[i] = Detection(
                    det.cx,
                    det.cy,
                    det.radius,
                    ClassificationResult(9, 0.5, "9"),
                )

        return result


def scale_tracks_for_display(tracks: list[Track], scale: float) -> list[Track]:
    """Return track copies with coordinates mapped back to full-resolution frame."""
    if scale == 1.0:
        return tracks

    inv = 1.0 / scale
    return [
        replace(
            track,
            cx=int(track.cx * inv),
            cy=int(track.cy * inv),
            radius=int(track.radius * inv),
        )
        for track in tracks
    ]


def draw_tracks(frame_bgr: np.ndarray, tracks: list[Track]) -> np.ndarray:
    """Draw highlight circles and labels for active tracks."""
    output = frame_bgr.copy()
    for track in tracks:
        color = _label_color(track.ball_number)
        cv2.circle(output, (track.cx, track.cy), track.radius + 2, color, 2)
        cv2.circle(output, (track.cx, track.cy), 2, color, -1)

        if track.ball_number is not None:
            text = str(track.ball_number)
        else:
            text = f"Ball {track.track_id}"

        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = max(0.4, track.radius / 30)
        thickness = max(1, int(scale * 2))
        (text_w, text_h), _ = cv2.getTextSize(text, font, scale, thickness)
        tx = track.cx - text_w // 2
        ty = track.cy - track.radius - 8
        cv2.rectangle(
            output,
            (tx - 2, ty - text_h - 2),
            (tx + text_w + 2, ty + 2),
            (0, 0, 0),
            -1,
        )
        cv2.putText(output, text, (tx, ty), font, scale, color, thickness, cv2.LINE_AA)

    return output


def _label_color(ball_number: Optional[int]) -> tuple[int, int, int]:
    palette = {
        1: (0, 220, 255),
        2: (255, 120, 0),
        3: (0, 0, 255),
        4: (255, 0, 200),
        5: (0, 140, 255),
        6: (0, 200, 0),
        7: (0, 0, 140),
        8: (200, 200, 200),
        9: (0, 255, 255),
    }
    return palette.get(ball_number, (255, 255, 255))
