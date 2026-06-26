"""
Click automation: drives the mouse through the discs and OCRs each detail view,
branching on the situation (source) the user picked.

  Routine Cleanup:
    Detect the S-rarity discs (gold bars), then for each one
        click disc -> wait -> capture+OCR popup -> dismiss popup -> next
    (the popup overlaps the grid, so it must be dismissed between clicks).

  Music Store:
    A fixed 2x5 grid of 10 discs with a persistent left detail panel, so
        click disc -> wait -> capture+OCR left panel -> next
    (no popup to dismiss).
"""
import time
import mss
import pyautogui
from PIL import Image

import config
from detector import detect_s_discs
from ocr import extract_from_image, capture_detail

# Move mouse to a screen corner to abort the whole run at any time.
pyautogui.FAILSAFE = True


def capture_full_screen() -> Image.Image:
    """Grab the entire primary monitor."""
    with mss.mss() as sct:
        mon = sct.monitors[1]
        shot = sct.grab(mon)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def _click(x: int, y: int) -> None:
    pyautogui.moveTo(x, y, duration=config.MOUSE_MOVE_DURATION)
    pyautogui.click()


def _dismiss_popup() -> None:
    x, y = config.RC_DISMISS_POINT
    pyautogui.moveTo(x, y, duration=config.MOUSE_MOVE_DURATION)
    pyautogui.click()
    time.sleep(config.DISMISS_WAIT)


def _read_one(situation: str, x: int, y: int, index: int) -> dict:
    """Click a disc, OCR its detail view, return the parsed dict."""
    _click(x, y)
    time.sleep(config.CLICK_WAIT)

    detail_img = capture_detail(situation)
    data, raw = extract_from_image(detail_img)
    data["_index"] = index
    data["_click"] = (x, y)
    data["_image"] = detail_img  # kept in memory for the rating UI; not exported

    print(f"\n----- Disc #{index + 1}  (click {x},{y}) -----")
    print("[RAW OCR]")
    print(raw)
    parsed = {k: v for k, v in data.items() if not k.startswith("_")}
    print("[PARSED]", parsed)

    return data


def _scan_routine_cleanup(progress_cb=None) -> list[dict]:
    screen = capture_full_screen()
    discs = detect_s_discs(screen)

    results: list[dict] = []
    total = len(discs)
    for i, d in enumerate(discs):
        data = _read_one("routine_cleanup", d["x"], d["y"], i)
        results.append(data)
        if progress_cb:
            progress_cb(i + 1, total, data)
        _dismiss_popup()  # uncover the grid for the next click
    return results


def _scan_music_store(progress_cb=None) -> list[dict]:
    points = config.MS_GRID_POINTS
    results: list[dict] = []
    total = len(points)
    for i, (x, y) in enumerate(points):
        data = _read_one("music_store", x, y, i)
        results.append(data)
        if progress_cb:
            progress_cb(i + 1, total, data)
    return results


def scan_all(source: str, progress_cb=None) -> list[dict]:
    """
    Scan every disc for the given source.

    progress_cb(done, total, data) is called after each disc, if given.
    Returns a list of parsed-disc dicts (with debug fields).
    """
    situation = config.get_situation(source)
    if situation == "music_store":
        return _scan_music_store(progress_cb)
    return _scan_routine_cleanup(progress_cb)


def scan_single_at(situation: str, x: int, y: int) -> tuple[dict, str]:
    """Click one given point, OCR its detail view. For debugging timing."""
    _click(x, y)
    time.sleep(config.CLICK_WAIT)
    detail_img = capture_detail(situation)
    data, raw = extract_from_image(detail_img)
    if situation != "music_store":
        _dismiss_popup()
    return data, raw
