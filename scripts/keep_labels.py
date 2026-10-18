#!/usr/bin/env python3
"""Keep the in-scene labels visible for the whole clip.
Veo often fades the top labels out after ~3 s. This takes the white, low-saturation
pixels (text + halo ring) from an early frame in the top band and overlays them on
every frame.
usage: keep_labels.py RAW.mp4 OUT.mp4 [--t 0.3] [--band 340] [--skip x0:y0:x1:y1 ...]
--skip zeroes rectangles (e.g. a bright rail that is not a label)."""
import argparse, subprocess, tempfile, os
import numpy as np
from PIL import Image, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("raw"); ap.add_argument("out")
ap.add_argument("--t", type=float, default=0.3)
ap.add_argument("--band", type=int, default=340)
ap.add_argument("--skip", nargs="*", default=[])
a = ap.parse_args()
tmp = tempfile.mkdtemp()
f0 = os.path.join(tmp, "f0.png"); lab = os.path.join(tmp, "lab.png")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.t), "-i", a.raw, "-frames:v", "1", f0], check=True)
im = np.asarray(Image.open(f0).convert("RGB")).astype(float)
lum = 0.299*im[..., 0] + 0.587*im[..., 1] + 0.114*im[..., 2]
sat = im.max(-1) - im.min(-1)
al = np.clip((lum-205)/30, 0, 1) * np.clip((45-sat)/25, 0, 1)
al[a.band:, :] = 0
for r in a.skip:
    x0, y0, x1, y1 = map(int, r.split(":")); al[y0:y1, x0:x1] = 0
alpha = Image.fromarray((al*255).astype("uint8")).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
rgba = Image.fromarray(im.astype("uint8")).convert("RGBA"); rgba.putalpha(alpha); rgba.save(lab)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.raw, "-i", lab, "-filter_complex",
                "[0:v][1:v]overlay=0:0,format=yuv420p[v]", "-map", "[v]", "-map", "0:a?",
                "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-c:a", "copy", a.out], check=True)
