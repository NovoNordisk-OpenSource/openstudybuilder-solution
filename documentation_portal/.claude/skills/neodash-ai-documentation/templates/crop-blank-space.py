#!/usr/bin/env python3
"""Crop blank space from NeoDash capture screenshots (top band + trailing band).

The full-height capture technique (CSS-expand the inner scroll container, then
fullPage) grows the document past the actual content, so every shot ends with a
tall band of empty dashboard background — plus a stray sidebar-toggle icon at the
far bottom-left that defeats a naive uniform-background trim.

For some reports the same expansion ALSO opens a tall band of empty background
*above* the report title (it is normally scrolled out of view, so it never shows
on a real screen — only in the full-page capture). The Audit Trail Report shows
~370px of it; the Activity Library Dashboard only ~30px (a normal gap).

Strategy:
  * TOP — find the app bar (the non-background block at the very top), then the
    leading background band beneath it. If that band is abnormally tall
    (> --top-threshold) collapse it to --top-margin px, keeping the app bar and
    the content. A normal small gap is left alone, so this is a no-op on shots
    that don't have the pathological band.
  * BOTTOM — for each `annotated-*.png` find the bottom-most red call-out pixel
    (the annotation colour #e01e28) and crop just below it. The matching clean
    sidecar (no red to detect) is trimmed to the SAME geometry as its annotated
    twin so the pair stays pixel-aligned. A clean image with no annotated twin (a
    bare overview shot) falls back to trimming trailing rows that match the
    background, ignoring the leftmost column so the sidebar icon doesn't keep the
    blank space alive.

Usage:
    python3 crop-blank-space.py <assets-dir> [--margin N] [--top-margin N]
                                             [--top-threshold N] [--dry-run]

Idempotent: re-running on already-cropped images is a no-op (nothing left to cut).
Requires Pillow (PIL).
"""
import argparse
import glob
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit(
        "Pillow (PIL) is required: pip install Pillow\n"
        "\n"
        "If pip is unavailable (some WSL/system Pythons ship without pip or\n"
        "ensurepip), use the stdlib-only fallback in this same directory:\n"
        "    python3 pngcrop.py <src.png> <dst.png> [margin]\n"
        "It crops one file at a time and has no dependencies, but it does not\n"
        "do red-call-out detection or annotated/clean pairing — check the\n"
        "result before publishing."
    )

# Annotation red is #e01e28; match generously to catch anti-aliased edges.
def _is_red(px):
    r, g, b = px[0], px[1], px[2]
    return r > 170 and g < 90 and b < 100


def _has_dark(px, w, y, dark=120, step=6, need=2):
    """True if row y holds at least `need` near-black pixels (text/borders).

    The empty dashboard background — top band, trailing band, gutters — has none;
    every content row (titles, card headers, tables) has plenty. This is more
    robust than matching the backdrop colour, which the white outer page margins
    would defeat."""
    c = 0
    for x in range(0, w, step):
        p = px[x, y]
        if p[0] < dark and p[1] < dark and p[2] < dark:
            c += 1
            if c >= need:
                return True
    return False


def _last_red_row(im):
    """Bottom-most row that contains the annotation red, or None if none."""
    w, h = im.size
    px = im.load()
    for y in range(h - 1, -1, -1):
        cnt = 0
        for x in range(0, w, 6):  # sample every 6px for speed
            if _is_red(px[x, y]):
                cnt += 1
                if cnt >= 3:  # need a few to avoid stray JPEG-ish noise
                    return y
    return None


def _last_dark_row(im):
    """Fallback for un-annotated shots: bottom-most row that holds content
    (near-black text/borders), below which is only blank background."""
    w, h = im.size
    px = im.load()
    for y in range(h - 1, -1, -1):
        if _has_dark(px, w, y):
            return y
    return None


def _top_geometry(im, top_margin, top_threshold, window=12):
    """Locate the leading empty background band beneath the app bar.

    Layout top-to-bottom: app bar (logo/text — has dark pixels), then an empty
    background band (no dark pixels), then the report content (title/tabs — dark
    again). Returns (keep_top, content_start):
      * if the band is taller than `top_threshold`, keep_top = appbar_end +
        top_margin so the app bar plus a small gap survives and the rest of the
        band is dropped;
      * otherwise keep_top = content_start (a normal small gap; no top trim).
    """
    w, h = im.size
    px = im.load()

    def dark(y):
        return _has_dark(px, w, y)

    # first dark row = top of the app-bar content
    first_dark = next((y for y in range(h) if dark(y)), None)
    if first_dark is None:
        return 0, 0  # nothing recognisable — leave it alone

    # end of app bar = first row after which `window` rows are all dark-free
    appbar_end = None
    y = first_dark
    while y < h:
        if not dark(y) and all(not dark(yy) for yy in range(y, min(h, y + window))):
            appbar_end = y
            break
        y += 1
    if appbar_end is None:
        return 0, 0

    # content starts at the next dark row (the report title)
    cs = appbar_end
    while cs < h and not dark(cs):
        cs += 1
    if cs >= h:
        return appbar_end, appbar_end

    band_h = cs - appbar_end
    if band_h > top_threshold:
        return appbar_end + top_margin, cs
    return cs, cs  # normal gap: no top trim


def _apply(path, keep_top, content_start, bottom_end, dry_run):
    """Keep rows [0,keep_top) then [content_start,bottom_end); stack them."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    bottom_end = min(h, bottom_end)
    top_trim = content_start - keep_top  # rows removed above content
    if top_trim <= 0 and bottom_end >= h:
        return False  # nothing to do
    body_h = bottom_end - content_start
    out = Image.new("RGB", (w, keep_top + body_h))
    out.paste(im.crop((0, 0, w, keep_top)), (0, 0))
    out.paste(im.crop((0, content_start, w, bottom_end)), (0, keep_top))
    if not dry_run:
        out.save(path)
    print(f"  {os.path.basename(path)}: {w}x{h} -> {w}x{out.size[1]}"
          f"{' (top -%d)' % top_trim if top_trim > 0 else ''}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("assets_dir")
    ap.add_argument("--margin", type=int, default=24,
                    help="px kept below the last call-out box (default 24)")
    ap.add_argument("--top-margin", type=int, default=40,
                    help="px kept below the app-bar content when an abnormal top "
                         "band is collapsed (default 40 — app bar + a small gap)")
    ap.add_argument("--top-threshold", type=int, default=120,
                    help="only collapse a top band taller than this (default "
                         "120; a normal ~30px gap is left untouched)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    annotated = sorted(glob.glob(os.path.join(args.assets_dir, "annotated-*.png")))
    cropped_clean = set()  # sidecars handled via their annotated twin

    print(f"Cropping captures in {args.assets_dir} "
          f"(margin={args.margin}, top-margin={args.top_margin}, "
          f"top-threshold={args.top_threshold})")
    for f in annotated:
        im = Image.open(f).convert("RGB")
        keep_top, content_start = _top_geometry(im, args.top_margin, args.top_threshold)
        lr = _last_red_row(im)
        if lr is None:
            print(f"  {os.path.basename(f)}: no red call-out found, skipped")
            continue
        bottom_end = lr + args.margin
        _apply(f, keep_top, content_start, bottom_end, args.dry_run)
        clean = f.replace("annotated-", "", 1)
        if os.path.exists(clean):
            # same geometry as the annotated twin keeps the pair aligned
            _apply(clean, keep_top, content_start, bottom_end, args.dry_run)
            cropped_clean.add(clean)

    # bare clean shots with no annotated twin
    for f in sorted(glob.glob(os.path.join(args.assets_dir, "*.png"))):
        if os.path.basename(f).startswith("annotated-") or f in cropped_clean:
            continue
        im = Image.open(f).convert("RGB")
        keep_top, content_start = _top_geometry(im, args.top_margin, args.top_threshold)
        lc = _last_dark_row(im)
        bottom_end = (lc + args.margin) if lc is not None else im.size[1]
        _apply(f, keep_top, content_start, bottom_end, args.dry_run)

    print("Done. Re-copy any cropped annotated images into docs/images/ if already synced.")


if __name__ == "__main__":
    main()
