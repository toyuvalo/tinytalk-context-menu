"""
Generate icon.ico for TinyTalk.
Design: dark rounded-square background, teal speech bubble, dark waveform bars inside.
Run: python make_icon.py
"""
from PIL import Image, ImageDraw
import math, os

C_BG     = (9,   9,   9,  255)
C_ACCENT = (0,  217, 217, 255)
C_DARK   = (9,   9,   9,  255)

def _rounded_rect(draw, x0, y0, x1, y1, r, fill):
    """Draw a filled rounded rectangle (compatible with older Pillow)."""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    r = min(r, (x1 - x0) // 2, (y1 - y0) // 2)
    if r < 1:
        if x0 < x1 and y0 < y1:
            draw.rectangle([x0, y0, x1, y1], fill=fill)
        return
    if x0 + r <= x1 - r:
        draw.rectangle([x0 + r, y0,     x1 - r, y1    ], fill=fill)
    if y0 + r <= y1 - r:
        draw.rectangle([x0,     y0 + r, x1,     y1 - r], fill=fill)
    draw.ellipse  ([x0,     y0,     x0+r*2, y0+r*2], fill=fill)
    draw.ellipse  ([x1-r*2, y0,     x1,     y0+r*2], fill=fill)
    draw.ellipse  ([x0,     y1-r*2, x0+r*2, y1    ], fill=fill)
    draw.ellipse  ([x1-r*2, y1-r*2, x1,     y1    ], fill=fill)


def make_frame(size):
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s    = size

    # ── Background square ──────────────────────────────────────────────────
    bg_r = max(2, s // 7)
    _rounded_rect(draw, 0, 0, s - 1, s - 1, bg_r, C_BG)

    # ── Speech bubble ──────────────────────────────────────────────────────
    pad   = s * 0.13
    bx0   = pad
    by0   = pad
    bx1   = s - pad
    by1   = s * 0.62          # bottom of bubble body (leaves room for tail)
    br    = max(2, s // 9)
    _rounded_rect(draw, bx0, by0, bx1, by1, br, C_ACCENT)

    # Tail — small triangle pointing bottom-left
    bw   = bx1 - bx0
    tx   = bx0 + bw * 0.18    # tail x anchor
    ty   = by1                 # top of tail (bottom of bubble)
    tail = [
        (tx,            ty),
        (tx + bw * 0.18, ty),
        (tx - bw * 0.04, ty + s * 0.15),
    ]
    draw.polygon(tail, fill=C_ACCENT)

    # ── Waveform bars inside bubble ────────────────────────────────────────
    heights   = [0.30, 0.60, 1.00, 0.60, 0.30]
    n_bars    = len(heights)
    inner_x0  = bx0 + bw * 0.15
    inner_x1  = bx1 - bw * 0.15
    inner_w   = inner_x1 - inner_x0
    bar_gap   = inner_w / (n_bars * 2)          # gap = half bar-slot
    bar_w     = bar_gap                          # bar width = gap width
    cy        = (by0 + by1) / 2
    max_h     = (by1 - by0) * 0.36

    for i, h in enumerate(heights):
        bx   = inner_x0 + bar_gap + i * bar_gap * 2
        bh   = max_h * h
        barr = max(1, int(bar_w // 2))
        _rounded_rect(draw,
                      bx,          cy - bh,
                      bx + bar_w,  cy + bh,
                      barr, C_DARK)

    return img


def main():
    sizes   = [16, 24, 32, 48, 64, 128, 256]
    frames  = [make_frame(s) for s in sizes]
    out     = os.path.join(os.path.dirname(__file__), "icon.ico")
    frames[0].save(out, format="ICO",
                   sizes=[(s, s) for s in sizes],
                   append_images=frames[1:])
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
