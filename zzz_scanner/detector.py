"""
Detects S-rarity drive discs on the Routine Cleanup (Challenge Results) screen.

ZZZ marks rarity with a colored bar under each disc thumbnail: gold = S,
purple = A. We find the gold bars (by color) inside the reward grid region,
filter to the wide/short bar shape, and return a click point on the disc
*above* each bar — in reading order (left-to-right, top-to-bottom).

Restricting the search to RC_GRID_REGION keeps us away from the big orange "S"
rank graphic and other gold UI elsewhere on the screen.

(Music Store uses a fixed grid — see config.MS_GRID_POINTS — so it needs no
detection.)
"""
import cv2
import numpy as np
from PIL import Image

import config


def _search_offset() -> tuple[int, int]:
    """Top-left offset of the search region, for converting back to screen coords."""
    if config.RC_GRID_REGION:
        return config.RC_GRID_REGION["left"], config.RC_GRID_REGION["top"]
    return 0, 0


def _crop_to_region(arr: np.ndarray) -> np.ndarray:
    if config.RC_GRID_REGION:
        r = config.RC_GRID_REGION
        return arr[r["top"]: r["top"] + r["height"], r["left"]: r["left"] + r["width"]]
    return arr


def detect_s_discs(img: Image.Image) -> list[dict]:
    """
    Find S-rarity disc click points in the given screenshot.

    Returns a list of dicts in reading order:
        { "x": click_x, "y": click_y, "box": (x, y, w, h) }   # box = the gold bar
    Coordinates are absolute (screen-space, accounting for RC_GRID_REGION).
    """
    arr = np.array(img.convert("RGB"))
    arr_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    region = _crop_to_region(arr_bgr)
    off_x, off_y = _search_offset()

    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(
        hsv,
        np.array(config.RC_BAR_HSV_LOWER),
        np.array(config.RC_BAR_HSV_UPPER),
    )

    # Close horizontal gaps so each rarity bar is one solid blob.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    found = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if not (config.RC_BAR_MIN_WIDTH <= w <= config.RC_BAR_MAX_WIDTH):
            continue
        if not (config.RC_BAR_MIN_HEIGHT <= h <= config.RC_BAR_MAX_HEIGHT):
            continue
        # The bar is wider than it is tall — reject anything roughly square.
        if w < h * 2:
            continue
        bar_cx = off_x + x + w // 2
        bar_cy = off_y + y + h // 2
        found.append({
            "x": bar_cx,
            "y": bar_cy + config.RC_CARD_CLICK_Y_OFFSET,  # click up onto the disc
            "box": (off_x + x, off_y + y, w, h),
        })

    return _sort_reading_order(found)


def _sort_reading_order(items: list[dict]) -> list[dict]:
    """Sort top-to-bottom by row, then left-to-right within each row."""
    if not items:
        return []
    tol = config.RC_ROW_TOLERANCE
    items = sorted(items, key=lambda i: i["y"])
    rows: list[list[dict]] = []
    for it in items:
        placed = False
        for row in rows:
            if abs(row[0]["y"] - it["y"]) <= tol:
                row.append(it)
                placed = True
                break
        if not placed:
            rows.append([it])
    ordered = []
    for row in rows:
        ordered.extend(sorted(row, key=lambda i: i["x"]))
    return ordered
