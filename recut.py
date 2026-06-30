from pathlib import Path
from PIL import Image
import cv2
import numpy as np
import os
import subprocess
import sys
import tempfile

VIDEO_EXTENSIONS = frozenset({".mp4", ".mov"})
IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"})

_TARGET_W = 4160
_TARGET_H = 104


def _validate(total_w: int, heights: list) -> None:
    if _TARGET_W % total_w != 0:
        print(f"Error: combined width {total_w} does not evenly divide {_TARGET_W}")
        sys.exit(1)
    for h in heights:
        if _TARGET_H % h != 0:
            print(f"Error: height {h} does not evenly divide {_TARGET_H}")
            sys.exit(1)


def _tile_to(img: Image.Image, w: int, h: int) -> Image.Image:
    nx, ny = w // img.width, h // img.height
    if nx == 1 and ny == 1:
        return img
    tiled = Image.new("RGB", (w, h))
    for row in range(ny):
        for col in range(nx):
            tiled.paste(img, (col * img.width, row * img.height))
    return tiled


def _compose(imgs: list) -> Image.Image:
    strips = [_tile_to(img, img.width, _TARGET_H) for img in imgs]
    total_w = sum(s.width for s in strips)
    stitched = Image.new("RGB", (total_w, _TARGET_H))
    x = 0
    for s in strips:
        stitched.paste(s, (x, 0))
        x += s.width
    return _transform(_tile_to(stitched, _TARGET_W, _TARGET_H))


def _transform(img: Image.Image) -> Image.Image:
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


def _frame_to_pil(frame: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


def _pil_to_bgr(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def process_image(paths: list) -> None:
    imgs = []
    for p in paths:
        try:
            img = Image.open(p)
        except FileNotFoundError:
            print(f"Error: file not found: {p}")
            sys.exit(1)
        except Image.UnidentifiedImageError:
            print(f"Error: not a valid image: {p}")
            sys.exit(1)
        imgs.append(img)

    _validate(sum(img.width for img in imgs), [img.height for img in imgs])

    canvas = _compose(imgs)
    stem = "_".join(p.stem for p in paths) + "_recut"
    output_path = paths[0].with_stem(stem)
    canvas.save(output_path)
    print(f"Saved to {output_path}")


def process_video(paths: list) -> None:
    n = len(paths)

    caps = []
    static_frames = []  # BGR frame for image inputs, None for video inputs
    for p in paths:
        if p.suffix.lower() in IMAGE_EXTENSIONS:
            try:
                img = Image.open(p).convert("RGB")
            except (FileNotFoundError, Image.UnidentifiedImageError) as e:
                print(f"Error: cannot open image: {p}")
                sys.exit(1)
            caps.append(None)
            static_frames.append(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
        else:
            cap = cv2.VideoCapture(str(p))
            if not cap.isOpened():
                print(f"Error: cannot open video: {p}")
                sys.exit(1)
            caps.append(cap)
            static_frames.append(None)

    # Per-input source fps (None for image inputs); cap the output at 30 fps
    # so the player stays smooth on playback.
    src_fps = [None if cap is None else (cap.get(cv2.CAP_PROP_FPS) or 0.0) for cap in caps]
    video_fps = [f for f in src_fps if f]
    if not video_fps:
        print("Error: could not determine frame rate of any video input")
        sys.exit(1)
    out_fps = min(max(video_fps), 30.0)

    # Output length is driven by the longest input in *time*, not frame count.
    durations = []
    for i, cap in enumerate(caps):
        if cap is None:
            continue
        fc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if fc > 0 and src_fps[i]:
            durations.append(fc / src_fps[i])
    total_out_frames = round(max(durations) * out_fps) if len(durations) == len(video_fps) else 0

    widths, heights = [], []
    for i, p in enumerate(paths):
        if caps[i] is None:
            h, w = static_frames[i].shape[:2]
        else:
            w = int(caps[i].get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(caps[i].get(cv2.CAP_PROP_FRAME_HEIGHT))
        widths.append(w)
        heights.append(h)
    _validate(sum(widths), heights)

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
    os.close(tmp_fd)

    writer = None
    try:
        writer = cv2.VideoWriter(
            tmp_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            out_fps,
            (1920, 1080),
        )

        last_frames = [None] * n
        read_count = [-1] * n                   # index of last frame read per video cap
        ended = [cap is None for cap in caps]    # image inputs never "end"
        idx = 0

        while True:
            if total_out_frames and idx >= total_out_frames:
                break

            out_t = idx / out_fps
            frames = []
            for i, cap in enumerate(caps):
                if cap is None:
                    frames.append(static_frames[i])
                    continue
                # Advance this video to the source frame matching the output time,
                # so every input plays at real-time speed regardless of its fps.
                target = round(out_t * src_fps[i])
                while read_count[i] < target and not ended[i]:
                    ok, frame = cap.read()
                    if ok:
                        read_count[i] += 1
                        last_frames[i] = frame
                    else:
                        ended[i] = True
                frames.append(last_frames[i])

            if all(ended):
                break

            if any(f is None for f in frames):
                print("\nError: one or more inputs yielded no readable frames")
                sys.exit(1)

            pils = [_frame_to_pil(f) for f in frames]
            out_frame = _pil_to_bgr(_compose(pils))

            writer.write(out_frame)
            idx += 1
            label = str(total_out_frames) if total_out_frames else "?"
            print(f"\rFrame {idx}/{label}", end="", flush=True)

        writer.release()
        writer = None
        print()

        stem = "_".join(p.stem for p in paths) + "_recut"
        video_path = next(p for p in paths if p.suffix.lower() in VIDEO_EXTENSIONS)
        output_path = video_path.parent / (stem + video_path.suffix)
        print(f"Encoding {idx} frames with libx265 (this can take a while on long clips)...")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-hide_banner", "-loglevel", "warning", "-stats",
                    "-i", tmp_path,
                    "-map", "0:v:0",
                    "-c:v", "libx265",
                    "-crf", "18",
                    str(output_path),
                ],
                check=True,
            )
        except FileNotFoundError:
            print("Error: ffmpeg not found — install it to process video")
            sys.exit(1)
        except subprocess.CalledProcessError:
            print("Error: ffmpeg failed (see output above)")
            sys.exit(1)
    finally:
        for cap in caps:
            if cap is not None:
                cap.release()
        if writer is not None:
            writer.release()
        os.unlink(tmp_path)

    print(f"Saved to {output_path}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python recut.py <input> [input2 ...]")
        sys.exit(1)

    paths = [Path(a) for a in sys.argv[1:]]
    for p in paths:
        if not p.exists():
            print(f"Error: file not found: {p}")
            sys.exit(1)

    exts = [p.suffix.lower() for p in paths]
    unknown = [p for p in paths if p.suffix.lower() not in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS]
    if unknown:
        print(f"Error: unsupported file type '{unknown[0].suffix}'")
        sys.exit(1)

    has_video = any(e in VIDEO_EXTENSIONS for e in exts)
    has_image = any(e in IMAGE_EXTENSIONS for e in exts)

    if has_video:
        process_video(paths)
    else:
        process_image(paths)


if __name__ == "__main__":
    main()
