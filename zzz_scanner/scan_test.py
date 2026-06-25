"""
Live end-to-end test of the click + OCR loop (no UI yet).

Open ZZZ to the relevant screen, run this, then switch to the game during the
countdown. It clicks through each disc, OCRs the detail view, and dumps the
results to scan_output.json.

Pick the source/situation with --routine (default) or --music.

SAFETY: slam the mouse into any screen corner to abort instantly
(pyautogui failsafe).

Usage:
  python scan_test.py --routine
  python scan_test.py --music
"""
import sys
import json
import time

import config
from automation import scan_all


def on_progress(done, total, data):
    name = f"{data.get('set')} / slot {data.get('type')}"
    ms = data.get("mainStat")
    subs = ", ".join(data.get("substats") or [])
    flags = "" if all(data["_ok"].values()) else "  <-- CHECK (low confidence)"
    print(f"[{done}/{total}] {name} | main={ms} | subs=[{subs}]{flags}")


def main():
    args = sys.argv[1:]
    if "--music" in args:
        source = "Music Store"
    elif "--routine" in args:
        source = "Routine Cleanup"
    else:
        source = config.get_source()

    print(f"Source: {source}  (situation: {config.get_situation(source)})")
    print(f"Switch to ZZZ now — starting in {config.START_DELAY:.0f}s...")
    print("(Move mouse to a screen corner at any time to abort.)\n")
    time.sleep(config.START_DELAY)

    results = scan_all(source, progress_cb=on_progress)

    # Strip debug fields for the clean export
    clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in results]

    out = "scan_output.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2, ensure_ascii=False)

    print(f"\nDone. {len(clean)} disc(s) scanned -> {out}")

    weak = [i for i, r in enumerate(results, 1) if not all(r["_ok"].values())]
    if weak:
        print(f"Low-confidence indices (review these): {weak}")


if __name__ == "__main__":
    main()
