"""
Draws the fixed Routine Cleanup disc grid + each disc's bar-sample patch on a
screenshot, marking which slots are detected as S-rarity (gold bar). Use it to
tune the grid coords (config._RC_COLS_X / _RC_ROWS_Y) and the S bar colour
(config.RC_S_BAR_COLOR / RC_S_BAR_TOLERANCE / RC_S_BAR_MIN_FRACTION).

Usage:
  python visualize_detection.py sample_images/routine_cleanup_obtain_1.png
  python visualize_detection.py sample_images/routine_cleanup_obtain_1.png --out check.png
"""
import sys
from PIL import Image, ImageDraw

import config
from detector import debug_grid


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python visualize_detection.py <screenshot.png> [--out output.png]")
        sys.exit(1)

    image_path = args[0]
    out_path = "detection_check.png"
    if "--out" in args:
        out_path = args[args.index("--out") + 1]

    img = Image.open(image_path).convert("RGB")
    info = debug_grid(img)
    draw = ImageDraw.Draw(img)

    hw = config.RC_BAR_SAMPLE_W // 2
    hh = config.RC_BAR_SAMPLE_H // 2
    for d in info:
        cx, cy = d["click"]
        bx, by = d["bar_point"]
        color = (0, 255, 0) if d["is_s"] else (255, 60, 60)
        # disc click point
        draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=color)
        # bar sample patch
        draw.rectangle([bx - hw, by - hh, bx + hw, by + hh], outline=color, width=2)
        draw.text((cx + 8, cy - 18), str(d["index"] + 1), fill=color)

    img.save(out_path)
    s_count = sum(1 for d in info if d["is_s"])
    print(f"Detected {s_count} S-rarity disc(s) of {len(info)} grid slots.")
    for d in info:
        tag = "S" if d["is_s"] else "-"
        print(f"  [{tag}] #{d['index'] + 1} click={d['click']} bar={d['bar_point']} "
              f"match={d['match_fraction']} mean_rgb={d['mean_rgb']}")
    print(f"\nSaved -> {out_path}")
    print("Green = detected S (will click), Red = skipped. Box = bar sample area.")


if __name__ == "__main__":
    main()
