"""
Live mouse coordinate tracker.

Run this, switch to Genshin, hover over the corners of the artifact popup.
Read the x,y values and fill in POPUP_REGION in config.py.

    top-left corner  → gives you  left, top
    bottom-right corner → gives you  left+width, top+height

Press Ctrl+C to stop.
"""
import time
import pyautogui

print("Starting in 3 seconds — switch to Genshin now...")
time.sleep(3)
print("Move mouse to popup corners. Press Ctrl+C when done.\n")
print(f"{'X':>6}  {'Y':>6}")
print("-" * 16)

try:
    while True:
        x, y = pyautogui.position()
        print(f"\r{x:>6}  {y:>6}", end="", flush=True)
        time.sleep(0.1)
except KeyboardInterrupt:
    print(f"\n\nLast position: x={x}, y={y}")
    print("\nOnce you have both corners:")
    print("  POPUP_REGION = {")
    print("    'left':   <top-left x>,")
    print("    'top':    <top-left y>,")
    print("    'width':  <bottom-right x> - <top-left x>,")
    print("    'height': <bottom-right y> - <top-left y>,")
    print("  }")
