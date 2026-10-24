"""Wavy pop-colour ribbons with text flowing along them (rendered as RGBA PNG frames).

Each ribbon is a long text band warped by a travelling sine wave, tilted, and
wiped in from the left / out to the right. Several ribbons stack into one layer.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "fonts", "LuckiestGuy-Regular.ttf")

PINK = ((255, 92, 160), (255, 246, 229), (196, 42, 110))      # band, text, edge
BUTTER = ((255, 222, 89), (43, 27, 20), (214, 166, 30))


def _sparkle(d, cx, cy, r, fill):
    pts = []
    for k in range(8):
        a = np.pi / 4 * k - np.pi / 2
        rr = r if k % 2 == 0 else r * 0.3
        pts.append((cx + rr * np.cos(a), cy + rr * np.sin(a)))
    d.polygon(pts, fill=fill)


def _strip(words, colors, bh):
    """One repeat unit of the band: TEXT ✦ TEXT ✦ ... on the band colour."""
    band, ink, edge = colors
    font = ImageFont.truetype(FONT, int(bh * 0.6))
    gap = int(bh * 0.55)
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    widths = [probe.textlength(w, font=font) for w in words]
    unit_w = int(sum(widths) + len(words) * gap * 2)
    im = Image.new("RGBA", (unit_w, bh), band + (255,))
    d = ImageDraw.Draw(im)
    x = gap
    for w, tw in zip(words, widths):
        d.text((x, bh * 0.53), w, font=font, fill=ink, anchor="lm")
        x += tw + gap
        _sparkle(d, x, bh / 2, bh * 0.2, ink)
        x += gap
    e = max(4, bh // 22)  # darker edge piping top & bottom
    d.rectangle([0, 0, unit_w, e], fill=edge)
    d.rectangle([0, bh - e, unit_w, bh], fill=edge)
    return np.asarray(im)


def _ribbon_frame(strip, t, dur, length, amp, wavelength, speed, angle, direction, wipe=0.35):
    unit_w = strip.shape[1]
    tiled = np.concatenate([strip] * (length // unit_w + 3), axis=1)
    off = int((speed * t) % unit_w)
    x0 = unit_w - off if direction > 0 else off  # >0: content flows left -> right
    band = tiled[:, x0:x0 + length]
    bh = band.shape[0]
    hc = bh + 2 * amp
    xs = np.arange(length)
    shift = amp * np.sin(2 * np.pi * xs / wavelength - direction * 2 * np.pi * t * 0.6)
    rows = np.arange(hc)[:, None] - (amp + shift[None, :]).round().astype(int)
    valid = (rows >= 0) & (rows < bh)
    out = np.zeros((hc, length, 4), np.uint8)
    out[valid] = band[rows.clip(0, bh - 1), np.broadcast_to(xs, rows.shape)][valid]
    # wipe in from the left, out to the right
    reveal_in = min(1.0, t / wipe)
    reveal_out = max(0.0, (t - (dur - wipe)) / wipe)
    ease = lambda v: 1 - (1 - v) ** 3
    lo, hi = int(ease(reveal_out) * length), int(ease(reveal_in) * length)
    mask = np.zeros(length, bool)
    mask[lo:hi] = True
    out[:, ~mask, 3] = 0
    im = Image.fromarray(out, "RGBA")
    # soft drop shadow
    sh = Image.new("RGBA", im.size, (40, 20, 10, 0))
    sh.putalpha(im.getchannel("A").point(lambda v: v * 0.35).filter(ImageFilter.GaussianBlur(10)))
    comp = Image.new("RGBA", (im.width, im.height + 24), (0, 0, 0, 0))
    comp.alpha_composite(sh, (0, 16))
    comp.alpha_composite(im, (0, 0))
    return comp.rotate(angle, Image.BICUBIC, expand=True)


def render(out_dir, dur, ribbons, size=(1080, 560), fps=30):
    """ribbons: list of dict(words, colors, cy, angle, direction, bh, speed). Writes %04d.png."""
    os.makedirs(out_dir, exist_ok=True)
    w, h = size
    strips = [_strip(r["words"], r["colors"], r.get("bh", 150)) for r in ribbons]
    n = round(dur * fps)
    for f in range(n):
        t = f / fps
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        for r, strip in zip(ribbons, strips):
            im = _ribbon_frame(strip, t, dur, length=1500, amp=r.get("amp", 26), wavelength=r.get("wavelength", 520),
                               speed=r.get("speed", 260), angle=r["angle"], direction=r["direction"])
            canvas.alpha_composite(im, ((w - im.width) // 2, r["cy"] - im.height // 2))
        canvas.save(os.path.join(out_dir, f"{f:04d}.png"))
    return n


if __name__ == "__main__":  # quick preview
    import sys
    render(sys.argv[1], 1.0, [
        dict(words=["COFFEE WITH KIRTI", "EP 04"], colors=BUTTER, cy=300, angle=7, direction=-1, bh=110),
        dict(words=["RATING TAN COFFEE", "LOSING TO A JAR"], colors=PINK, cy=270, angle=-6, direction=1),
    ])
