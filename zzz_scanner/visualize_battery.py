"""
Draws a battery scan step (the 6-column grid points + bar-sample patches) and
the DETAIL panel region on an Obtain-screen screenshot, marking which slots are
detected as S-rarity. Use it to tune BATTERY_COLS_X, RC_BATTERY_PLANS, the bar
geometry, and BATTERY_PANEL_REGION.

Usage:
  python visualize_battery.py sample_images/RoutineCleanupBattery_1.png --count 1 --step 0
  python visualize_battery.py sample_images/RoutineCleanup_3Batteries_1_scroll.png --count 3 --step 1
"""
import sys
from PIL import Image, ImageDraw

import config
from detector import debug_battery


def _arg(args, name, default):
    return int(args[args.index(name) + 1]) if name in args else default


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python visualize_battery.py <screenshot.png> [--count N] [--step K] [--out out.png]")
        sys.exit(1)

    image_path = args[0]
    count = _arg(args, "--count", 1)
    step = _arg(args, "--step", 0)
    out_path = args[args.index("--out") + 1] if "--out" in args else "battery_check.png"

    plan = config.RC_BATTERY_PLANS.get(count)
    if not plan or step >= len(plan):
        print(f"No plan for count={count} step={step}. "
              f"count has {len(plan) if plan else 0} step(s).")
        sys.exit(1)
    scrolls, row_ys = plan[step]

    img = Image.open(image_path).convert("RGB")
    info = debug_battery(img, row_ys)
    draw = ImageDraw.Draw(img)

    # DETAIL panel region (blue)
    r = config.BATTERY_PANEL_REGION
    draw.rectangle([r["left"], r["top"], r["left"] + r["width"], r["top"] + r["height"]],
                   outline=(0, 120, 255), width=2)
    draw.text((r["left"] + 2, r["top"] - 18), "BATTERY_PANEL_REGION", fill=(0, 120, 255))

    hw = config.RC_BATTERY_BAR_SAMPLE_W // 2
    hh = config.RC_BATTERY_BAR_SAMPLE_H // 2
    for d in info:
        cx, cy = d["click"]
        bx, by = d["bar_point"]
        color = (0, 255, 0) if d["is_s"] else (255, 60, 60)
        draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=color)
        draw.rectangle([bx - hw, by - hh, bx + hw, by + hh], outline=color, width=2)

    img.save(out_path)
    s_count = sum(1 for d in info if d["is_s"])
    print(f"count={count} step={step} scrolls={scrolls} rows={row_ys}")
    print(f"Detected {s_count} S-rarity disc(s) of {len(info)} checked points.")
    for d in info:
        tag = "S" if d["is_s"] else "-"
        print(f"  [{tag}] {d['click']} bar={d['bar_point']} "
              f"match={d['match_fraction']} mean_rgb={d['mean_rgb']}")
    print(f"\nSaved -> {out_path}")
    print("Blue = panel crop, Green = detected S (click), Red = skipped. Box = bar sample.")


if __name__ == "__main__":
    main()
