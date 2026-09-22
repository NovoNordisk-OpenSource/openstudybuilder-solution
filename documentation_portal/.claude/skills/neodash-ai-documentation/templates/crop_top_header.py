#!/usr/bin/env python3
"""Crop the NeoDash top header bar (logo + live DB connection string) off a
screenshot (pure stdlib). Detects the thin solid-grey divider rule NeoDash
renders directly under the header and crops everything at/above it.

Usage: crop_top_header.py FILE1.png FILE2.png ...
Edits files in place. Skips (and reports) any file where no divider is found
in the first 150 rows, rather than guessing.
"""
import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from pngcrop import read_png, write_png


def find_divider(w, h, nch, pix, search_rows=150, tol=4):
    stride = w * nch
    target = 211
    for y in range(10, min(search_rows, h)):
        row = pix[y * stride:(y + 1) * stride]
        hits = 0
        samples = range(0, w, max(1, w // 100))
        for x in samples:
            base = x * nch
            if all(abs(row[base + c] - target) <= tol for c in range(3)):
                hits += 1
        if hits / len(list(samples)) > 0.8:
            return y
    return None


def main():
    for f in sys.argv[1:]:
        w, h, nch, color, pix = read_png(f)
        y = find_divider(w, h, nch, pix)
        if y is None:
            print(f"SKIP (no divider found): {f}")
            continue
        stride = w * nch
        new_h = h - (y + 1)
        cropped = pix[(y + 1) * stride:]
        write_png(f, w, new_h, nch, color, cropped)
        print(f"{f}: {w}x{h} -> {w}x{new_h} (cropped top {y + 1}px)")


if __name__ == "__main__":
    main()
