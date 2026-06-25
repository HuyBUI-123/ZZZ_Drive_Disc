"""
CLI test tool for the OCR pipeline (image -> OCR -> parsed result).

Pick the region with --rc (Routine Cleanup popup) or --ms (Music Store panel).
If neither is given, it's guessed from the filename.

Usage:
  # Image already cropped to just the detail view:
  python test_ocr.py sample_images/detail_popup_1.png

  # Full game screenshot — auto-crop using the situation's region:
  python test_ocr.py sample_images/routine_cleanup_obtain_1.png --rc --crop
  python test_ocr.py sample_images/MusicStore_1.png --ms --crop

  # Save the cropped region so you can visually verify alignment:
  python test_ocr.py sample_images/MusicStore_1.png --ms --crop --save-crop
"""
import sys
import json
from PIL import Image

import config
from ocr import run_ocr, extract_from_image


def _pick_region(args, path):
    if "--ms" in args:
        return config.MS_PANEL_REGION, "music_store"
    if "--rc" in args:
        return config.RC_POPUP_REGION, "routine_cleanup"
    # Guess from filename
    low = path.lower()
    if "music" in low:
        return config.MS_PANEL_REGION, "music_store"
    return config.RC_POPUP_REGION, "routine_cleanup"


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    image_path = args[0]
    do_crop = "--crop" in args
    save_crop = "--save-crop" in args

    img = Image.open(image_path).convert("RGB")
    region, situation = _pick_region(args, image_path)

    if do_crop:
        r = region
        box = (r["left"], r["top"], r["left"] + r["width"], r["top"] + r["height"])
        img = img.crop(box)
        print(f"[{situation}] Cropped to {box}  ({img.width}x{img.height}px)")
        if save_crop:
            out = "debug_crop.png"
            img.save(out)
            print(f"Saved crop -> {out}  (open this to verify alignment)")

    print("\n" + "=" * 50)
    print("RAW OCR OUTPUT")
    print("=" * 50)
    raw = run_ocr(img)
    print(raw)

    print("\n" + "=" * 50)
    print("PARSED RESULT")
    print("=" * 50)
    data, _ = extract_from_image(img)
    clean = {k: v for k, v in data.items() if not k.startswith("_")}
    print(json.dumps(clean, indent=2))

    print("\n" + "=" * 50)
    print("CONFIDENCE")
    print("=" * 50)
    all_ok = True
    for field, ok in data["_ok"].items():
        status = "OK " if ok else "FAIL"
        print(f"  [{status}] {field}")
        if not ok:
            all_ok = False

    if not all_ok:
        print("\nSome fields failed. Check RAW OCR OUTPUT above.")
        print("If alignment looks wrong, adjust the region in config.py and re-run with --crop --save-crop.")
    print()


if __name__ == "__main__":
    main()
