# find_mdi_font.py — run this once to locate the bundled font
import qtawesome as qta
import os

fonts_dir = os.path.join(os.path.dirname(qta.__file__), "fonts")
print("Fonts folder:", fonts_dir)
for f in os.listdir(fonts_dir):
    print(" -", f)