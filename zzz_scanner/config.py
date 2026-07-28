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
SOURCE_OPTIONS = [
    "Routine Cleanup",
    "Routine Cleanup - Battery",
    "Music Store",
    "Music Store - Selected",
]
SOURCE = "Routine Cleanup"  # default

# Which UI layout each source maps to.
SITUATION_BY_SOURCE = {
    "Routine Cleanup": "routine_cleanup",
    "Routine Cleanup - Battery": "battery",
    "Music Store": "music_store",
    "Music Store - Selected": "music_store",
}

# Some UI sources are written to the export under a canonical name.
EXPORT_SOURCE = {
    "Routine Cleanup - Battery": "Routine Cleanup",
}


def get_situation(source: str) -> str:
    return SITUATION_BY_SOURCE.get(source, "routine_cleanup")


def get_export_source(source: str) -> str:
    """The source string written to the JSON export."""
    return EXPORT_SOURCE.get(source, source)


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


# ===========================================================================
# Situation 3: ROUTINE CLEANUP - BATTERY  (the "Obtain" screen)
# ===========================================================================
# Battery farming opens the "Obtain" dialog: a 6-column grid of rewards (EXP,
# drive discs, materials) with a persistent DETAIL panel on the right. Only the
# gold-bar S discs matter. The layout is fixed per battery count, so we define
# a scan PLAN per count: a list of scroll STEPS, each listing the disc-row Y
# centers to check at that scroll position. At every listed (column, row) we
# check the bar below for the gold colour (reusing RC_S_BAR_*); matches get
# clicked and the DETAIL panel OCR'd. Steps after the first are reached by
# scrolling down RC_BATTERY_SCROLL_AMOUNT.
#
# NOTE: the coords below are first-pass estimates — tune them against the
# RoutineCleanupBattery_* and RoutineCleanup_*Batteries_*_scroll.png samples
# with visualize_battery.py.

# The right DETAIL panel (title + main stat + sub-stats), to OCR.
BATTERY_PANEL_REGION = {
    "left": 1460,
    "top": 470,
    "width": 560,
    "height": 560,
}

# The 6 column centers of the reward grid (x, px at 2560x1440).
BATTERY_COLS_X = [602, 749, 896, 1043, 1190, 1337]

# Bar-check geometry for the (smaller) obtain-grid discs.
RC_BATTERY_BAR_CHECK_OFFSET = 50   # px below a disc center to its rarity bar
RC_BATTERY_BAR_SAMPLE_W = 34
RC_BATTERY_BAR_SAMPLE_H = 10

# Scrolling: hover here, then scroll this many wheel "clicks" per single scroll
# unit (negative = down). Calibrate one unit against the reference screenshots.
RC_BATTERY_SCROLL_POINT = (760, 640)
RC_BATTERY_SCROLL_AMOUNT = -3

# Scan PLAN per battery count. Each step is (scrolls_to_do_first, [row Y centers
# to check]). Scrolls are cumulative down the list (0, then +2, then +2 = 4
# total). Each step is tuned against the matching *_scroll.png screenshot so it
# scans a section's disc rows exactly once — no re-scanning across steps.
RC_BATTERY_PLANS = {
    # 1 & 2 batteries: all S discs visible without scrolling.
    1: [(0, [560])],
    2: [(0, [560, 980])],
    # 3 batteries: step 0 covers sections "1"+"2"; +2 scrolls covers "3".
    3: [
        (0, [560, 980]),   # -> RoutineCleanup_3Batteries_0_scroll.png
        (2, [927]),         # -> RoutineCleanup_3Batteries_2_scroll.png
    ],
    # 4 batteries: +2 scrolls per further section ("3", then "4").
    4: [
        (0, [560, 980]),   # -> RoutineCleanup_4Batteries_0_scroll.png
        (2, [927]),         # -> RoutineCleanup_4Batteries_2_scroll.png
        (2, [870]),         # -> RoutineCleanup_4Batteries_4_scroll.png
    ],
}


# ---------------------------------------------------------------------------
# Timing / automation
# ---------------------------------------------------------------------------
MOUSE_MOVE_DURATION = 0.15   # seconds for the cursor to glide to a target
CLICK_WAIT = 0.2             # wait after clicking a disc for details to render
DISMISS_WAIT = 0.2           # wait after dismissing before the next click
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
    "Feathered Fate",
    "Thorned Rose",
]
