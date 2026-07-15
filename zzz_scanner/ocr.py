"""
Image -> OCR text -> parsed drive disc data.
Uses rapidocr-onnxruntime (pure pip install, no system binaries needed).

Two detail layouts feed this, depending on the situation:
  - Routine Cleanup -> centered popup   (config.RC_POPUP_REGION)
  - Music Store      -> left side panel  (config.MS_PANEL_REGION)
Both render the same labelled text, so a single parser handles them.
"""
import cv2
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

import config
from parser import parse_popup_text

# Single shared engine instance (loads ONNX models once)
_engine = RapidOCR()

# Boxes whose top edges are within this many pixels count as the same row.
_ROW_TOLERANCE = 18


def load_image(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def preprocess(img: Image.Image) -> np.ndarray:
    """
    Upscale 2x + mild sharpening before OCR. The detail view has light text on
    a dark background, so contrast is already good.
    """
    arr = np.array(img)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    up = cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    blur = cv2.GaussianBlur(up, (0, 0), 3)
    sharp = cv2.addWeighted(up, 1.5, blur, -0.5, 0)
    return cv2.cvtColor(sharp, cv2.COLOR_GRAY2BGR)


def run_ocr(img: Image.Image) -> str:
    """
    Run RapidOCR and return text ordered top-to-bottom, and left-to-right
    within each row. Row ordering matters for the 2-column sub-stats layout so
    that "HP 3%" and "CRIT Rate 2.4%" stay paired with their values.
    """
    arr = preprocess(img)
    result, _ = _engine(arr)
    if not result:
        return ""

    # Each entry is [box, text, confidence]; box is 4 [x, y] corners.
    def top_left(entry):
        box = entry[0]
        ys = [p[1] for p in box]
        xs = [p[0] for p in box]
        return min(xs), min(ys)

    entries = sorted(result, key=lambda e: top_left(e)[1])  # by y first

    rows: list[list] = []
    for e in entries:
        ex, ey = top_left(e)
        for row in rows:
            if abs(row[0][1] - ey) <= _ROW_TOLERANCE:
                row.append((ex, ey, e[1]))
                break
        else:
            rows.append([(ex, ey, e[1])])

    lines = []
    for row in rows:
        row.sort(key=lambda r: r[0])  # left-to-right within the row
        lines.append(" ".join(text for _, _, text in row))
    return "\n".join(lines)


def extract_from_image(img: Image.Image) -> tuple[dict, str]:
    """Return (parsed_data, raw_ocr_text)."""
    raw = run_ocr(img)
    data = parse_popup_text(raw)
    return data, raw


def _region_for(situation: str) -> dict:
    if situation == "music_store":
        return config.MS_PANEL_REGION
    if situation == "battery":
        return config.BATTERY_PANEL_REGION
    return config.RC_POPUP_REGION


def capture_detail(situation: str) -> Image.Image:
    """Grab the detail region (popup or left panel) for the given situation."""
    import mss
    region = _region_for(situation)
    with mss.mss() as sct:
        shot = sct.grab(region)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


def extract_from_screen(situation: str) -> tuple[dict, str]:
    """Capture the detail region from the live game and extract data."""
    img = capture_detail(situation)
    return extract_from_image(img)
