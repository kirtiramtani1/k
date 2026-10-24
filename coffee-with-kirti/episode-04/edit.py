"""Coffee with Kirti - Episode 4: edit + render pipeline.

Usage: python3 edit.py   (footage expected in ../footage/ep04, output in ./build)
"""
import os, subprocess, wave
import numpy as np
import ribbon
from ribbon import PINK, BUTTER

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "footage", "ep04")
FONTS = os.path.join(HERE, "..", "fonts")
BUILD = os.path.join(HERE, "build")
RNNOISE = os.path.join(HERE, "..", "models", "sh.rnnn")  # RNNoise speech model (somnolent-hogwash)
W, H, FPS = 1080, 1920, 30

# Per-source grade: neutralise the night-street blue (v1) and the heavy
# tungsten orange of the cafe (v2/v3), then one shared warm "coffee" finish.
GRADE = {
    "v1": "colortemperature=temperature=5200:mix=0.6,eq=brightness=0.045:gamma=1.1",
    "v2": "colortemperature=temperature=7600:mix=0.55,eq=saturation=0.86",
    "v3": "colortemperature=temperature=7200:mix=0.45,eq=saturation=0.9",
    "img": "eq=saturation=0.95",
}
FINISH = ("curves=all='0/0.03 0.25/0.22 0.5/0.5 0.75/0.79 1/0.97',"
          "colorbalance=rs=0.02:bs=-0.03:rh=0.03:gh=0.01:bh=-0.03,"
          "vibrance=intensity=0.08,vignette=angle=0.35")

# Edit decision list. Captions use source-clip times; **word** = highlight.
# gain: dialogue level (b-roll is ducked so the music carries it).
EDL = [
    # cold open - the jar that beat us, with one line to make you stay
    dict(src="v3", a=11.0, b=14.1, zoom=1.12, ribbon_y=150, ribbons=[
        dict(words=["COFFEE WITH KIRTI", "EP 04"], colors=BUTTER, cy=330, angle=8, direction=-1, bh=110),
        dict(words=["RATING TAN COFFEE", "LOSING TO A JAR"], colors=PINK, cy=230, angle=-6, direction=1, bh=165, speed=430)],
         caps=[(12.24, 14.1, "nobody can even **open** this")]),
    # title over the first dessert jar (which, ironically, opens just fine)
    dict(src="v2", a=0.0, b=3.6, zoom=1.0, gain=0.15, title=True),
    dict(src="v2", a=19.0, b=21.4, zoom=1.0, gain=0.15),
    dict(src="v2", a=4.2, b=8.1, zoom=1.0, caps=[(6.14, 8.1, "this is **nice**, guys")]),
    dict(src="v2", a=9.0, b=12.6, zoom=1.06, caps=[(9.02, 11.6, "now... the **first bite**")]),
    dict(src="v2", a=14.0, b=16.4, zoom=1.0, caps=[(14.8, 16.3, "let's taste it")]),
    dict(src="v2", a=22.0, b=26.0, zoom=1.0, gain=0.12, note="the order"),
    dict(src="v2", a=27.9, b=29.9, zoom=1.0, caps=[(28.22, 29.9, "how is it?")]),
    dict(src="v2", a=29.9, b=32.1, zoom=1.14, caps=[(29.94, 31.0, "**very tasty**"), (31.1, 32.1, "it IS tasty")]),
    dict(src="v2", a=36.7, b=38.0, zoom=1.0, caps=[(36.88, 38.0, "so, **Kirti?**")]),
    dict(src="v2", a=40.2, b=43.0, zoom=1.0, gain=0.12),
    dict(src="v2", a=45.9, b=48.9, zoom=1.0, caps=[(46.4, 48.4, "it's **very tasty**")]),
    # the jar that would not open
    dict(src="v3", a=7.7, b=11.0, zoom=1.0, caps=[(8.0, 8.6, "**talent!**"), (8.86, 11.0, "what are you doing? open it like this")]),
    dict(src="v3", a=11.0, b=14.1, zoom=1.15, note="jar 1 – us 0", caps=[(12.24, 14.1, "nobody can even **open** this")]),
    # sign-off, then the end card over one last happy bite
    dict(src="v2", a=32.6, b=35.6, zoom=1.0, caps=[(32.76, 34.8, "so you should come to **Tan Coffee** again"), (34.86, 35.6, "again!")]),
    dict(src="v2", a=50.0, b=54.0, zoom=1.0, gain=0.15, endcard=True, ribbon_y=1080, ribbons=[
        dict(words=["SEE YOU AT THE NEXT TABLE", "COFFEE WITH KIRTI"], colors=PINK, cy=230, angle=-5, direction=1, bh=130)]),
]


def run(cmd):
    subprocess.run(cmd, check=True)


def seg_video(i, s):
    out = os.path.join(BUILD, f"seg{i:02d}.mp4")
    if os.environ.get("REUSE_SEGMENTS") and os.path.exists(out):
        d = s["dur"] if "dur" in s else s["b"] - s["a"]
        return out, round(d * FPS) / FPS
    z = s.get("zoom", 1.0)
    fit = f"scale={int(W*z)}:{int(H*z)}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"
    if s["src"].startswith("i"):
        d = s["dur"]
        n = int(d * FPS)
        vf = (f"scale=2160:-2:flags=lanczos,zoompan=z='1.0+0.06*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'"
              f":d={n}:s={W}x{H}:fps={FPS},{GRADE['img']},{FINISH},format=yuv420p")
        run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(d), "-i", os.path.join(SRC, s["src"] + ".jpg"),
             "-f", "lavfi", "-t", str(d), "-i", "anullsrc=r=48000:cl=stereo",
             "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-crf", "16", "-preset", "medium",
             "-c:a", "pcm_s16le", "-shortest", out])
        return out, n / FPS
    d = s["b"] - s["a"]
    g = s.get("gain", 1.0)
    vf = (f"fps={FPS},hqdn3d=2:2:4:4,{fit},unsharp=5:5:0.6,{GRADE[s['src']]},{FINISH},format=yuv420p")
    af = (f"aresample=48000,aformat=channel_layouts=stereo,highpass=f=90,volume={g},"
          f"afade=t=in:d=0.03,afade=t=out:st={d-0.04:.3f}:d=0.04")
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(s["a"]), "-t", f"{d:.3f}", "-i", os.path.join(SRC, s["src"] + ".mp4"),
         "-vf", vf, "-af", af, "-frames:v", str(round(d * FPS)), "-c:v", "libx264", "-crf", "16", "-preset", "medium",
         "-c:a", "pcm_s16le", out])
    return out, round(d * FPS) / FPS


def ts(t):
    h, r = divmod(max(t, 0), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ass_text(t):
    # **word** -> warm caramel highlight
    parts = t.split("**")
    return "".join(p if k % 2 == 0 else r"{\c&H6FB0E8&}" + p + r"{\c&HFFFFFF&}" for k, p in enumerate(parts))


def build_ass(timeline):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter SemiBold,68,&H00FFFFFF,&H00FFFFFF,&H8C0E1218,&H00000000,0,0,0,0,100,100,0.3,0,3,16,0,2,110,110,430,1
Style: Title,Cormorant Garamond SemiBold,128,&H00F3F7FB,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,0,4,5,60,60,0,1
Style: Sub,Cormorant Garamond Medium Italic,66,&H00A9D3EE,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,6,0,1,0,3,5,60,60,0,1
Style: Note,Cormorant Garamond Medium Italic,78,&H00F3F7FB,&H00FFFFFF,&H00000000,&H8C000000,0,0,0,0,100,100,0.5,0,1,0,3,8,90,90,300,1
Style: Rule,Inter,10,&H00A9D3EE,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    pop = r"{\fad(90,110)\fscx94\fscy94\t(0,140,\fscx100\fscy100)}"
    for start, dur, s in timeline:
        for (ca, cb, txt) in s.get("caps", []):
            if "dur" in s:
                t0, t1 = start + ca, start + cb
            else:
                t0, t1 = start + max(ca - s["a"], 0), start + min(cb - s["a"], dur)
            ev.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},Cap,,0,0,0,,{pop}{ass_text(txt)}")
        if "note" in s:  # soft dark band at the top keeps the serif line readable on bright frames
            ev.append(f"Dialogue: 1,{ts(start+0.05)},{ts(start+dur-0.05)},Rule,,0,0,0,,{{\\pos(0,140)\\an7\\1c&H0A0C10&\\1a&H68&"
                      f"\\blur45\\fad(300,250)\\p1}}m 0 0 l 1080 0 1080 330 0 330{{\\p0}}")
            ev.append(f"Dialogue: 2,{ts(start+0.1)},{ts(start+dur-0.05)},Note,,0,0,0,,"
                      r"{\fad(350,250)\blur0.4\fscx96\fscy96\t(0,600,\fscx100\fscy100)}" + s["note"])
        if s.get("title") or s.get("endcard"):
            a, b = start + 0.25, start + dur - (0.15 if s.get("title") else 0.0)
            y = 760 if s.get("title") else 820
            f = r"{\fad(450,350)\blur0.6" + "}"
            # soft dark band so the serif title reads on any background
            ev.append(f"Dialogue: 0,{ts(a-0.1)},{ts(b)},Rule,,0,0,0,,{{\\pos(0,{y-200})\\an7\\1c&H0A0C10&\\1a&H70&\\blur40\\fad(400,350)\\p1}}m 0 0 l 1080 0 1080 470 0 470{{\\p0}}")
            rise = lambda y0: rf"\move(540,{y0+18},540,{y0},0,600)"
            ev.append(f"Dialogue: 2,{ts(a)},{ts(b)},Title,,0,0,0,,{{{rise(y)}}}{f}Coffee with Kirti")
            ev.append(f"Dialogue: 2,{ts(a+0.25)},{ts(b)},Rule,,0,0,0,,{{\\pos(540,{y+92})\\fad(450,350)\\p1}}m 0 0 l 220 0 220 3 0 3{{\\p0}}")
            sub = "Episode 4" if s.get("title") else "see you at the next table"
            ev.append(f"Dialogue: 2,{ts(a+0.35)},{ts(b)},Sub,,0,0,0,,{{{rise(y+160)}}}{f}{sub}")
    return head + "\n".join(ev) + "\n"


def music(dur, path, sr=48000, bpm=84):
    """Original warm lo-fi bed (synthesised here, so it's free to publish)."""
    rng = np.random.default_rng(4)
    n = int(dur * sr) + sr
    out = np.zeros((n, 2))
    beat = 60 / bpm
    bar = beat * 4

    def note(f, length, amp, pan=0.0, kind="keys"):
        t = np.arange(int(length * sr)) / sr
        if kind == "keys":  # soft electric-piano: fundamental + bell partial, slow decay, tremolo
            w = np.sin(2*np.pi*f*t) + 0.35*np.sin(2*np.pi*2*f*t)*np.exp(-t*3) + 0.08*np.sin(2*np.pi*3.01*f*t)*np.exp(-t*6)
            env = np.minimum(t/0.012, 1) * np.exp(-t*0.9)
            w *= env * (1 + 0.12*np.sin(2*np.pi*4.5*t))
        else:  # round bass
            w = np.sin(2*np.pi*f*t) + 0.2*np.sin(2*np.pi*2*f*t)
            w *= np.minimum(t/0.02, 1) * np.exp(-t*1.6)
        w *= amp
        return np.stack([w*(1-pan)*0.5+w*0.5*(1-abs(pan)), w*(1+pan)*0.5+w*0.5*(1-abs(pan))], 1)

    def add(buf, at):
        i = int(at * sr)
        if i >= n:
            return
        j = min(i + len(buf), n)
        out[i:j] += buf[:j-i]

    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    prog = [  # Fmaj9, Em7, Dm9, Cmaj7(add6)
        ([53, 57, 60, 64, 67], 41), ([52, 55, 59, 62], 40),
        ([50, 53, 57, 60, 64], 38), ([48, 52, 55, 59, 62], 36)]
    melody = [72, 76, 74, 71, 69, 72, 71, 67]
    t, k = 0.0, 0
    while t < dur + bar:
        notes, root = prog[k % 4]
        for q, m in enumerate(notes):  # gentle strum
            add(note(hz(m), bar*1.1, 0.055, pan=(q-2)*0.25), t + q*0.018)
        add(note(hz(m := notes[1] + 12), beat*1.5, 0.035, pan=0.3), t + beat*2.5)
        add(note(hz(root), beat*1.8, 0.22, kind="bass"), t)
        add(note(hz(root + 7), beat*1.2, 0.15, kind="bass"), t + beat*2.5)
        if k >= 2 and k % 2 == 0:  # little playful top line
            for q in range(4):
                add(note(hz(melody[(k + q) % 8]), beat*0.9, 0.03, pan=-0.3), t + beat*(q + 0.5))
        for b in range(4):  # soft kick + brushed shaker
            bt = t + b*beat
            if b in (0, 2) or (b == 3 and k % 2):
                kt = np.arange(int(0.25*sr))/sr
                kick = np.sin(2*np.pi*(52 + 60*np.exp(-kt*30))*kt) * np.exp(-kt*14) * 0.28
                add(np.stack([kick, kick], 1), bt + (beat*0.5 if b == 3 else 0))
            for off, a in ((0, 0.018), (0.5, 0.03)):
                h = rng.standard_normal(int(0.06*sr)) * np.exp(-np.arange(int(0.06*sr))/sr*60) * a
                h = np.diff(h, prepend=0)
                add(np.stack([h*0.8, h], 1), bt + beat*off + 0.012*(off > 0))
        t += bar
        k += 1
    out = out[:int(dur*sr)]
    fade = int(2.5 * sr)
    out[:int(0.4*sr)] *= np.linspace(0, 1, int(0.4*sr))[:, None]
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    out /= np.abs(out).max() + 1e-9
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes((out * 0.8 * 32767).astype(np.int16).tobytes())


def main():
    os.makedirs(BUILD, exist_ok=True)
    timeline, files, t = [], [], 0.0
    for i, s in enumerate(EDL):
        f, d = seg_video(i, s)
        files.append(f)
        timeline.append((t, d, s))
        t += d
    total = t
    with open(os.path.join(BUILD, "list.txt"), "w") as fh:
        fh.writelines(f"file '{f}'\n" for f in files)
    cut = os.path.join(BUILD, "cut.mkv")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(BUILD, "list.txt"),
         "-c", "copy", cut])
    ass = os.path.join(BUILD, "captions.ass")
    with open(ass, "w") as fh:
        fh.write(build_ass(timeline))
    bed = os.path.join(BUILD, "music.wav")
    music(total, bed)
    final = os.path.join(HERE, "Coffee_with_Kirti_Ep04.mp4")
    # wavy pop-colour ribbons, each a PNG sequence overlaid at its segment's start time
    rib_inputs, rib_chain, label = [], "", "sub"
    for k, (start, dur, s) in enumerate(t for t in timeline if "ribbons" in t[2]):
        d = os.path.join(BUILD, f"ribbon{k}")
        ribbon.render(d, dur, s["ribbons"])
        rib_inputs += ["-itsoffset", f"{start:.3f}", "-framerate", str(FPS), "-i", os.path.join(d, "%04d.png")]
        rib_chain += f"[{label}][{k+2}:v]overlay=0:{s['ribbon_y']}:eof_action=pass[r{k}];"
        label = f"r{k}"
    fc = (f"[0:v]subtitles={ass}:fontsdir={FONTS}[sub];{rib_chain}"
          f"[{label}]fade=t=out:st={total-0.6:.2f}:d=0.6[v];"
          f"[0:a]highpass=f=100,arnndn=m={RNNOISE}:mix=0.9,afftdn=nr=12:nf=-35:tn=1,lowpass=f=9000,"
          "equalizer=f=220:t=q:w=1.2:g=-3,speechnorm=e=6:r=0.0001:l=1,"
          "acompressor=threshold=-22dB:ratio=3:attack=8:release=180:makeup=4,"
          "equalizer=f=3000:t=q:w=1:g=2.5,asplit[dia][key];"
          f"[1:a]lowpass=f=5200,volume=1.3[mus];"
          "[mus][key]sidechaincompress=threshold=0.03:ratio=7:attack=40:release=450[duck];"
          f"[dia][duck]amix=inputs=2:normalize=0,loudnorm=I=-13:TP=-2:LRA=8,alimiter=limit=0.79:level=0,"
          f"afade=t=out:st={total-1.2:.2f}:d=1.2[a]")
    run(["ffmpeg", "-v", "error", "-y", "-i", cut, "-i", bed, *rib_inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", final])
    print(f"rendered {final} ({total:.1f}s)")
    from cover import make_cover
    make_cover(os.path.join(HERE, "Coffee_with_Kirti_Ep04_cover.jpg"))


if __name__ == "__main__":
    main()
