# match_font_version.py
import json, os

fonts_dir = r"C:\Users\User\Documents\GitHub\Final-Year-Project\.venv\Lib\site-packages\qtawesome\fonts"

v5 = json.load(open(os.path.join(fonts_dir, "materialdesignicons5-webfont-charmap-5.9.55.json")))
v6 = json.load(open(os.path.join(fonts_dir, "materialdesignicons6-webfont-charmap-6.9.96.json")))

test_codepoints = [
    0xF056E, 0xF06BD, 0xF0029, 0xF039B, 0xF0335,
    0xF0341, 0xF0026, 0xF1009, 0xF00BA, 0xF08BB,
]

for cp in test_codepoints:
    hexcode = f"0x{cp:x}"   # now matches the '0x...' format used in the charmap
    in_v5 = hexcode in v5.values()
    in_v6 = hexcode in v6.values()
    print(f"U+{cp:05X}: v5={in_v5}  v6={in_v6}")
    