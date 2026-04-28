# recut

Slices a 4160×104 image into three strips and composes them onto a 1920×1080 canvas. Smaller images are accepted as long as their width evenly divides 4160 and their height evenly divides 104 — they are tiled to fill the full 4160×104 before processing.

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 slice_and_compose.py <input.jpg/png>
```
