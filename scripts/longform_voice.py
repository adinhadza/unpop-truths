#!/usr/bin/env python3
"""Free narration with Kokoro (open-source TTS, runs on CPU).
usage: longform_voice.py scenes.json out_dir --voice am_michael [--speed 1.0] [--only 01,02] [--joined sample.wav]
Writes one WAV per scene (24 kHz mono) so every picture can be timed to its line."""
import argparse, json, os
import numpy as np, soundfile as sf
from kokoro import KPipeline

ap = argparse.ArgumentParser()
ap.add_argument("scenes"); ap.add_argument("out")
ap.add_argument("--voice", default="am_michael"); ap.add_argument("--speed", type=float, default=1.0)
ap.add_argument("--only", default=""); ap.add_argument("--joined", default="")
a = ap.parse_args()
job = json.load(open(a.scenes)); os.makedirs(a.out, exist_ok=True)
only = set(x.strip() for x in a.only.split(",") if x.strip())
lang = "b" if a.voice.startswith("b") else "a"
pipe = KPipeline(lang_code=lang)
joined = []
for s in job["scenes"]:
    if only and s["id"] not in only:
        continue
    text = s["narration"].replace("…", "...")
    parts = [aud for _, _, aud in pipe(text, voice=a.voice, speed=a.speed)]
    audio = np.concatenate([p.numpy() if hasattr(p, "numpy") else p for p in parts])
    sf.write(os.path.join(a.out, f"{s['id']}.wav"), audio, 24000)
    joined += [audio, np.zeros(int(24000 * 0.35))]
    print(s["id"], round(len(audio) / 24000, 2), "s", flush=True)
if a.joined and joined:
    sf.write(a.joined, np.concatenate(joined), 24000)
