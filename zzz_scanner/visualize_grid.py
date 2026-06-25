"""
Draws the fixed Music Store grid (MS_GRID_POINTS) and the left detail panel
crop (MS_PANEL_REGION) on a Music Store screenshot, so you can verify the
click points land on each disc and the panel crop covers the text.

Usage:
  python visualize_grid.py sample_images/MusicStore_1.png
  python visualize_grid.py sample_images/MusicStore_1.png --out check.png
"""
import sys
from PIL import Image, ImageDraw

import config


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python visualize_grid.py <screenshot.png> [--out output.png]")
        sys.exit(1)

    image_path = args[0]
    out_path = "grid_check.png"
    if "--out" in args:
        out_path = args[args.index("--out") + 1]

    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Left detail panel crop (red box)
    r = config.MS_PANEL_REGION
    draw.rectangle(
        [r["left"], r["top"], r["left"] + r["width"], r["top"] + r["height"]],
        outline=(255, 0, 0), width=3,
    )
    draw.text((r["left"] + 2, r["top"] - 18), "MS_PANEL_REGION", fill=(255, 255, 0))

    # Grid click points (green crosshair + index)
    for i, (x, y) in enumerate(config.MS_GRID_POINTS, 1):
        draw.line([x - 14, y, x + 14, y], fill=(0, 255, 0), width=2)
        draw.line([x, y - 14, x, y + 14], fill=(0, 255, 0), width=2)
        draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 0, 0))
        draw.text((x + 10, y + 6), str(i), fill=(0, 255, 0))

    img.save(out_path)
    print(f"Plotted {len(config.MS_GRID_POINTS)} grid points + panel region.")
    for i, (x, y) in enumerate(config.MS_GRID_POINTS, 1):
        print(f"  #{i}: click at ({x}, {y})")
    print(f"\nSaved -> {out_path}")
    print("Red box = left panel crop, Green crosshair = disc click point.")
    print("If points are off, adjust _MS_COLS_X / _MS_ROWS_Y in config.py.")


if __name__ == "__main__":
    main()
