import os
import sys
import json


def _app_dir() -> str:
    """Folder to write output to: next to the .exe when frozen, else this script."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# Final export, ready to upload to the web app (written next to the app)
EXPORT_FILE = os.path.join(_app_dir(), "drive_discs_export.json")

# Small settings file that persists user choices (e.g. last save path)
# across runs, including in the built .exe.
SETTINGS_FILE = os.path.join(_app_dir(), "scanner_settings.json")


def load_settings() -> dict:
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(data: dict) -> None:
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


def get_export_path() -> str:
    """Last-used save path, falling back to the default export file."""
    return load_settings().get("export_path") or EXPORT_FILE


def set_export_path(path: str) -> None:
    s = load_settings()
    s["export_path"] = path
    save_settings(s)


def get_source() -> str:
    """Last-used source, falling back to the default."""
    val = load_settings().get("source")
    return val if val in SOURCE_OPTIONS else SOURCE


def set_source(value: str) -> None:
    s = load_settings()
    s["source"] = value
    save_settings(s)


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
# Target resolution. All regions/coordinates below are in screen pixels at
# this resolution. (Reference screenshots were 2560x1440.)
SCREEN_WIDTH = 2560
SCREEN_HEIGHT = 1440


# ---------------------------------------------------------------------------
# Sources / situations
# ---------------------------------------------------------------------------
# Source options the user picks on the start page (must match the web app
# constants.ts). "Music Store" and "Music Store - Selected" return the same
# in-game UI, so they share a scanning situation.
SOURCE_OPTIONS = ["Routine Cleanup", "Music Store", "Music Store - Selected"]
SOURCE = "Routine Cleanup"  # default

# Which UI layout each source maps to.
SITUATION_BY_SOURCE = {
    "Routine Cleanup": "routine_cleanup",
    "Music Store": "music_store",
    "Music Store - Selected": "music_store",
}


def get_situation(source: str) -> str:
    return SITUATION_BY_SOURCE.get(source, "routine_cleanup")


# ===========================================================================
# Situation 1: ROUTINE CLEANUP
# ===========================================================================
# Challenge Results screen. A grid of reward discs sits on the right. Only the
# S-rarity discs (gold bar under the thumbnail) are scanned; A-rarity (purple
# bar) are ignored. Clicking a disc opens a centered detail popup, which we
# OCR, then dismiss before clicking the next.
#
# NOTE: all pixel values are first-pass estimates from the 2560x1440 reference
# screenshots and should be fine-tuned with a live run (find_coords.py /
# visualize_region.py).

# Where to look for the disc grid (and their gold rarity bars).
RC_GRID_REGION = {
    "left": 1742,
    "top": 655,
    "width": 703,
    "height": 420,
}

# The detail popup's text area (title + main stat + sub-stats), to OCR.
RC_POPUP_REGION = {
    "left": 790,
    "top": 284,
    "width": 977,
    "height": 704,
}

# A safe empty spot to click to dismiss the open detail popup.
RC_DISMISS_POINT = (2300, 720)

# Each S disc is found by its gold rarity bar; click this far ABOVE the bar's
# center to land on the disc thumbnail itself.
RC_CARD_CLICK_Y_OFFSET = -65

# HSV range (OpenCV: H 0-179) for the S-rarity bar. The bar is a flat pure
# gold — RGB (255,181,0) == HSV (21,255,255) — so we keep a tight band around
# it. This isolates the bar from the duller gold of disc artwork, which would
# otherwise merge into one oversized blob.
RC_BAR_HSV_LOWER = (17, 180, 180)
RC_BAR_HSV_UPPER = (25, 255, 255)

# Size filtering for the detected gold bars (px at 2560x1440).
RC_BAR_MIN_WIDTH = 80    # real bars ~125px; A-rank artwork blobs ~61px
RC_BAR_MAX_WIDTH = 300
RC_BAR_MIN_HEIGHT = 6
RC_BAR_MAX_HEIGHT = 90
RC_BAR_MIN_ASPECT = 1.6  # bar w/h is high; square artwork blobs ~1.1
RC_ROW_TOLERANCE = 60    # px: bars within this Y range count as the same row


# ===========================================================================
# Situation 2: MUSIC STORE  (and "Music Store - Selected")
# ===========================================================================
# Tuning Results screen. A fixed 2x5 grid of exactly 10 S-rarity discs, with a
# persistent detail panel on the LEFT. The selected disc (animated border) is
# the one shown on the left. We simply click each grid cell in order and OCR
# the left panel after each click — no popup to dismiss.

# Detail panel on the left (title + main stat + sub-stats), to OCR.
MS_PANEL_REGION = {
    "left": 790,
    "top": 244,
    "width": 410,
    "height": 706,
}

# Fixed grid of 10 disc centers (2 rows x 5 columns), in reading order.
_MS_COLS_X = [1408, 1631, 1853, 2076, 2299]
_MS_ROWS_Y = [567, 851]
MS_GRID_POINTS = [(x, y) for y in _MS_ROWS_Y for x in _MS_COLS_X]


# ---------------------------------------------------------------------------
# Timing / automation
# ---------------------------------------------------------------------------
MOUSE_MOVE_DURATION = 0.15   # seconds for the cursor to glide to a target
CLICK_WAIT = 0.5             # wait after clicking a disc for details to render
DISMISS_WAIT = 0.3           # wait after dismissing before the next click
START_DELAY = 3.0            # countdown after launch to switch to the game


# ---------------------------------------------------------------------------
# Web-app vocabulary (must match zzz-t3/src/lib/constants.ts)
# ---------------------------------------------------------------------------

# Drive disc slots (the web app's "type" field).
SLOTS = ["1", "2", "3", "4", "5", "6"]

# Valid main stats per slot. Slots 1-3 are fixed; 4-6 vary.
MAIN_STATS_BY_SLOT = {
    "1": ["HP"],
    "2": ["ATK"],
    "3": ["DEF"],
    "4": ["%HP", "%ATK", "%DEF", "Crit Rate", "Crit DMG", "AP"],
    "5": ["%HP", "%ATK", "%DEF", "PEN Ratio",
          "Physical", "Electric", "Ether", "Fire", "Ice", "Wind"],
    "6": ["%HP", "%ATK", "%DEF", "AM", "Impact", "ER"],
}

# All possible substats (the web app's checkbox vocabulary).
ALL_SUBSTATS = [
    "HP", "%HP", "ATK", "%ATK", "DEF", "%DEF",
    "PEN", "AP", "Crit Rate", "Crit DMG",
]

# Scores matching the web app (constants.ts)
SCORES = [
    "Complete trash",
    "Trash",
    "Usable",
    "Good",
    "Excellent",
    "Marvelous",
    "Unknown",
]

# Drive disc sets (constants.ts)
ARTIFACT_SETS = [
    "Astral Voice",
    "Branch & Blade Song",
    "Chaos Jazz",
    "Chaotic Metal",
    "Fanged Metal",
    "Freedom Blues",
    "Hormone Punk",
    "Inferno Metal",
    "Polar Metal",
    "Proto Punk",
    "Puffer Electro",
    "Shockstar Disco",
    "Soul Rock",
    "Swing Jazz",
    "Thunder Metal",
    "Woodpecker Electro",
    "Shadow Harmony",
    "Phaethon's Melody",
    "King of the Summit",
    "Yunkui Tales",
    "Moonlight Lullaby",
    "Dawn's Bloom",
    "White Water Ballad",
    "Shining Aria",
    "Bunny in Wonderland",
    "Notes From the Chained",
    "Wuthering Salon",
    "The Sky Ablaze",
]
