"""Coffee with Kirti - Episode 4 cover (1080x1920, grid-safe centre 1080x1440).

Pastel collage style: bold serif headline, die-cut sticker cut-outs of the
real footage. Cut-outs use a local ISNet model (../models/isnet-general-use.onnx).
Usage: python3 cover.py
"""
import os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "footage", "ep04")
FONTS = os.path.join(HERE, "..", "fonts")
MODEL = os.path.join(HERE, "..", "models", "isnet-general-use.onnx")
BUILD = os.path.join(HERE, "build")
W, H = 1080, 1920

BUTTER = (247, 228, 150)
ESPRESSO = (43, 27, 20)
CARAMEL = (176, 104, 52)
CREAM = (251, 244, 228)
YELLOW = (255, 225, 77)

HEADLINE = [("POV: ", "2 girls"), ("vs ", "1 jar")]  # (roman, italic accent) per line


def frame(src, t):
    out = os.path.join(BUILD, f"cover_{src}_{t}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", os.path.join(SRC, src + ".mp4"),
                    "-frames:v", "1", "-vf",
                    "scale=iw*2.4:ih*2.4:flags=lanczos,unsharp=7:7:0.8,"
                    "colortemperature=temperature=6200:mix=0.4,eq=saturation=1.05:gamma=1.08", out], check=True)
    return Image.open(out).convert("RGB")


def cutout(im, sess, keep=None):
    x = np.asarray(im.resize((1024, 1024), Image.LANCZOS), np.float32) / 255.0 - 0.5
    m = sess.run(None, {sess.get_inputs()[0].name: x.transpose(2, 0, 1)[None]})[0][0, 0]
    m = (m - m.min()) / (m.max() - m.min())
    m = np.clip((m - 0.3) / 0.35, 0, 1)  # firm up soft fringes
    mask = Image.fromarray((m * 255).astype(np.uint8)).resize(im.size, Image.LANCZOS)
    if keep:  # only keep this box (fractions of the frame)
        box = Image.new("L", im.size, 0)
        x0, y0, x1, y1 = keep
        ImageDraw.Draw(box).rectangle([x0 * im.width, y0 * im.height, x1 * im.width, y1 * im.height], fill=255)
        mask = Image.fromarray(np.minimum(np.asarray(mask), np.asarray(box)))
    rgba = im.copy()
    rgba.putalpha(mask)
    return rgba.crop(mask.getbbox())


def sticker(rgba, border=18, shadow=True):
    """White die-cut border + soft shadow, like a printed sticker."""
    pad = border * 3
    a = ImageOps.expand(rgba, pad, fill=(0, 0, 0, 0))
    alpha = a.getchannel("A").point(lambda v: 255 if v > 90 else 0)
    edge = alpha.filter(ImageFilter.MaxFilter(border * 2 + 1)).filter(ImageFilter.GaussianBlur(1.2))
    out = Image.new("RGBA", a.size, (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", a.size, (60, 35, 20, 0))
        sh.putalpha(edge.point(lambda v: v * 0.35).filter(ImageFilter.GaussianBlur(18)))
        out.alpha_composite(sh, (8, 16))
    white = Image.new("RGBA", a.size, CREAM + (255,))
    white.putalpha(edge)
    out.alpha_composite(white)
    out.alpha_composite(a)
    return out


def polaroid(im, caption, size=(500, 600), border=22, bottom=92):
    """Selfie as a little polaroid print with a handwritten-style caption and soft shadow."""
    w, h = size
    s = max(w / im.width, h / im.height)
    ph = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    top = round(ph.height * 0.16)  # bias the crop upward: hair + face
    ph = ph.crop(((ph.width - w) // 2, top, (ph.width - w) // 2 + w, top + h))
    card = Image.new("RGBA", (w + 2 * border, h + border + bottom), CREAM + (255,))
    card.paste(ph, (border, border))
    font = ImageFont.truetype(os.path.join(FONTS, "CormorantGaramond-MediumItalic.ttf"), 52)
    ImageDraw.Draw(card).text((card.width / 2, h + border + bottom / 2), caption, font=font, fill=ESPRESSO, anchor="mm")
    pad = 40
    out = Image.new("RGBA", (card.width + 2 * pad, card.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (60, 35, 20, 90)).filter(ImageFilter.GaussianBlur(0))
    shadow = Image.new("RGBA", out.size, (0, 0, 0, 0))
    shadow.paste(sh, (pad + 6, pad + 14))
    out.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(16)))
    out.alpha_composite(card, (pad, pad))
    return out


def sparkle(d, cx, cy, r, fill):
    pts = []
    for k in range(8):
        ang = np.pi / 4 * k - np.pi / 2
        rr = r if k % 2 == 0 else r * 0.28
        pts.append((cx + rr * np.cos(ang), cy + rr * np.sin(ang)))
    d.polygon(pts, fill=fill)


def make_cover(path):
    import onnxruntime as ort
    os.makedirs(BUILD, exist_ok=True)
    sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
    friend = sticker(cutout(frame("v2", 35.2), sess), border=20)   # big smile, drinks + desserts at Tan Coffee
    kirti = polaroid(frame("v2", 47.3), "very tasty")              # "it's very tasty" selfie
    jar = sticker(cutout(frame("v3", 15.5), sess, keep=(0.0, 0.38, 1.0, 0.9)), border=16)

    # background: butter yellow with a soft light pool behind the headline
    bg = Image.new("RGB", (W, H), BUTTER)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([-200, 120, W + 200, 1100], fill=120)
    bg = Image.composite(Image.new("RGB", (W, H), (252, 240, 190)), bg, glow.filter(ImageFilter.GaussianBlur(160)))
    cv = bg.convert("RGBA")
    d = ImageDraw.Draw(cv)

    # series pill
    pill_font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 30)
    label = "COFFEE WITH KIRTI  ·  EP 04"
    tw = d.textlength(label, font=pill_font) + 30 * 0.12 * len(label)
    x0, y0 = (W - tw) / 2 - 34, 300
    d.rounded_rectangle([x0, y0, x0 + tw + 68, y0 + 64], radius=32, fill=ESPRESSO)
    x = x0 + 34
    for ch in label:  # tracked caps
        d.text((x, y0 + 15), ch, font=pill_font, fill=CREAM)
        x += d.textlength(ch, font=pill_font) + 30 * 0.12

    # headline: roman + caramel italic accent, centred per line
    roman = ImageFont.truetype(os.path.join(FONTS, "DMSerifDisplay-Regular.ttf"), 136)
    ital = ImageFont.truetype(os.path.join(FONTS, "DMSerifDisplay-Italic.ttf"), 136)
    y = 400
    for a, b in HEADLINE:
        wa, wb = d.textlength(a, font=roman), d.textlength(b, font=ital)
        x = (W - wa - wb) / 2
        d.text((x, y), a, font=roman, fill=ESPRESSO)
        d.text((x + wa, y), b, font=ital, fill=CARAMEL)
        y += 142

    # eyes emoji, like the reference's little reaction
    try:
        emo = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
        e = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
        ImageDraw.Draw(e).text((0, 0), "\U0001F440", font=emo, embedded_color=True)
        e = e.crop(e.getbbox()).resize((84, 84 * e.height // e.width), Image.LANCZOS) if e.getbbox() else None
        if e:
            cv.alpha_composite(e, ((W - e.width) // 2, y + 14))
    except OSError:
        pass

    # sparkles
    for cx, cy, r in [(150, 520, 34), (930, 470, 26), (980, 600, 14), (110, 690, 16)]:
        sparkle(d, cx, cy, r, CARAMEL)

    # Kirti's selfie tilted on the right, friend + the table in front on the left
    k = kirti.rotate(6, Image.BICUBIC, expand=True)
    cv.alpha_composite(k, (W - k.width + 30, 760))
    fw = 700
    f = friend.resize((fw, round(friend.height * fw / friend.width)), Image.LANCZOS).rotate(-4, Image.BICUBIC, expand=True)
    cv.alpha_composite(f, (-130, 1010))
    jw = 270
    j = jar.resize((jw, round(jar.height * jw / jar.width)), Image.LANCZOS).rotate(12, Image.BICUBIC, expand=True)
    jx, jy = W - 330, 1500
    cv.alpha_composite(j, (jx, jy))

    # "jar 1 - us 0" tag
    tag_font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", 44)
    txt = "jar 1 – us 0"
    tw = d.textlength(txt, font=tag_font)
    tag = Image.new("RGBA", (int(tw) + 90, 120), (0, 0, 0, 0))
    td = ImageDraw.Draw(tag)
    td.rounded_rectangle([10, 10, tw + 70, 96], radius=26, fill=YELLOW, outline=ESPRESSO, width=4)
    td.text((40, 26), txt, font=tag_font, fill=ESPRESSO)
    tag = tag.rotate(-8, Image.BICUBIC, expand=True)
    cv.alpha_composite(tag, (jx - 250, jy + j.height - 110))

    cv.convert("RGB").save(path, quality=95)


if __name__ == "__main__":
    make_cover(os.path.join(HERE, "Coffee_with_Kirti_Ep04_cover.jpg"))
    print("cover written")
