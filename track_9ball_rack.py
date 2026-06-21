#!/usr/bin/env python3
"""Track and label 9-ball rack balls in top-down pool table video."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

from ball_colors import run_calibration
from ball_tracker import BallTracker, draw_tracks, scale_tracks_for_display


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Track pool balls in a top-down 9-ball rack video using OpenCV."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input video file",
    )
    parser.add_argument(
        "--output",
        help="Path to save annotated output video (MP4)",
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Show live preview window",
    )
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="Run interactive HSV calibration on the first frame",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Resize factor for processing (e.g. 0.5 for faster processing)",
    )
    return parser.parse_args()


def open_video(path: str) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"Error: could not open video '{path}'", file=sys.stderr)
        sys.exit(1)
    return cap


def create_writer(
    output_path: str,
    fps: float,
    frame_size: tuple[int, int],
) -> cv2.VideoWriter:
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, frame_size)
    if not writer.isOpened():
        print(f"Error: could not create output video '{output_path}'", file=sys.stderr)
        sys.exit(1)
    return writer


def resize_frame(frame, scale: float):
    if scale == 1.0:
        return frame
    return cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)


def process_video(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file not found '{input_path}'", file=sys.stderr)
        sys.exit(1)

    cap = open_video(str(input_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    ret, first_frame = cap.read()
    if not ret:
        print("Error: could not read first frame from video", file=sys.stderr)
        sys.exit(1)

    felt_lower = None
    felt_upper = None
    if args.calibrate:
        felt_lower, felt_upper = run_calibration(first_frame)

    tracker = BallTracker(felt_lower=felt_lower, felt_upper=felt_upper)

    writer = None
    if args.output:
        writer = create_writer(args.output, fps, (frame_width, frame_height))

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        proc_frame = resize_frame(frame, args.scale)
        tracks = tracker.update(proc_frame)
        display_tracks = scale_tracks_for_display(tracks, args.scale)
        annotated = draw_tracks(frame, display_tracks)

        if writer is not None:
            writer.write(annotated)

        if args.display:
            cv2.imshow("9-Ball Tracker", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        frame_idx += 1

    cap.release()
    if writer is not None:
        writer.release()
    if args.display:
        cv2.destroyAllWindows()

    print(f"Processed {frame_idx} frames.")


def main() -> None:
    args = parse_args()
    process_video(args)


if __name__ == "__main__":
    main()
