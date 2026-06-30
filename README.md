# recut

Prepares content for the LED banner by slicing an image (or video frame) into three strips and composing them onto a display canvas.

| | |
|---|---|
| LED wall | 4160 × 104 px |
| Input width | must evenly divide 4160 px (e.g. 1040, 2080, 4160) |
| Input height | must evenly divide 104 px |
| Image formats | JPEG, PNG, BMP, TIFF, WebP |
| Video formats | MP4, MOV |

A single input is remapped directly if it is 4160 px wide, or tiled to fill 4160 px if narrower. Multiple inputs are stitched side by side and the combined strip is tiled — so two 1040 px inputs become a 2080 px unit that repeats twice. The combined width must evenly divide 4160, and each input's height must evenly divide 104. For videos with different lengths, shorter inputs freeze on their last frame. Images and videos can be mixed freely — images are treated as static frames held for the full duration of the video.

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

Output is saved next to the first video input (or first input for images only). The filename joins all input stems with `_` and appends `_recut` (e.g. `clip1.mov + texture.jpg` → `clip1_texture_recut.mov`).
