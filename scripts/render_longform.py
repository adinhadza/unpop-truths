#!/usr/bin/env python3
"""Build a long-form 16:9 episode: one picture per scene, slow zoom-out timed to that scene's
narration, soft crossfades, word-group captions, big on-screen numbers, quiet music, end card.

usage: render_longform.py scenes.json IMG_DIR VOICE_DIR OUT.mp4 [--music track.m4a] [--brand "PAGE NAME"]
       [--only 01,02,...] [--fast]
IMG_DIR has <id>.jpg, VOICE_DIR has <id>.m4a|.wav (from longform_voice.py)."""
import argparse, json, os, subprocess, tempfile, textwrap, shutil

ap = argparse.ArgumentParser()
ap.add_argument("scenes"); ap.add_argument("img"); ap.add_argument("voice"); ap.add_argument("out")
ap.add_argument("--music", default=""); ap.add_argument("--brand", default="")
ap.add_argument("--endcard", default="", help="1920x1080 image used as the end card")
ap.add_argument("--only", default=""); ap.add_argument("--fast", action="store_true")
ap.add_argument("--fonts", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts"))
a = ap.parse_args()

W, H, FPS = 1920, 1080, 30
XF = 0.4                       # crossfade seconds
FB = os.path.join(a.fonts, "Poppins-Bold.ttf")
job = json.load(open(a.scenes))
only = set(x.strip() for x in a.only.split(",") if x.strip())
scenes = [s for s in job["scenes"] if not only or s["id"] in only]
tmp = tempfile.mkdtemp(prefix="lf_")

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("ffmpeg failed:\n" + " ".join(cmd)[:600] + "\n" + r.stderr[-1500:])
    return r.stdout

def dur(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).strip())

def voice_file(sid):
    for ext in (".m4a", ".wav", ".mp3"):
        p = os.path.join(a.voice, sid + ext)
        if os.path.exists(p):
            return p
    raise SystemExit(f"missing voice for scene {sid}")

def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%").replace(",", "\\,")

def caption_chunks(text, n_words=6):
    words = text.replace("…", "...").split()
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= n_words or w.endswith((".", "?", "!")) and len(cur) >= 3:
            chunks.append(" ".join(cur)); cur = []
    if cur:
        chunks.append(" ".join(cur))
    return chunks

# ---- 1. one clip per scene -------------------------------------------------------------
clips, durs, lead = [], [], 0.25
for i, s in enumerate(scenes):
    sid = s["id"]
    v = voice_file(sid); vd = dur(v)
    hook = i < 6 and not only
    d = round(vd + (0.15 if hook else 0.45) + lead + XF, 3)   # audio plus breathing room plus overlap
    frames = int(d * FPS)
    img = os.path.join(a.img, sid + ".jpg")
    big = 1.0 if a.fast else 2.0
    zstart = 1.18 if hook else 1.12
    vf = [f"scale={int(W*big*zstart)}:{int(H*big*zstart)}:force_original_aspect_ratio=increase",
          f"crop={int(W*big*zstart)}:{int(H*big*zstart)}",
          f"zoompan=z='{zstart}-({zstart}-1)*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}",
          "eq=saturation=1.05:contrast=1.03", "format=yuv420p"]
    # captions: chunks spread over the narration time, proportional to word count
    chunks = caption_chunks(s["narration"])
    total_w = sum(len(c.split()) for c in chunks)
    t = lead
    for c in chunks:
        cd = vd * len(c.split()) / total_w
        tf = os.path.join(tmp, f"cap_{sid}_{len(vf)}.txt"); open(tf, "w").write(c)
        vf.append(f"drawtext=fontfile={FB}:textfile={tf}:fontsize=50:fontcolor=white:borderw=5:bordercolor=black@0.85:"
                  f"x=(w-text_w)/2:y=h-150:enable='between(t,{t:.2f},{t+cd:.2f})'")
        t += cd
    if s.get("onscreen") and s["onscreen"].upper() != "FOLLOW":
        tf = os.path.join(tmp, f"on_{sid}.txt"); open(tf, "w").write(s["onscreen"])
        show = min(vd + lead, 4.5)
        vf.append(f"drawtext=fontfile={FB}:textfile={tf}:fontsize=120:fontcolor=0xFFC94A:borderw=8:bordercolor=black@0.9:"
                  f"x=(w-text_w)/2:y=h*0.12:enable='between(t,0.15,{show:.2f})':"
                  f"alpha='min(1,(t-0.15)/0.2)'")
    if a.brand:
        vf.append(f"drawtext=fontfile={FB}:text='{esc(a.brand.upper())}':fontsize=26:fontcolor=white@0.85:borderw=2:"
                  f"bordercolor=black@0.6:x=w-text_w-30:y=28")
    out = os.path.join(tmp, f"v_{sid}.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", f"{d}", "-i", img,
         "-vf", ",".join(vf), "-frames:v", str(frames), "-c:v", "libx264", "-preset", "veryfast" if a.fast else "medium",
         "-crf", "20", "-r", str(FPS), out])
    clips.append(out); durs.append(d)
    print(f"scene {sid}: {d:.1f}s", flush=True)

# ---- 2. end card --------------------------------------------------------------------------
if a.endcard:
    ec = os.path.join(tmp, "end.mp4"); ed = 4.0
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", f"{ed}", "-i", a.endcard, "-vf",
         f"scale={W}:{H},zoompan=z='1.06-0.06*on/{int(ed*FPS)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(ed*FPS)}:s={W}x{H}:fps={FPS},fade=t=in:d=0.5,format=yuv420p",
         "-frames:v", str(int(ed*FPS)), "-c:v", "libx264", "-crf", "20", ec])
    clips.append(ec); durs.append(ed)
elif a.brand:
    ec = os.path.join(tmp, "end.mp4"); ed = 4.0
    t1 = os.path.join(tmp, "e1.txt"); open(t1, "w").write(a.brand.upper())
    t2 = os.path.join(tmp, "e2.txt"); open(t2, "w").write("Follow for the next story")
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x0B1324:s={W}x{H}:r={FPS}:d={ed}",
         "-vf", f"drawtext=fontfile={FB}:textfile={t1}:fontsize=96:fontcolor=0xFFC94A:x=(w-text_w)/2:y=h*0.40,"
                f"drawtext=fontfile={FB}:textfile={t2}:fontsize=48:fontcolor=white:x=(w-text_w)/2:y=h*0.55,"
                f"fade=t=in:d=0.5,format=yuv420p", "-c:v", "libx264", "-crf", "20", ec])
    clips.append(ec); durs.append(ed)

# ---- 3. join with crossfades --------------------------------------------------------------
inputs, fc, prev, offset = [], [], "0:v", 0.0
for c in clips:
    inputs += ["-i", c]
for k in range(1, len(clips)):
    offset += durs[k - 1] - XF
    fc.append(f"[{prev}][{k}:v]xfade=transition=fade:duration={XF}:offset={offset:.3f}[x{k}]")
    prev = f"x{k}"
video = os.path.join(tmp, "video.mp4")
if len(clips) == 1:
    shutil.copy(clips[0], video)
else:
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", f"[{prev}]",
         "-c:v", "libx264", "-preset", "veryfast" if a.fast else "medium", "-crf", "20", video])
total = dur(video)

# ---- 4. narration track aligned to the scene starts ----------------------------------------
ainputs, amix, start = [], [], 0.0
for i, s in enumerate(scenes):
    ainputs += ["-i", voice_file(s["id"])]
    ms = int((start + lead) * 1000)
    amix.append(f"[{i}:a]aresample=48000,adelay={ms}:all=1[a{i}]")
    start += durs[i] - XF
labels = "".join(f"[a{i}]" for i in range(len(scenes)))
amix.append(f"{labels}amix=inputs={len(scenes)}:normalize=0,apad,atrim=0:{total:.3f},loudnorm=I=-16:TP=-1.5[nar]")
narr = os.path.join(tmp, "narr.m4a")
run(["ffmpeg", "-v", "error", "-y", *ainputs, "-filter_complex", ";".join(amix), "-map", "[nar]", "-c:a", "aac", "-b:a", "192k", narr])

# ---- 5. music under the voice, then mux -----------------------------------------------------
if a.music:
    fc = (f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{total:.3f},loudnorm=I=-32:TP=-8,"
          f"afade=t=in:d=1.5,afade=t=out:st={max(0, total-3):.2f}:d=3[m];"
          f"[0:a][m]amix=inputs=2:duration=first:normalize=0[aout]")
    run(["ffmpeg", "-v", "error", "-y", "-i", narr, "-i", a.music, "-filter_complex", fc, "-map", "[aout]",
         "-c:a", "aac", "-b:a", "192k", os.path.join(tmp, "mix.m4a")])
    narr = os.path.join(tmp, "mix.m4a")
run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", narr, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
     "-c:a", "copy", "-shortest", "-movflags", "+faststart", a.out])
print(f"done: {a.out} {dur(a.out):.1f}s")
shutil.rmtree(tmp, ignore_errors=True)
