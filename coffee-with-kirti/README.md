# Coffee with Kirti

## Episode 4 — Tan Coffee
`episode-04/edit.py` is the full edit: cut list, colour grade, captions, title cards,
an original synthesised music bed (free to publish), and the mix.

```
# put the raw clips in footage/ep04 as v1.mp4 v2.mp4 v3.mp4 i1.jpg i2.jpg i3.jpg
python3 episode-04/edit.py      # -> episode-04/Coffee_with_Kirti_Ep04.mp4 (1080x1920, 30fps, -14 LUFS)
```
Footage, renders and `models/` are git-ignored: put `sh.rnnn` (RNNoise, GregorR/rnnoise-models) and
`isnet-general-use.onnx` (rembg release) in `models/`. `cover.py` builds the cover; `ribbon.py` the wavy ribbons.
 Title font: Cormorant Garamond (OFL, `fonts/OFL.txt`); captions: Inter.
