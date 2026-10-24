"""Coffee with Kirti - Episode 4: edit + render pipeline.

Usage: python3 edit.py   (footage expected in ../footage/ep04, output in ./build)
"""
import os, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "footage", "ep04")
FONTS = os.path.join(HERE, "..", "fonts")
BUILD = os.path.join(HERE, "build")
W, H, FPS = 1080, 1920, 30

# Per-source grade: neutralise the night-street blue (v1) and the heavy
# tungsten yellow of the cafe (v2/v3), then one shared creamy "latte" finish:
# soft matte blacks, rolled-off highlights, gentle yellows, warm mids.
GRADE = {
    "v1": "hqdn3d=4:3:6:6,colortemperature=temperature=5600:mix=0.6,eq=brightness=0.06:gamma=1.15:saturation=0.95,colorbalance=gs=-0.05:gm=-0.04:gh=-0.02",
    "v2": "colortemperature=temperature=9000:mix=0.7,eq=saturation=0.82:gamma=1.04",
    "v3": "colortemperature=temperature=8600:mix=0.65,eq=saturation=0.85",
}
FINISH = ("curves=r='0/0.05 0.5/0.52 1/0.96':g='0/0.045 0.5/0.5 1/0.95':b='0/0.06 0.5/0.47 1/0.9',"
          "selectivecolor=yellows='-0.1 0 0.15 0':reds='0 0.03 0.05 0':neutrals='0 0 0.03 0',"
          "eq=contrast=1.04:saturation=0.92,vignette=angle=0.3")

# Edit decision list. Captions use source-clip times; **word** = highlight.
# gain: dialogue level (b-roll is ducked so the music carries it).
# punch: source time of a quick punch-in; hook/sticker: on-screen text; sfx: sound accent.
EDL = [
    # cold open - the laugh + the line that makes you ask "wait, why?"
    dict(src="v1", a=8.9, b=12.4, zoom=1.08, punch=10.4, hook="POV: fresh haircuts, zero plans",
         caps=[(10.4, 12.36, "we're sitting on the **ROAD**")]),
    # title over the first dessert jar
    dict(src="v2", a=0.6, b=2.7, gain=0.35, title=True, sfx="whoosh", flash=True),
    dict(src="v1", a=0.0, b=2.3, chapter=("01", "the road"), caps=[(0.0, 2.3, "no idea where we've ended up")]),
    dict(src="v1", a=3.9, b=9.0, punch=6.6, caps=[
        (3.98, 5.88, "sitting on the road"),
        (5.88, 9.0, "after getting haircuts like **THIS**")]),
    dict(src="v1", a=12.3, b=14.6, zoom=1.1, caps=[(12.36, 14.6, "haan, **piyenge** yaar!")]),
    dict(src="v2", a=19.3, b=21.0, gain=0.3, sfx="whoosh", flash=True, chapter=("02", "tan coffee")),
    dict(src="v2", a=6.0, b=8.1, caps=[(6.14, 8.1, "this is **nice**, guys")]),
    dict(src="v2", a=9.0, b=11.6, punch=10.4, caps=[(9.02, 11.6, "now... the **first bite**")]),
    dict(src="v2", a=23.0, b=25.0, gain=0.25),
    dict(src="v2", a=28.1, b=32.1, punch=29.94, sticker=(29.95, "taste test: PASSED"),
         caps=[(28.22, 29.9, "how is it?"), (29.94, 31.0, "**very tasty**"), (31.1, 32.1, "it IS tasty")]),
    dict(src="v2", a=36.7, b=38.0, caps=[(36.88, 38.0, "so, **Kirti?**")]),
    dict(src="v2", a=46.2, b=48.6, punch=46.5, caps=[(46.4, 48.4, "it's **very tasty**")]),
    # the jar that would not open
    dict(src="v3", a=7.8, b=11.0, flash=True, chapter=("03", "the jar"), caps=[(8.0, 8.6, "**talent!**"), (8.86, 11.0, "what are you doing? open it like this")]),
    dict(src="v3", a=12.0, b=14.1, punch=12.3, sticker=(12.9, "jar 1 – us 0"),
         caps=[(12.24, 14.1, "nobody can even **open** this")]),
    # sign-off
    dict(src="v2", a=32.6, b=35.6, punch=34.86, caps=[(32.76, 34.8, "so you should come to **Tan Coffee** again"), (34.86, 35.6, "**again!**")]),
    # ...then the laugh "develops" into a polaroid
    dict(src="v1", a=2.3, b=3.05, zoom=1.05),
    dict(src="v1", still=3.0, dur=3.4, polaroid=True, endcard=True, flash=True, sfx="shutter"),
]


def run(cmd):
    subprocess.run(cmd, check=True)


def seg_polaroid(out, s):
    """Freeze the moment as a slightly tilted polaroid over a blurred copy of itself."""
    n = round(s["dur"] * FPS)
    look = f"{GRADE[s['src']]},{FINISH}"
    fc = (f"[0:v]fps={FPS},{look},split[bg][fg];"
          f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=30,eq=brightness=-0.12[b];"
          "[fg]scale=720:900:force_original_aspect_ratio=increase:flags=lanczos,crop=720:900,unsharp=5:5:0.5,"
          "pad=772:1056:26:26:color=0xF7F2EA,format=rgba,rotate=-3*PI/180:ow=rotw(iw):oh=roth(ih):c=none[card];"
          f"[b][card]overlay=x=(W-w)/2:y=760-h/2,"
          f"zoompan=z='1.0+0.06*exp(-in/5)+0.02*in/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={W}x{H}:fps={FPS},"
          "format=yuv420p[v]")
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", os.path.join(BUILD, "still.png"),
         "-f", "lavfi", "-t", f"{n/FPS:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
         "-filter_complex", fc, "-map", "[v]", "-map", "1:a", "-frames:v", str(n),
         "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "pcm_s16le", "-t", f"{n/FPS:.3f}", out])
    return out, n / FPS


def seg_video(i, s):
    out = os.path.join(BUILD, f"seg{i:02d}.mp4")
    if s.get("polaroid"):
        if os.environ.get("REUSE_SEGMENTS") and os.path.exists(out):
            return out, round(s["dur"] * FPS) / FPS
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(s["still"]), "-i", os.path.join(SRC, s["src"] + ".mp4"),
             "-frames:v", "1", os.path.join(BUILD, "still.png")])
        return seg_polaroid(out, s)
    d = s["b"] - s["a"]
    frz = s.get("freeze", 0.0)
    n = round(d * FPS) + round(frz * FPS)
    if os.environ.get("REUSE_SEGMENTS") and os.path.exists(out):
        return out, n / FPS
    z = s.get("zoom", 1.0)
    # gentle push-in across every shot + an eased snap punch-in on the funny beat
    zexpr = f"{z}+0.035*in/{round(d*FPS)}"
    if "punch" in s:
        p = round((s["punch"] - s["a"]) * FPS)
        zexpr += f"+0.14*min(1,max(0,(in-{p})/4))"
    fit = f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}"
    zoom = (f"zoompan=z='{zexpr}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={W}x{H}:fps={FPS}")
    pad = f",tpad=stop_mode=clone:stop_duration={frz}" if frz else ""
    g = s.get("gain", 1.0)
    vf = f"fps={FPS},hqdn3d=2:2:4:4,{fit},{zoom}{pad},unsharp=5:5:0.5,{GRADE[s['src']]},{FINISH},format=yuv420p"
    af = (f"aresample=48000,aformat=channel_layouts=stereo,volume={g},"
          f"afade=t=in:d=0.03,afade=t=out:st={d-0.04:.3f}:d=0.04,apad=whole_dur={n/FPS:.3f}")
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(s["a"]), "-t", f"{d:.3f}", "-i", os.path.join(SRC, s["src"] + ".mp4"),
         "-vf", vf, "-af", af, "-frames:v", str(n), "-c:v", "libx264", "-crf", "16", "-preset", "medium",
         "-c:a", "pcm_s16le", "-t", f"{n/FPS:.3f}", out])
    return out, n / FPS


def ts(t):
    h, r = divmod(max(t, 0), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ass_text(t):
    # **word** -> warm caramel serif-italic accent inside the clean sans caption
    parts = t.split("**")
    return "".join(p if k % 2 == 0 else r"{\fnCormorant Garamond Medium Italic\fs118\bord5\shad3\c&H8FC8F2&}" + p + r"{\r}"
                   for k, p in enumerate(parts))


def build_ass(timeline):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter ExtraBold,76,&H00FFFFFF,&H00FFFFFF,&H00141018,&H96000000,0,0,0,0,100,100,0,0,1,6,3,2,100,100,440,1
Style: Hook,Inter ExtraBold,68,&H00181410,&H00FFFFFF,&H00F4F8FB,&H00000000,0,0,0,0,100,100,0,0,3,18,0,8,90,90,290,1
Style: Sticker,Inter ExtraBold,62,&H00181410,&H00FFFFFF,&H006BC6FF,&H00000000,0,0,0,0,100,100,0,0,3,16,0,5,0,0,0,1
Style: Title,Cormorant Garamond SemiBold,128,&H00F3F7FB,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,0,4,5,60,60,0,1
Style: Sub,Cormorant Garamond Medium Italic,66,&H00A9D3EE,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,6,0,1,0,3,5,60,60,0,1
Style: ChapNo,Inter SemiBold,30,&H00DCE8F2,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,9,0,1,0,2,8,0,0,300,1
Style: Chap,Cormorant Garamond Medium Italic,92,&H00F3F7FB,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,1,0,1,0,3,8,0,0,345,1
Style: Card,Cormorant Garamond Medium Italic,50,&H00403A36,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,0,0,5,0,0,0,1
Style: Flash,Inter,10,&H00F7FAFC,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Rule,Inter,10,&H00A9D3EE,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    pop = r"{\fad(60,90)\fscx80\fscy80\t(0,90,\fscx108\fscy108)\t(90,170,\fscx100\fscy100)}"
    sticker = r"\fscx0\fscy0\t(0,120,\fscx118\fscy118)\t(120,220,\fscx100\fscy100)\fad(0,150)"
    band = lambda t0, t1, y: (f"Dialogue: 0,{ts(t0)},{ts(t1)},Rule,,0,0,0,,{{\\pos(0,{y})\\an7\\1c&H0A0C10&\\1a&H70&"
                              f"\\blur40\\fad(300,300)\\p1}}m 0 0 l 1080 0 1080 470 0 470{{\\p0}}")
    rel = lambda start, s, x: start + x - s["a"]
    for start, dur, s in timeline:
        end = start + dur
        for (ca, cb, txt) in s.get("caps", []):
            t0, t1 = max(rel(start, s, ca), start), min(rel(start, s, cb), end)
            ev.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},Cap,,0,0,0,,{pop}{ass_text(txt)}")
        if "hook" in s:
            ev.append(f"Dialogue: 3,{ts(start)},{ts(end)},Hook,,0,0,0,,{{\\fad(0,120)\\fscx85\\fscy85\\t(0,120,\\fscx100\\fscy100)}}{s['hook']}")
        if "sticker" in s:
            st, txt = s["sticker"]
            ev.append(f"Dialogue: 3,{ts(rel(start, s, st))},{ts(end)},Sticker,,0,0,0,,{{\\pos(740,600)\\frz7{sticker}}}{txt}")
        if s.get("title"):
            a, b, y = start + 0.1, end - 0.05, 760
            ev.append(band(a - 0.05, b, y - 200))
            rise = lambda y0: rf"\move(540,{y0+18},540,{y0},0,400)"
            f = r"{\fad(250,200)\blur0.6}"
            ev.append(f"Dialogue: 2,{ts(a)},{ts(b)},Title,,0,0,0,,{{{rise(y)}}}{f}Coffee with Kirti")
            ev.append(f"Dialogue: 2,{ts(a+0.15)},{ts(b)},Rule,,0,0,0,,{{\\pos(540,{y+92})\\fad(250,200)\\p1}}m 0 0 l 220 0 220 3 0 3{{\\p0}}")
            ev.append(f"Dialogue: 2,{ts(a+0.2)},{ts(b)},Sub,,0,0,0,,{{{rise(y+160)}}}{f}Episode 4")
        if "chapter" in s:
            no, name = s["chapter"]
            ev.append(f"Dialogue: 3,{ts(start+0.05)},{ts(start+1.7)},ChapNo,,0,0,0,,{{\\fad(220,260)}}CHAPTER {no}")
            ev.append(f"Dialogue: 3,{ts(start+0.12)},{ts(start+1.7)},Chap,,0,0,0,,{{\\an8\\fad(260,260)\\move(540,363,540,345,0,400)}}{name}")
        if s.get("flash"):  # soft white flash, like a camera blink, on scene changes
            ev.append(f"Dialogue: 4,{ts(start)},{ts(start+0.22)},Flash,,0,0,0,,{{\\pos(0,0)\\1a&H30&\\fad(0,200)\\p1}}m 0 0 l {W} 0 {W} {H} 0 {H}{{\\p0}}")
        if s.get("endcard"):
            ev.append(f"Dialogue: 3,{ts(start+0.35)},{ts(end)},Card,,0,0,0,,{{\\pos(560,1236)\\frz3\\fad(400,0)}}ep. 04 · tan coffee")
            ev.append(f"Dialogue: 3,{ts(start+0.55)},{ts(end)},Title,,0,0,0,,{{\\pos(540,1400)\\fs110\\fad(300,0)}}Coffee with Kirti")
            ev.append(f"Dialogue: 3,{ts(start+0.9)},{ts(end)},Cap,,0,0,0,,{{\\an5\\pos(540,1500)\\fs46\\bord3{sticker}}}"
                      f"tag the friend you'd sit on the road with")
    return head + "\n".join(ev) + "\n"


def sfx(timeline, total, path, sr=48000):
    """Small synthesised accents: whoosh into new scenes, pop on stickers/punch-ins."""
    rng = np.random.default_rng(7)
    out = np.zeros(int((total + 1) * sr))

    def put(x, at):
        i = int(at * sr)
        j = min(i + len(x), len(out))
        if i < len(out):
            out[i:j] += x[:j-i]

    t = lambda d: np.arange(int(d * sr)) / sr
    def whoosh():
        x = t(0.45); n = rng.standard_normal(len(x))
        # band of noise swept upward, smoothed by a moving average that shrinks over time
        env = np.sin(np.pi * x / 0.45) ** 2
        k = np.convolve(n, np.ones(24) / 24, "same") * (1 - x / 0.45) + np.diff(n, prepend=0) * 0.15 * (x / 0.45)
        return k * env * 0.5
    def pop():
        x = t(0.12)
        return np.sin(2 * np.pi * (900 - 2500 * x) * x) * np.exp(-x * 45) * 0.45
    def shutter():
        x = t(0.16); n = rng.standard_normal(len(x))
        clicks = np.exp(-x * 120) + 0.7 * np.exp(-np.clip(x - 0.07, 0, None) * 140) * (x > 0.07)
        return np.diff(n, prepend=0) * clicks * 0.6

    def ding():
        x = t(0.7)
        return (np.sin(2*np.pi*1568*x) + 0.4*np.sin(2*np.pi*2349*x)) * np.exp(-x * 7) * 0.18

    for start, dur, s in timeline:
        if s.get("sfx") == "whoosh":
            put(whoosh(), max(start - 0.2, 0))
        if s.get("sfx") == "shutter":
            put(shutter(), start)
        if "punch" in s:
            put(pop() * 0.5, start + s["punch"] - s["a"])
        if "sticker" in s:
            put(ding(), start + s["sticker"][0] - s["a"])
    out /= max(np.abs(out).max(), 1e-9)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes((out * 0.7 * 32767).astype(np.int16).tobytes())


def music(dur, path, sr=48000, bpm=100):
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
        if k >= 1:  # playful top line
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
    fx = os.path.join(BUILD, "sfx.wav")
    sfx(timeline, total, fx)
    final = os.path.join(HERE, "Coffee_with_Kirti_Ep04.mp4")
    # Dialogue clean-up: cut rumble/hiss, strip cafe noise, tame the room boom that
    # reads as echo, close the gaps between words, then lift and level the voices.
    voice = ("highpass=f=120,lowpass=f=8500,afftdn=nr=20:nf=-30:tn=1,"
             "equalizer=f=220:t=q:w=1.2:g=-4,equalizer=f=500:t=q:w=1.5:g=-2,"
             "agate=threshold=0.015:ratio=3:attack=4:release=140:range=0.25,"
             "equalizer=f=3200:t=q:w=1:g=4,equalizer=f=6500:t=q:w=1:g=1.5,deesser,"
             "speechnorm=e=8:r=0.0001:l=1,"
             "acompressor=threshold=-20dB:ratio=4:attack=5:release=120:makeup=4")
    fc = (f"[0:v]subtitles={ass}:fontsdir={FONTS},fade=t=out:st={total-0.4:.2f}:d=0.4[v];"
          f"[0:a]{voice},asplit[dia][key];"
          "[1:a]lowpass=f=7000,volume=1.1[mus];"
          "[mus][key]sidechaincompress=threshold=0.02:ratio=10:attack=20:release=350[duck];"
          "[2:a]aformat=channel_layouts=stereo,volume=0.5[fx];"
          "[dia][duck][fx]amix=inputs=3:normalize=0,loudnorm=I=-12:TP=-2:LRA=7,alimiter=limit=0.79:level=0,"
          f"afade=t=out:st={total-0.8:.2f}:d=0.8[a]")
    run(["ffmpeg", "-v", "error", "-y", "-i", cut, "-i", bed, "-i", fx, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", final])
    print(f"rendered {final} ({total:.1f}s)")


if __name__ == "__main__":
    main()
