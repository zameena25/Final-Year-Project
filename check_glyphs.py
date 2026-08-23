# check_glyphs.py
glyphs = ["󰒘", "󰕮", "󰚽", "󰀩", "󰎛", "󰌵", "󰍁", "󰀦", "󱀉", "󰂺", "󰢻"]
for g in glyphs:
    print(f"{g!r} -> U+{ord(g):04X}")