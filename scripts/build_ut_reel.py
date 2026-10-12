#!/usr/bin/env python3
"""Build one Unpopular Truths Reel (approved format, 12 Oct 2026).

3 still illustrations, slow push-in, film grain + dust, vignette,
one handwritten line at a time synced to the voice, calm music under it.

usage: build_ut_reel.py --images a.jpg b.jpg c.jpg --voice voice.mp3 \
         --lines lines.txt --music music/calm/float.m4a --out reel.mp4
lines.txt: one spoken line per row (normally 6 = 2 per picture), in the same
order and with the same pauses as the voice recording.
"""
import argparse, os, re, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "assets", "fonts", "caveat.ttf")
DELAY = 0.4      # voice starts 0.4 s in
TAIL = 2.0       # picture holds 2 s after the last word


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-3000:])
    return r


MIN_LEN = 11.0  # seconds; Facebook Reels for this page must be 10 s+


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "csv=p=0", path]).stdout
    return float(out.strip())


def line_starts(voice, lines):
    """Start time (in the voice file) of each spoken line. Picks the set of
    pauses whose speech chunks best match the relative length of each line
    (the narrator sometimes pauses inside a line too)."""
    import itertools
    n = len(lines)
    err = run(["ffmpeg", "-hide_banner", "-i", voice, "-af",
               "silencedetect=noise=-35dB:d=0.2", "-f", "null", "-"]).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", err)]
    vlen = duration(voice)
    gaps = [(s, e) for s, e in zip(starts, ends) if s > 0.3 and e < vlen - 0.3]
    if len(gaps) < n - 1:
        raise SystemExit(f"voice has only {len(gaps)} pauses for {n} lines")
    tail = [s for s in starts if s >= vlen - 0.3 or s > max([g[1] for g in gaps] or [0])]
    speech_end = min(tail) if tail else vlen
    weights = [len(l.replace(" ", "")) for l in lines]
    tw = sum(weights)
    best = None
    for combo in itertools.combinations(gaps, n - 1):
        b = [0.0] + [g[1] for g in combo] + [speech_end]
        segs = []
        for i in range(n):
            end = combo[i][0] if i < n - 1 else speech_end
            segs.append(end - b[i])
        total = sum(segs)
        err_ = sum((sg / total - w / tw) ** 2 for sg, w in zip(segs, weights))
        err_ -= 0.002 * sum(g[1] - g[0] for g in combo)   # prefer longer pauses
        if best is None or err_ < best[0]:
            best = (err_, [0.0] + [g[1] for g in combo])
    return best[1]


def esc(path):
    return path.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", nargs="+", required=True)
    ap.add_argument("--voice", required=True)
    ap.add_argument("--lines", required=True)
    ap.add_argument("--music")
    ap.add_argument("--music-start", type=float, default=8.0)
    ap.add_argument("--handle", default="@unpopulartruths")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    lines = [l.strip() for l in open(a.lines, encoding="utf-8") if l.strip()]
    imgs = a.images
    if len(lines) % len(imgs):
        raise SystemExit("number of lines must be a multiple of number of images")
    per = len(lines) // len(imgs)
    vlen = duration(a.voice)
    total = round(DELAY + vlen + TAIL, 2)
    # Reels must be at least 10 s: hold the last frame/line longer if the voice is short.
    total = max(total, MIN_LEN)
    st = [t + DELAY if i else 0.0 for i, t in enumerate(line_starts(a.voice, lines))]
    st = [round(x - (0.1 if i else 0), 2) for i, x in enumerate(st)]
    ends = st[1:] + [total]
    img_cut = [st[i * per] for i in range(len(imgs))] + [total]

    tmp = tempfile.mkdtemp()
    segs = []
    for i, img in enumerate(imgs):
        d = img_cut[i + 1] - img_cut[i]
        frames = int(round(d * 30))
        seg = os.path.join(tmp, f"seg{i}.mp4")
        vf = ("scale=1440:-2,crop=1440:2560,"
              "zoompan=z='1+0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
              f":d=1:s=720x1280:fps=30,eq=saturation=0.9:contrast=1.03,"
              "noise=alls=14:allf=t+u,vignette=PI/5,format=yuv420p")
        run(["ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", img,
             "-vf", vf, "-frames:v", str(frames), "-c:v", "libx264",
             "-crf", "16", "-preset", "fast", seg])
        segs.append(seg)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{s}'\n" for s in segs)
    base = os.path.join(tmp, "base.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base])

    draws = []
    for i, line in enumerate(lines):
        tf = os.path.join(tmp, f"l{i}.txt")
        open(tf, "w", encoding="utf-8").write(line)
        draws.append(
            f"drawtext=fontfile='{esc(FONT)}':textfile='{esc(tf)}':fontsize=46:"
            f"fontcolor=white@0.95:x=(w-text_w)/2:y=h*0.47-text_h/2:"
            f"borderw=1:bordercolor=black@0.35:shadowcolor=black@0.6:shadowx=2:shadowy=2:"
            f"enable='between(t,{st[i]:.2f},{ends[i] - 0.02:.2f})'")
    hf = os.path.join(tmp, "h.txt")
    open(hf, "w").write(a.handle)
    draws.append(f"drawtext=fontfile='{esc(FONT)}':textfile='{esc(hf)}':fontsize=26:"
                 "fontcolor=white@0.7:x=(w-text_w)/2:y=h*0.80")

    fc = (f"nullsrc=s=180x320:r=6:d={total},"
          "geq=lum='if(gt(random(1)\\,0.9993)\\,255\\,0)':cb=128:cr=128,"
          "scale=720:1280:flags=bilinear,gblur=sigma=1.2,fps=30,format=gbrp[dust];"
          # soft dark band behind the text so it stays readable on bright pictures
          "color=black:s=720x240:r=30,format=yuva444p,"
          "geq=lum=16:cb=128:cr=128:a='95*exp(-pow((Y-120)/62\\,2))'[band];"
          "[0:v]format=gbrp[v0];[v0][dust]blend=all_mode=screen:all_opacity=0.3,format=yuv444p[vd];"
          "[vd][band]overlay=0:H*0.47-120:shortest=1,"
          + ",".join(draws) + ",format=yuv420p[v];"
          f"[1:a]adelay={int(DELAY*1000)}:all=1,apad,loudnorm=I=-16:TP=-1.5[vo]")
    inputs = ["-i", base, "-i", a.voice]
    if a.music:
        inputs += ["-ss", str(a.music_start), "-i", a.music]
        fc += (f";[2:a]loudnorm=I=-30:TP=-6,afade=t=in:d=0.6,"
               f"afade=t=out:st={total - 1.8:.2f}:d=1.8[mu];"
               "[vo][mu]amix=inputs=2:duration=longest:normalize=0[a]")
    else:
        fc += ";[vo]anull[a]"
    run(["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[v]",
         "-map", "[a]", "-t", str(total), "-c:v", "libx264", "-preset", "slow",
         "-b:v", "3500k", "-maxrate", "4500k", "-bufsize", "9M",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
         "-movflags", "+faststart", a.out])
    print(f"built {a.out}: {total}s, lines at {st}, image cuts at {img_cut}")


if __name__ == "__main__":
    main()
