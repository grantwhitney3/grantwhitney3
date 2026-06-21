# 9-Ball Rack Ball Tracker

OpenCV-based tool that detects and tracks pool balls in top-down table video, highlights each ball with a circle, and overlays numbered labels (1–9) when color classification is confident.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Process a video and save annotated output
python track_9ball_rack.py --input path/to/video.mp4 --output annotated.mp4

# Show live preview while processing
python track_9ball_rack.py --input path/to/video.mp4 --display

# Tune HSV color ranges for your lighting and felt color
python track_9ball_rack.py --input path/to/video.mp4 --calibrate
```

### CLI flags

| Flag | Description |
|------|-------------|
| `--input` | Path to input video (required) |
| `--output` | Path to save annotated MP4 |
| `--display` | Show live preview window |
| `--calibrate` | Interactive HSV slider mode for felt and ball colors |
| `--scale` | Resize factor for processing (default: 1.0; use 0.5 for speed) |

Press `q` in the preview window to quit early.

## How it works

1. **Felt masking** — Isolates the green/blue table surface to reduce false detections.
2. **Circle detection** — Uses Hough circle transform to find ball candidates.
3. **Color classification** — Maps HSV color in each ball's center to a ball number (1–9).
4. **Stripe detection** — Distinguishes solid yellow (1) from striped yellow (9) via white-band ratio.
5. **Tracking** — Associates detections across frames by nearest-neighbor matching so labels persist through movement.
6. **Rack heuristics** — When balls are tightly clustered, uses diamond-rack geometry (apex → 1, center → 9) as a fallback.

## Tuning tips

- Use a **fixed overhead camera** with consistent lighting for best results.
- If balls are missed or false positives appear, run `--calibrate` to adjust felt HSV bounds.
- Ball radius scales with frame width automatically; very high or low camera angles may need a different `--scale`.
- Hardest pairs to distinguish: **1 vs 9** (both yellow) and **7 vs 8** (both dark). Expect occasional mislabels under poor lighting.

## Limitations

- No deep-learning model — fast and lightweight, but not competition-grade accuracy.
- Works best on standard APA/BCA ball colors over green or blue felt.
- Overlapping balls in a tight rack may produce low-confidence labels until balls separate.
