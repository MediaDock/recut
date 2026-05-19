# recut

Prepares content for the LED banner by slicing a 4160×104 image (or video frame) into three strips and composing them onto a 1920×1080 canvas.

A single input is remapped directly if it is 4160px wide, or tiled to fill 4160px if it is a fraction of that width. Multiple inputs are stitched side by side and the combined strip is tiled to fill 4160px — so two 1040px inputs become a 2080px unit that repeats twice. The combined width must evenly divide 4160, and each input's height must evenly divide 104. For videos with different lengths, shorter inputs freeze on their last frame.

![styleguide](.readme/styleguide.png)

## Prerequisites

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/download.html) on your `PATH` (video only)
- Supported formats: JPEG, PNG, BMP, TIFF, WebP (image) · MP4 (video)

## Usage

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 recut.py <input> [input2 ...]
```

Output is saved next to the first input with `_recut` appended (e.g. `banner.png` → `banner_recut.png`).
