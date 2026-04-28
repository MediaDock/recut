# recut

Slices a 4160×104 image (or video frame) into three strips and composes them onto a 1920×1080 canvas. Smaller inputs are accepted as long as their width evenly divides 4160 and their height evenly divides 104 — they are tiled to fill the full 4160×104 before processing. Video output is re-encoded with H.264 and audio is preserved; requires `ffmpeg` on your PATH.

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 recut.py <input.jpg/png/mp4>
```
