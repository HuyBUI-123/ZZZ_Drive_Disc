"""
Draws an OCR crop region on a screenshot so you can verify alignment.

Pick the region with --rc (Routine Cleanup popup) or --ms (Music Store panel).
Defaults to --rc. (For the Routine Cleanup disc grid use visualize_detection.py.)

Usage:
  python visualize_region.py sample_images/detail_popup_1.png --rc
  python visualize_region.py sample_images/MusicStore_1.png --ms --out check.png
"""
import sys
from PIL import Image, ImageDraw

import config


def _pick_region(args):
    if "--ms" in args:
        return config.MS_PANEL_REGION, "MS_PANEL_REGION"
    return config.RC_POPUP_REGION, "RC_POPUP_REGION"


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python visualize_region.py <screenshot.png> [--rc|--ms|--grid] [--out output.png]")
        sys.exit(1)

    image_path = args[0]
    out_path = "region_check.png"
    if "--out" in args:
        out_path = args[args.index("--out") + 1]

    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    r, name = _pick_region(args)
    x0, y0 = r["left"], r["top"]
    x1, y1 = x0 + r["width"], y0 + r["height"]

    draw.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=3)
    label = f"{name} ({x0},{y0}) {r['width']}x{r['height']}px"
    draw.rectangle([x0, y0 - 22, x0 + len(label) * 8, y0], fill=(255, 0, 0))
    draw.text((x0 + 2, y0 - 20), label, fill=(255, 255, 255))

    img.save(out_path)
    print(f"Saved -> {out_path}")
    print(f"Region {name}: left={x0}, top={y0}, right={x1}, bottom={y1}")
    print("If misaligned, edit the region in config.py and re-run.")


if __name__ == "__main__":
    main()
