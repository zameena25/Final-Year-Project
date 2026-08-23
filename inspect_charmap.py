# inspect_charmap.py
import json, os

fonts_dir = r"C:\Users\User\Documents\GitHub\Final-Year-Project\.venv\Lib\site-packages\qtawesome\fonts"

v5 = json.load(open(os.path.join(fonts_dir, "materialdesignicons5-webfont-charmap-5.9.55.json")))

# Print the first 5 entries so we can see the actual key/value format
for i, (k, v) in enumerate(v5.items()):
    print(repr(k), "->", repr(v))
    if i >= 5:
        break

print("Total icons in v5:", len(v5))