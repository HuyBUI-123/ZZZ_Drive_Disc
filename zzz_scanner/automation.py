"""
Click automation: drives the mouse through the detected thumbnails,
OCRs each detail popup, and returns the parsed artifacts.

Flow per artifact (popup overlaps center thumbnails, so we must dismiss
between each one before the next click lands on a thumbnail):
    click thumbnail -> wait -> capture+OCR popup -> dismiss popup -> next
"""
import time
import mss
import pyautogui
from PIL import Image

import config
from detector import detect_thumbnails
from ocr import extract_from_image, capture_popup

# Move mouse to a screen corner to abort the whole run at any time.
pyautogui.FAILSAFE = True


def capture_full_screen() -> Image.Image:
    """Grab the entire primary monitor."""
    with mss.mss() as sct:
        mon = sct.monitors[1]
        shot = sct.grab(mon)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def _dismiss_popup() -> None:
    x, y = config.POPUP_DISMISS_POINT
    pyautogui.moveTo(x, y, duration=config.MOUSE_MOVE_DURATION)
    pyautogui.click()
    time.sleep(config.DISMISS_WAIT)


def scan_all(progress_cb=None) -> list[dict]:
    """
    Detect every 5-star thumbnail, click through each, OCR its popup.

    progress_cb(done, total, data) is called after each artifact, if given.
    Returns a list of parsed-artifact dicts (with debug fields).
    """
    screen = capture_full_screen()
    thumbs = detect_thumbnails(screen)

    results: list[dict] = []
    total = len(thumbs)

    for i, t in enumerate(thumbs):
        # Click the thumbnail
        pyautogui.moveTo(t["x"], t["y"], duration=config.MOUSE_MOVE_DURATION)
        pyautogui.click()
        time.sleep(config.POPUP_WAIT)

        # Read the popup
        popup_img = capture_popup()
        data, raw = extract_from_image(popup_img)
        data["_index"] = i
        data["_click"] = (t["x"], t["y"])
        data["_image"] = popup_img  # kept in memory for the rating UI; not exported
        results.append(data)

        if progress_cb:
            progress_cb(i + 1, total, data)

        # Dismiss so the next thumbnail isn't hidden behind the popup
        _dismiss_popup()

    return results


def scan_single_at(x: int, y: int) -> tuple[dict, str]:
    """Click one given point, OCR its popup, dismiss. For debugging timing."""
    pyautogui.moveTo(x, y, duration=config.MOUSE_MOVE_DURATION)
    pyautogui.click()
    time.sleep(config.POPUP_WAIT)
    popup_img = capture_popup()
    data, raw = extract_from_image(popup_img)
    _dismiss_popup()
    return data, raw
