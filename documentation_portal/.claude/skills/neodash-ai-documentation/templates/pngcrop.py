#!/usr/bin/env python3
"""Minimal pure-stdlib PNG reader/writer + content-bounds crop.

Handles non-interlaced 8-bit RGB/RGBA/grayscale PNGs, which is what
screen captures are. No external deps (no Pillow available here).
"""
import struct
import sys
import zlib


def read_png(path):
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos = 8
    idat = bytearray()
    ihdr = None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif ctype == b"IDAT":
            idat += body
        elif ctype == b"IEND":
            break
        pos += 12 + length
    w, h, depth, color, comp, filt, interlace = ihdr
    assert depth == 8, f"only 8-bit supported, got {depth}"
    assert interlace == 0, "interlaced PNG not supported"
    nch = {0: 1, 2: 3, 4: 2, 6: 4}[color]
    raw = zlib.decompress(bytes(idat))

    # Undo per-scanline filters.
    stride = w * nch
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        ft = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if ft == 1:
            for i in range(nch, stride):
                line[i] = (line[i] + line[i - nch]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                b = prev[i]
                c = prev[i - nch] if i >= nch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, nch, color, out


def write_png(path, w, h, nch, color, pix):
    stride = w * nch
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter type None
        raw += pix[y * stride:(y + 1) * stride]

    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, color, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    open(path, "wb").write(png)


def content_bottom(w, h, nch, pix, bg_tol=6):
    """Last row index that differs from the image's background colour."""
    stride = w * nch
    bg = pix[0:nch]  # top-left pixel is background
    for y in range(h - 1, -1, -1):
        row = pix[y * stride:(y + 1) * stride]
        for x in range(0, stride, nch):
            for c in range(min(3, nch)):
                if abs(row[x + c] - bg[c]) > bg_tol:
                    return y
    return 0


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    margin = int(sys.argv[3]) if len(sys.argv) > 3 else 24
    w, h, nch, color, pix = read_png(src)
    bottom = content_bottom(w, h, nch, pix)
    new_h = min(h, bottom + 1 + margin)
    stride = w * nch
    cropped = pix[0:new_h * stride]
    write_png(dst, w, new_h, nch, color, cropped)
    print(f"{src}: {w}x{h} -> {w}x{new_h} (content ends y={bottom}, margin={margin})")
