from PIL import Image
import os
import sys

def process_image(input_path: str):
    base, ext = os.path.splitext(input_path)
    output_path = f"{base}_recut{ext}"

    try:
        img = Image.open(input_path)
    except FileNotFoundError:
        print(f"Error: file not found: {input_path}")
        sys.exit(1)
    except Image.UnidentifiedImageError:
        print(f"Error: not a valid image: {input_path}")
        sys.exit(1)

    if 4160 % img.width != 0:
        print(f"Error: width {img.width} is not an integer divisor of 4160")
        sys.exit(1)

    if 104 % img.height != 0:
        print(f"Error: height {img.height} is not an integer divisor of 104")
        sys.exit(1)

    nx = 4160 // img.width
    ny = 104 // img.height
    if nx > 1 or ny > 1:
        tiled = Image.new("RGB", (4160, 104))
        for row in range(ny):
            for col in range(nx):
                tiled.paste(img, (col * img.width, row * img.height))
        img = tiled

    # Cut the 3 pieces
    piece1 = img.crop((0,    0, 1872, 104))  # 1872x104
    piece2 = img.crop((1872, 0, 3744, 104))  # 1872x104
    piece3 = img.crop((3744, 0, 4160, 104))  #  416x104

    # Create white canvas
    canvas = Image.new("RGB", (1920, 1080), color=(255, 255, 255))

    # Place pieces
    canvas.paste(piece1, (0, 0))    # top-left at (0,   0)
    canvas.paste(piece2, (0, 104))  # top-left at (0, 104)
    canvas.paste(piece3, (0, 208))  # top-left at (0, 208)

    try:
        canvas.save(output_path)
    except FileNotFoundError:
        print(f"Error: output directory does not exist: {output_path}")
        sys.exit(1)
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python slice_and_compose.py <input.jpg/png>")
        sys.exit(1)

    process_image(sys.argv[1])
