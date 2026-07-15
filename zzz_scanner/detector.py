"""
Detects S-rarity discs by checking a fixed set of grid points for the gold
rarity bar just below each disc.

Two situations use this:
  - Routine Cleanup (Challenge Results): a fixed 2x4 grid (config.RC_GRID_POINTS).
  - Routine Cleanup - Battery (Obtain screen): a 6-column grid, scanned per
    scroll step via config.RC_BATTERY_PLANS.

In both, a slot is S-rarity when enough of the sampled bar patch matches the
exact gold colour (config.RC_S_BAR_*). Music Store needs no rarity check (all
10 discs are S), so it isn't handled here.
"""
import numpy as np
from PIL import Image

import config


def _match_fraction(arr, cx, cy, offset, hw, hh, target, tol):
    """Fraction of the bar-sample patch (below a disc) matching the gold colour."""
    by = cy + offset
    h, w, _ = arr.shape
    y0, y1 = max(0, by - hh), min(h, by + hh + 1)
    x0, x1 = max(0, cx - hw), min(w, cx + hw + 1)
    if y0 >= y1 or x0 >= x1:
        return 0.0, by, np.empty((0, 3), dtype=int)
    patch = arr[y0:y1, x0:x1].reshape(-1, 3).astype(int)
    match = np.all(np.abs(patch - target) <= tol, axis=1)
    return float(match.mean()), by, patch


def _detect(arr, points, offset, sample_w, sample_h) -> list[dict]:
    target = np.array(config.RC_S_BAR_COLOR, dtype=int)
    tol = config.RC_S_BAR_TOLERANCE
    min_frac = config.RC_S_BAR_MIN_FRACTION
    hw, hh = sample_w // 2, sample_h // 2

    out = []
    for cx, cy in points:
        frac, by, _ = _match_fraction(arr, cx, cy, offset, hw, hh, target, tol)
        if frac >= min_frac:
            out.append({"x": cx, "y": cy, "bar": (cx, by)})
    return out


def _debug(arr, points, offset, sample_w, sample_h) -> list[dict]:
    target = np.array(config.RC_S_BAR_COLOR, dtype=int)
    tol = config.RC_S_BAR_TOLERANCE
    min_frac = config.RC_S_BAR_MIN_FRACTION
    hw, hh = sample_w // 2, sample_h // 2

    out = []
    for i, (cx, cy) in enumerate(points):
        frac, by, patch = _match_fraction(arr, cx, cy, offset, hw, hh, target, tol)
        mean = tuple(int(v) for v in patch.mean(axis=0)) if patch.size else (0, 0, 0)
        out.append({
            "index": i,
            "click": (cx, cy),
            "bar_point": (cx, by),
            "match_fraction": round(frac, 3),
            "mean_rgb": mean,
            "is_s": frac >= min_frac,
        })
    return out


# ---------------------------------------------------------------------------
# Routine Cleanup (Challenge Results) — fixed 2x4 grid
# ---------------------------------------------------------------------------
def detect_s_discs(img: Image.Image) -> list[dict]:
    """S-rarity discs in the fixed grid, in reading order."""
    arr = np.array(img.convert("RGB"))
    return _detect(arr, config.RC_GRID_POINTS,
                   config.RC_BAR_CHECK_OFFSET,
                   config.RC_BAR_SAMPLE_W, config.RC_BAR_SAMPLE_H)


def debug_grid(img: Image.Image) -> list[dict]:
    """Per-slot diagnostics for all grid positions, for tuning."""
    arr = np.array(img.convert("RGB"))
    return _debug(arr, config.RC_GRID_POINTS,
                  config.RC_BAR_CHECK_OFFSET,
                  config.RC_BAR_SAMPLE_W, config.RC_BAR_SAMPLE_H)


# ---------------------------------------------------------------------------
# Routine Cleanup - Battery (Obtain screen) — 6-column grid, per scroll step
# ---------------------------------------------------------------------------
def _battery_points(row_ys: list[int]) -> list[tuple[int, int]]:
    """All (column, row) points for the given row Y centers, in reading order."""
    return [(x, y) for y in row_ys for x in config.BATTERY_COLS_X]


def detect_s_battery(img: Image.Image, row_ys: list[int]) -> list[dict]:
    """S-rarity discs among the 6 columns on each of the given rows."""
    arr = np.array(img.convert("RGB"))
    return _detect(arr, _battery_points(row_ys),
                   config.RC_BATTERY_BAR_CHECK_OFFSET,
                   config.RC_BATTERY_BAR_SAMPLE_W, config.RC_BATTERY_BAR_SAMPLE_H)


def debug_battery(img: Image.Image, row_ys: list[int]) -> list[dict]:
    """Per-point diagnostics for a battery scan step, for tuning."""
    arr = np.array(img.convert("RGB"))
    return _debug(arr, _battery_points(row_ys),
                  config.RC_BATTERY_BAR_CHECK_OFFSET,
                  config.RC_BATTERY_BAR_SAMPLE_W, config.RC_BATTERY_BAR_SAMPLE_H)
