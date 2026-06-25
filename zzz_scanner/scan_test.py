"""
Live end-to-end test of the click + OCR loop (no UI yet).

Open Genshin to the strongbox "Obtained" screen, run this, then switch
to the game during the countdown. It will click through every detected
5-star artifact, OCR each popup, and dump the results to scan_output.json.

SAFETY: slam the mouse into any screen corner to abort instantly
(pyautogui failsafe).

Usage:
  python scan_test.py
"""
import json
import time

import config
from automation import scan_all


def on_progress(done, total, data):
    name = f"{data.get('set')} / {data.get('type')}"
    ms = data.get("mainStat")
    subs = ", ".join(data.get("substats") or [])
    un = data.get("unactivatedSubstat")
    flags = "" if all(data["_ok"].values()) else "  <-- CHECK (low confidence)"
    print(f"[{done}/{total}] {name} | main={ms} | subs=[{subs}]"
          f"{' | unact=' + un if un else ''}{flags}")


def main():
    print(f"Switch to Genshin now — starting in {config.START_DELAY:.0f}s...")
    print("(Move mouse to a screen corner at any time to abort.)\n")
    time.sleep(config.START_DELAY)

    results = scan_all(progress_cb=on_progress)

    # Strip debug fields for the clean export
    clean = []
    for r in results:
        clean.append({k: v for k, v in r.items() if not k.startswith("_")})

    out = "scan_output.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2)

    print(f"\nDone. {len(clean)} artifact(s) scanned -> {out}")

    # Summary of any low-confidence reads
    weak = [i for i, r in enumerate(results, 1) if not all(r["_ok"].values())]
    if weak:
        print(f"Low-confidence indices (review these): {weak}")


if __name__ == "__main__":
    main()
