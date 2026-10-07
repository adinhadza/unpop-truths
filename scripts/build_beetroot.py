#!/usr/bin/env python3
"""Builds one Dr. Beetroot Reel (stock footage + voice + labels) from a script file.

Usage: build_beetroot.py <script.json> <output.mp4>
Needs in the working folder: kokoro.onnx, voices.bin, Poppins-Bold.ttf, Poppins-Medium.ttf.
Optional environment: VOICE (default af_heart), SPEED (default 0.95).

Script file: "title", "items" (a list) and "outro", each with "big", "sub", "say" and
an optional "clip". A clip is a Pixabay video link without the _large.mp4 ending, or a
full link to any MP4. A scene without a clip reuses the title clip.
"""
import json, os, subprocess, sys
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont
from kokoro_onnx import Kokoro

W, H, FPS, PAD = 1080, 1920, 30, 0.4
YEL, INK, WHITE = (255, 214, 10), (15, 18, 28), (255, 255, 255)
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = "build"


def font(weight, size):
    return ImageFont.truetype(f"Poppins-{weight}.ttf", size)


def note(msg):
    print(f"::notice::{msg}")


def fail(msg):
    print(f"::error::{msg}")
    sys.exit(1)


def run(cmd):
    subprocess.run(cmd, check=True)


def fetch_clip(link, name):
    """Downloads a clip and returns a 1080x1920 version, or None if it cannot be fetched."""
    raw, out = f"{WORK}/{name}_raw.mp4", f"{WORK}/{name}.mp4"
    tries = [link] if link.endswith(".mp4") else [f"{link}_{q}.mp4" for q in ("large", "medium", "small", "tiny")]
    for url in tries:
        ok = subprocess.run(["curl", "-sfL", "-m", "180", "-A", "Mozilla/5.0", "-o", raw, url]).returncode == 0
        if ok and os.path.getsize(raw) > 10000:
            break
    else:
        return None
    done = subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", "1", "-t", "8", "-i", raw, "-an", "-vf",
                           f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps={FPS}",
                           "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-pix_fmt", "yuv420p", out])
    return out if done.returncode == 0 else None


def centered(draw, y, text, fnt, fill, **kw):
    draw.text(((W - draw.textlength(text, font=fnt)) / 2, y), text, font=fnt, fill=fill, **kw)


def overlay(big, sub, number, mascot):
    """Transparent layer: dark gradients, number badge, labels, mascot badge and disclaimer."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    grad = Image.new("L", (1, H))
    for y in range(H):
        grad.putpixel((0, y), int(200 * max(0, (y - 900) / 1020) ** 1.2) + (int(120 * (1 - y / 420)) if y < 420 else 0))
    im.paste(Image.new("RGBA", (W, H), (0, 0, 0, 255)), (0, 0), grad.resize((W, H)))
    d = ImageDraw.Draw(im)
    if number:
        d.ellipse((60, 110, 200, 250), fill=YEL)
        f = font("Bold", 92)
        d.text((130 - d.textlength(str(number), font=f) / 2, 112), str(number), font=f, fill=INK)
    size = 150
    while d.textlength(big, font=font("Bold", size)) > W - 120:
        size -= 6
    centered(d, 1180, big, font("Bold", size), YEL, stroke_width=6, stroke_fill=INK)
    if sub:
        sub_size = 70
        while d.textlength(sub, font=font("Bold", sub_size)) > W - 100:
            sub_size -= 4
        centered(d, 1180 + size + 30, sub, font("Bold", sub_size), WHITE, stroke_width=4, stroke_fill=INK)
    d.ellipse((50, 1650, 230, 1830), fill=WHITE)
    mask = Image.new("L", (150, 150), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 150, 150), fill=255)
    im.paste(mascot, (65, 1665), mask)
    d.text((255, 1690), "Dr. Beetroot", font=font("Bold", 46), fill=WHITE)
    d.text((255, 1752), "General wellness info. Not medical advice.", font=font("Medium", 27), fill=(225, 225, 225))
    return im


def main():
    if len(sys.argv) != 3:
        fail("usage: build_beetroot.py <script.json> <output.mp4>")
    script, out = json.load(open(sys.argv[1])), sys.argv[2]
    os.makedirs(WORK, exist_ok=True)
    scenes = [dict(script["title"], number=0)]
    scenes += [dict(item, number=i + 1) for i, item in enumerate(script["items"])]
    scenes += [dict(script["outro"], number=0)]

    kokoro = Kokoro("kokoro.onnx", "voices.bin")
    voice, speed = os.environ.get("VOICE", "af_heart"), float(os.environ.get("SPEED", "0.95"))
    audio, rate = [], 24000
    for s in scenes:
        samples, rate = kokoro.create(s["say"], voice=voice, speed=speed, lang="en-us")
        samples = np.concatenate([samples, np.zeros(int(rate * PAD), dtype=samples.dtype)])
        s["dur"] = len(samples) / rate
        audio.append(samples)
    sf.write(f"{WORK}/voice.wav", np.concatenate(audio), rate)

    fallback = None
    for i, s in enumerate(scenes):
        s["file"] = fetch_clip(s["clip"], f"clip{i}") if s.get("clip") else None
        if s.get("clip") and not s["file"]:
            print(f"::warning::could not fetch the clip for \"{s['big']}\"; using the title clip instead")
        fallback = fallback or s["file"]
    if not fallback:
        fail("no clip could be downloaded")

    mascot = Image.open(os.path.join(HERE, "..", "drbeetroot", "assets", "mascot.jpg")).convert("RGB").resize((150, 150), Image.LANCZOS)
    parts = []
    for i, s in enumerate(scenes):
        overlay(s["big"], s.get("sub", ""), s["number"], mascot).save(f"{WORK}/ov{i}.png")
        part = f"{WORK}/part{i}.mp4"
        frames = int(s["dur"] * FPS) + 1
        # Slow sideways drift so even a still-looking clip has movement.
        run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", s["file"] or fallback,
             "-i", f"{WORK}/ov{i}.png", "-filter_complex",
             f"[0:v]scale=1188:2112,zoompan=z='1':d=1:s={W}x{H}:x='54-54*on/{frames}':y=96:fps={FPS}[b];[b][1:v]overlay=0:0,format=yuv420p",
             "-t", f"{s['dur']:.3f}", "-r", str(FPS), "-c:v", "libx264", "-crf", "19", "-preset", "fast", part])
        parts.append(part)
    with open(f"{WORK}/list.txt", "w") as f:
        f.write("\n".join(f"file '{os.path.abspath(p)}'" for p in parts))
    run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{WORK}/list.txt",
         "-i", f"{WORK}/voice.wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out])
    note(f"Built {out}: {sum(s['dur'] for s in scenes):.1f} seconds, {len(scenes)} scenes")


if __name__ == "__main__":
    main()
