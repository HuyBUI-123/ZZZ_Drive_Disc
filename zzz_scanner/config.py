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
# Challenge Results screen. The 8 reward discs sit in a FIXED 2x4 grid (like
# Music Store) and mix S and A rarity. For each grid slot we sample the small
# rarity-bar area just below the disc: if it matches the exact gold S-rarity
# colour, that disc is S and gets clicked; otherwise it's skipped. Clicking a
# disc opens a centered detail popup, which we OCR, then dismiss before the
# next click.

# The detail popup's text area (title + main stat + sub-stats), to OCR.
RC_POPUP_REGION = {
    "left": 790,
    "top": 284,
    "width": 977,
    "height": 704,
}

# A safe empty spot to click to dismiss the open detail popup.
RC_DISMISS_POINT = (2300, 720)

# Fixed 2x4 grid of the 8 shown disc centers (click points), in reading order.
_RC_COLS_X = [1846, 2012, 2179, 2345]
_RC_ROWS_Y = [745, 957]
RC_GRID_POINTS = [(x, y) for y in _RC_ROWS_Y for x in _RC_COLS_X]

# The rarity bar sits this far BELOW each disc center. We sample a small patch
# there (wide + thin, like the bar) and call the disc S-rarity if enough of the
# patch matches the gold bar colour below.
RC_BAR_CHECK_OFFSET = 58   # px below the click point to the bar's center
RC_BAR_SAMPLE_W = 40       # patch width  (bar is wide)
RC_BAR_SAMPLE_H = 10       # patch height (bar is thin)

# The exact S-rarity bar colour (RGB). Re-pick it with pick_color.py if it ever
# drifts. A disc counts as S when at least RC_S_BAR_MIN_FRACTION of the sampled
# patch is within RC_S_BAR_TOLERANCE (per RGB channel) of this colour.
RC_S_BAR_COLOR = (255, 181, 0)   # pure gold
RC_S_BAR_TOLERANCE = 45          # max per-channel difference to still count
RC_S_BAR_MIN_FRACTION = 0.25     # >= this fraction of the patch must match


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
