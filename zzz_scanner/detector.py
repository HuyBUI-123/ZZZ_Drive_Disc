"""
Detects S-rarity discs on the Routine Cleanup (Challenge Results) screen.

The 8 reward discs sit in a FIXED 2x4 grid (like Music Store) and mix S and A
rarity. Rather than colour-detecting bars anywhere on screen (which also picks
up gold disc artwork and the yellow set-name text), we check each fixed grid
slot: sample the small bar area just below the disc and, if enough of it
matches the exact gold S-rarity colour, it's an S disc worth clicking.

(Music Store uses a fixed grid too — see config.MS_GRID_POINTS — but all 10 of
its discs are S, so it needs no rarity check.)
"""
import numpy as np
from PIL import Image

import config


def _bar_patch(arr: np.ndarray, cx: int, cy: int):
    """Return (patch_pixels, bar_center_y) for the bar area below a disc."""
    by = cy + config.RC_BAR_CHECK_OFFSET
    hw = config.RC_BAR_SAMPLE_W // 2
    hh = config.RC_BAR_SAMPLE_H // 2
    h, w, _ = arr.shape
    y0, y1 = max(0, by - hh), min(h, by + hh + 1)
    x0, x1 = max(0, cx - hw), min(w, cx + hw + 1)
    if y0 >= y1 or x0 >= x1:
        return np.empty((0, 3), dtype=int), by
    return arr[y0:y1, x0:x1].reshape(-1, 3).astype(int), by


def _bar_match_fraction(patch: np.ndarray) -> float:
    """Fraction of patch pixels within tolerance of the S-rarity gold colour."""
    if patch.size == 0:
        return 0.0
    target = np.array(config.RC_S_BAR_COLOR, dtype=int)
    match = np.all(np.abs(patch - target) <= config.RC_S_BAR_TOLERANCE, axis=1)
    return float(match.mean())


def detect_s_discs(img: Image.Image) -> list[dict]:
    """
    Check each fixed grid slot and return the S-rarity ones in reading order:
        { "x": click_x, "y": click_y, "bar": (bar_x, bar_y) }
    """
    arr = np.array(img.convert("RGB"))
    results = []
    for cx, cy in config.RC_GRID_POINTS:
        patch, by = _bar_patch(arr, cx, cy)
        if _bar_match_fraction(patch) >= config.RC_S_BAR_MIN_FRACTION:
            results.append({"x": cx, "y": cy, "bar": (cx, by)})
    return results


def debug_grid(img: Image.Image) -> list[dict]:
    """Per-slot diagnostics for all 8 positions (S or not), for tuning."""
    arr = np.array(img.convert("RGB"))
    out = []
    for i, (cx, cy) in enumerate(config.RC_GRID_POINTS):
        patch, by = _bar_patch(arr, cx, cy)
        frac = _bar_match_fraction(patch)
        mean = tuple(int(v) for v in patch.mean(axis=0)) if patch.size else (0, 0, 0)
        out.append({
            "index": i,
            "click": (cx, cy),
            "bar_point": (cx, by),
            "match_fraction": round(frac, 3),
            "mean_rgb": mean,
            "is_s": frac >= config.RC_S_BAR_MIN_FRACTION,
        })
    return out
