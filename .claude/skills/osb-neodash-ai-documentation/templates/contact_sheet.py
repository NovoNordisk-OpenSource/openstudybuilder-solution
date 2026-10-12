#!/usr/bin/env python3
"""Build a labeled contact sheet of the top strip of many PNGs (pure stdlib).

Usage: contact_sheet.py OUT.png STRIP_H WIDTH FILE1 FILE2 ...
Stacks the top STRIP_H rows (padded/cropped to WIDTH, converted to RGB) of
each input PNG, separated by a thin black rule, so many screenshots' headers
can be reviewed in one image.
"""
import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from pngcrop import read_png, write_png


def to_rgb_row(pix, nch, w, x0, x1):
    row = bytearray()
    for x in range(x0, x1):
        if x < w:
            base = x * nch
            r, g, b = pix[base], pix[base + 1 if nch > 1 else base], pix[base + 2 if nch > 2 else base]
            if nch == 1:
                r = g = b = pix[base]
            elif nch == 2:
                r = g = b = pix[base]
            row += bytes((r, g, b))
        else:
            row += bytes((255, 255, 255))
    return row


def main():
    out, strip_h, width = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    files = sys.argv[4:]
    rule = 4
    sheet_rows = []
    for f in files:
        w, h, nch, color, pix = read_png(f)
        stride = w * nch
        for y in range(min(strip_h, h)):
            row = pix[y * stride:(y + 1) * stride]
            sheet_rows.append(to_rgb_row(row, nch, w, 0, width))
        for _ in range(rule):
            sheet_rows.append(bytes((255, 0, 0)) * width)
    total_h = len(sheet_rows)
    flat = bytearray()
    for r in sheet_rows:
        flat += r
    write_png(out, width, total_h, 3, 2, flat)
    print(f"{out}: {width}x{total_h} from {len(files)} files")
    for i, f in enumerate(files):
        print(f"  strip {i}: y={i * (strip_h + rule)} {f}")


if __name__ == "__main__":
    main()
