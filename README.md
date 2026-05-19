# recut

Prepares content for the LED banner by slicing an image (or video frame) into three strips and composing them onto a display canvas.

| | |
|---|---|
| LED wall | 4160 × 104 px |
| Output canvas | 1920 × 1080 px |
| Input width | must evenly divide 4160 px (e.g. 1040, 2080, 4160) |
| Input height | must evenly divide 104 px |
| Image formats | JPEG, PNG, BMP, TIFF, WebP |
| Video formats | MP4 |

A single input is remapped directly if it is 4160 px wide, or tiled to fill 4160 px if narrower. Multiple inputs are stitched side by side and the combined strip is tiled — so two 1040 px inputs become a 2080 px unit that repeats twice. The combined width must evenly divide 4160, and each input's height must evenly divide 104. For videos with different lengths, shorter inputs freeze on their last frame.

![styleguide](.readme/styleguide.png)

## Prerequisites

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/download.html) on your `PATH` (video only)

## Usage

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 recut.py <input> [input2 ...]
```

Output is saved next to the first input with `_recut` appended (e.g. `banner.png` → `banner_recut.png`).
