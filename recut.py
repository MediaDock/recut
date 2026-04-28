from pathlib import Path
from PIL import Image
import cv2
import numpy as np
import os
import subprocess
import sys
import tempfile

VIDEO_EXTENSIONS = frozenset({".mp4"})
IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"})

_TARGET_W = 4160
_TARGET_H = 104


def _validate(width: int, height: int) -> None:
    if _TARGET_W % width != 0:
        print(f"Error: width {width} does not evenly divide {_TARGET_W}")
        sys.exit(1)
    if _TARGET_H % height != 0:
        print(f"Error: height {height} does not evenly divide {_TARGET_H}")
        sys.exit(1)


def _transform(img: Image.Image) -> Image.Image:
    nx = _TARGET_W // img.width
    ny = _TARGET_H // img.height
    if nx > 1 or ny > 1:
        tiled = Image.new("RGB", (_TARGET_W, _TARGET_H))
        for row in range(ny):
            for col in range(nx):
                tiled.paste(img, (col * img.width, row * img.height))
        img = tiled

    piece1 = img.crop((0,    0, 1872, _TARGET_H))
    piece2 = img.crop((1872, 0, 3744, _TARGET_H))
    piece3 = img.crop((3744, 0, _TARGET_W, _TARGET_H))

    canvas = Image.new("RGB", (1920, 1080), color=(255, 255, 255))
    canvas.paste(piece1, (0, 0))
    canvas.paste(piece2, (0, _TARGET_H))
    canvas.paste(piece3, (0, _TARGET_H * 2))
    return canvas


def _transform_bgr(frame: np.ndarray) -> np.ndarray:
    pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    return cv2.cvtColor(np.array(_transform(pil)), cv2.COLOR_RGB2BGR)


def process_image(input_path: Path) -> None:
    try:
        img = Image.open(input_path)
    except FileNotFoundError:
        print(f"Error: file not found: {input_path}")
        sys.exit(1)
    except Image.UnidentifiedImageError:
        print(f"Error: not a valid image: {input_path}")
        sys.exit(1)

    _validate(img.width, img.height)
    canvas = _transform(img)

    output_path = input_path.with_stem(input_path.stem + "_recut")
    canvas.save(output_path)
    print(f"Saved to {output_path}")


def process_video(input_path: Path) -> None:
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        print(f"Error: cannot open video: {input_path}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    _validate(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
    os.close(tmp_fd)

    try:
        writer = cv2.VideoWriter(
            tmp_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (1920, 1080),
        )

        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            writer.write(_transform_bgr(frame))
            idx += 1
            label = str(frame_count) if frame_count else "?"
            print(f"\rFrame {idx}/{label}", end="", flush=True)

        cap.release()
        writer.release()
        print()

        output_path = input_path.with_stem(input_path.stem + "_recut")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", tmp_path,
                    "-i", str(input_path),
                    "-map", "0:v:0",
                    "-map", "1:a?",
                    "-c:v", "libx264",
                    "-crf", "18",
                    "-c:a", "copy",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
            )
        except FileNotFoundError:
            print("Error: ffmpeg not found — install it to process video")
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"Error: ffmpeg failed:\n{e.stderr.decode()}")
            sys.exit(1)
    finally:
        cap.release()
        os.unlink(tmp_path)

    print(f"Saved to {output_path}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python slice_and_compose.py <input>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    ext = input_path.suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        process_image(input_path)
    elif ext in VIDEO_EXTENSIONS:
        process_video(input_path)
    else:
        print(f"Error: unsupported file type '{ext}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
