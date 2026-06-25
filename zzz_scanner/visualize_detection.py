"""
Draws detected S-rarity discs on a Routine Cleanup screenshot so you can
verify detection before wiring up clicking.

Usage:
  python visualize_detection.py sample_images/routine_cleanup_obtain_1.png
  python visualize_detection.py sample_images/routine_cleanup_obtain_1.png --out check.png
  python visualize_detection.py sample_images/routine_cleanup_obtain_1.png --mask   # also save the HSV mask
"""
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw

import config
from detector import detect_s_discs, _crop_to_region


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python visualize_detection.py <screenshot.png> [--out output.png] [--mask]")
        sys.exit(1)

    image_path = args[0]
    out_path = "detection_check.png"
    if "--out" in args:
        out_path = args[args.index("--out") + 1]

    img = Image.open(image_path).convert("RGB")
    discs = detect_s_discs(img)

    draw = ImageDraw.Draw(img)

    # Draw the search region in blue
    if config.RC_GRID_REGION:
        r = config.RC_GRID_REGION
        draw.rectangle(
            [r["left"], r["top"], r["left"] + r["width"], r["top"] + r["height"]],
            outline=(0, 120, 255), width=2,
        )

    # Draw each detected gold bar in green + index + click point in red
    for i, t in enumerate(discs, 1):
        x, y, w, h = t["box"]
        draw.rectangle([x, y, x + w, y + h], outline=(0, 255, 0), width=3)
        draw.ellipse([t["x"] - 6, t["y"] - 6, t["x"] + 6, t["y"] + 6], fill=(255, 0, 0))
        draw.text((x + 4, y - 16), str(i), fill=(255, 255, 0))

    img.save(out_path)
    print(f"Detected {len(discs)} S-rarity disc(s).")
    for i, t in enumerate(discs, 1):
        print(f"  #{i}: click at ({t['x']}, {t['y']})  bar box={t['box']}")
    print(f"\nSaved → {out_path}")
    print("Blue = search region, Green = detected gold bar, Red dot = click point.")

    # Optionally dump the raw HSV mask for tuning the color range
    if "--mask" in args:
        arr = cv2.cvtColor(np.array(Image.open(image_path).convert("RGB")), cv2.COLOR_RGB2BGR)
        region = _crop_to_region(arr)
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(
            hsv, np.array(config.RC_BAR_HSV_LOWER), np.array(config.RC_BAR_HSV_UPPER)
        )
        cv2.imwrite("detection_mask.png", mask)
        print("Saved HSV mask → detection_mask.png (white = matched color)")


if __name__ == "__main__":
    main()
