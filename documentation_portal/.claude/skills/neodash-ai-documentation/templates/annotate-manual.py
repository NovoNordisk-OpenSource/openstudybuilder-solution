#!/usr/bin/env python3
"""Draw the skill's red call-out boxes on a *manual* screenshot (no browser/DOM).

The live-capture path annotates via DOM/SVG injection (templates/annotation-snippet.js),
reading each target's bounding box from the running NeoDash page. When Playwright/Node
is not available and screenshots are taken by hand, there is no DOM to measure — so this
module reproduces the SAME visual style (red #e01e28, 3px box, optional arrow + white
label chip + numbered badge) from explicit pixel coordinates instead.

Coordinates are plain image pixels (origin = top-left). A box is {x, y, w, h}; optional
keys: label (text chip), number (badge), arrow ("auto" or {x, y} origin point).

Two ways to use it
------------------
1. Spec file (recommended — one JSON per screenshot, easy to tweak & re-run):

     python annotate-manual.py spec.json

   spec.json:
     {
       "input":  "neodash-docs/<report>/assets/<report>-<tab>-NN-<slug>.png",
       "output": "neodash-docs/<report>/assets/annotated-<report>-<tab>-NN-<slug>.png",
       "boxes": [
         {"x": 24,  "y": 60,  "w": 380, "h": 220, "number": 1, "label": "A"},
         {"x": 430, "y": 60,  "w": 300, "h": 120, "number": 2, "label": "B", "arrow": "auto"}
       ]
     }

   Batch: pass several spec files, or a directory to process every *.json inside it.
   If "output" is omitted it defaults to annotated-<input name> in the same folder.

2. Import and call directly:

     from annotate_manual import annotate
     annotate("clean.png", "annotated.png", [
         {"x": 24, "y": 60, "w": 380, "h": 220, "label": "A", "number": 1},
     ])

Idempotent per run: it always redraws from the clean input, so re-running just
regenerates the annotated output.

Requires Pillow (PIL):  pip install Pillow
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    sys.exit("Pillow (PIL) is required: pip install Pillow")

# Match annotation-snippet.js exactly so manual and live shots look identical.
RED = (224, 30, 40)      # #e01e28
WHITE = (255, 255, 255)
BOX_STROKE = 3
ARROW_STROKE = 3
BADGE_R = 13
LABEL_FS = 15
BADGE_FS = 14


def _font(size: int):
    """A bold sans font if the platform has one, else Pillow's default bitmap font."""
    for name in ("arialbd.ttf", "Arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf",
                 "segoeuib.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text_size(draw: "ImageDraw.ImageDraw", text: str, font) -> tuple[int, int]:
    try:
        l, t, r, b = draw.textbbox((0, 0), text, font=font)
        return r - l, b - t
    except AttributeError:  # very old Pillow
        return draw.textsize(text, font=font)


def _draw_arrowhead(draw, x1, y1, x2, y2, color, size=10):
    """Filled triangular head at (x2, y2) pointing along the (x1,y1)->(x2,y2) line."""
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    for da in (math.radians(150), math.radians(-150)):
        draw.line(
            [(x2, y2), (x2 + size * math.cos(ang + da), y2 + size * math.sin(ang + da))],
            fill=color, width=ARROW_STROKE,
        )


def annotate(input_path: str, output_path: str, boxes: list[dict]) -> str:
    """Render red call-outs onto a copy of input_path and save to output_path."""
    im = Image.open(input_path).convert("RGBA")
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    label_font = _font(LABEL_FS)
    badge_font = _font(BADGE_FS)

    for spec in boxes:
        x, y = int(spec["x"]), int(spec["y"])
        w, h = int(spec["w"]), int(spec["h"])

        # red box (outset 3px like the JS: x-3, y-3, w+6, h+6)
        draw.rectangle(
            [x - 3, y - 3, x + w + 3, y + h + 3],
            outline=RED, width=BOX_STROKE,
        )

        # arrow (+ optional label chip at its origin)
        arrow = spec.get("arrow")
        if arrow:
            if arrow in ("auto", True):
                ox, oy = max(12, x - 140), max(12, y - 60)
            else:
                ox, oy = int(arrow["x"]), int(arrow["y"])
            tx, ty = x, y
            draw.line([(ox, oy), (tx, ty)], fill=RED, width=ARROW_STROKE)
            _draw_arrowhead(draw, ox, oy, tx, ty, RED)

            label = spec.get("label")
            if label:
                tw, th = _text_size(draw, label, label_font)
                pad_x, box_h = 8, LABEL_FS + 12
                box_w = tw + pad_x * 2
                lx = max(2, ox - box_w)
                ly = max(2, oy - box_h // 2)
                draw.rectangle([lx, ly, lx + box_w, ly + box_h],
                               fill=WHITE, outline=RED, width=2)
                draw.text((lx + pad_x, ly + (box_h - th) // 2), label,
                          fill=RED, font=label_font)
        elif spec.get("label") and spec.get("number") is None:
            # label without an arrow: chip just above the box's top-left
            label = spec["label"]
            tw, th = _text_size(draw, label, label_font)
            pad_x, box_h = 8, LABEL_FS + 12
            box_w = tw + pad_x * 2
            lx, ly = x - 3, max(2, y - 3 - box_h - 4)
            draw.rectangle([lx, ly, lx + box_w, ly + box_h],
                           fill=WHITE, outline=RED, width=2)
            draw.text((lx + pad_x, ly + (box_h - th) // 2), label,
                      fill=RED, font=label_font)

        # numbered badge at the box top-left corner
        number = spec.get("number")
        if number is not None:
            cx, cy = x - 3, y - 3
            draw.ellipse([cx - BADGE_R, cy - BADGE_R, cx + BADGE_R, cy + BADGE_R],
                         fill=RED)
            label = str(number)
            tw, th = _text_size(draw, label, badge_font)
            draw.text((cx - tw / 2, cy - th / 2), label, fill=WHITE, font=badge_font)

    out = Image.alpha_composite(im, overlay).convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    out.save(output_path)
    return output_path


def _default_output(input_path: str) -> str:
    d, base = os.path.split(input_path)
    return os.path.join(d, base if base.startswith("annotated-") else "annotated-" + base)


def _run_spec(spec_path: str) -> str:
    with open(spec_path, "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    root = os.path.dirname(os.path.abspath(spec_path))

    def resolve(p: str) -> str:
        return p if os.path.isabs(p) else os.path.normpath(os.path.join(root, p))

    inp = resolve(spec["input"])
    out = resolve(spec["output"]) if spec.get("output") else _default_output(inp)
    annotate(inp, out, spec.get("boxes", []))
    return out


def _expand(paths: list[str]) -> list[str]:
    specs: list[str] = []
    for p in paths:
        if os.path.isdir(p):
            specs.extend(sorted(glob.glob(os.path.join(p, "*.json"))))
        else:
            specs.append(p)
    return specs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Draw red call-out boxes on manual screenshots.")
    ap.add_argument("specs", nargs="+",
                    help="One or more spec JSON files, or a directory of *.json specs.")
    args = ap.parse_args(argv)

    specs = _expand(args.specs)
    if not specs:
        sys.exit("No spec files found.")
    for s in specs:
        out = _run_spec(s)
        print(f"annotated -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
