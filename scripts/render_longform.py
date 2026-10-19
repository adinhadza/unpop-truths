#!/usr/bin/env python3
"""Build a long-form 16:9 episode: one picture per scene, slow zoom-out timed to that scene's
narration, soft crossfades, word-group captions, big on-screen numbers, quiet music, end card.

usage: render_longform.py scenes.json IMG_DIR VOICE_DIR OUT.mp4 [--music track.m4a] [--brand "PAGE NAME"]
       [--endcard img] [--cta-at 15] [--only 01,02,...] [--fast]
IMG_DIR has <id>.jpg, VOICE_DIR has <id>.m4a|.wav (from longform_voice.py).

The zoom is drawn frame by frame with OpenCV at sub-pixel precision (ffmpeg's zoompan snaps to
whole pixels, which made it shake). Needs: pip install opencv-python-headless numpy pillow
--cta-at N inserts the "Like, share & follow" cut-scene at the first scene break from about N seconds
(0 = off; skipped automatically with --only)."""
import argparse, json, os, subprocess, tempfile, textwrap, shutil, sys
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cta_cutscene import make_cutscene

ap = argparse.ArgumentParser()
ap.add_argument("scenes"); ap.add_argument("img"); ap.add_argument("voice"); ap.add_argument("out")
ap.add_argument("--music", default=""); ap.add_argument("--brand", default="")
ap.add_argument("--endcard", default="", help="1920x1080 image used as the end card")
ap.add_argument("--cta-at", type=float, default=15.0, help="seconds; 0 disables the follow cut-scene")
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

# ---- trim a plain paper/white border some image models paint around the picture ----------
def trim_border(im, tol=14, max_frac=0.12):
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.int16)
    h, w = g.shape
    def plain(line, ref):
        return np.abs(line - ref).mean() < tol and line.std() < tol
    edges = {}
    for side in ("top", "bottom", "left", "right"):
        lim = int((h if side in ("top", "bottom") else w) * max_frac); n = 0
        ref = {"top": g[0], "bottom": g[-1], "left": g[:, 0], "right": g[:, -1]}[side].mean()
        if ref < 170:                              # only light paper/white borders, never dark sky
            edges[side] = 0; continue
        while n < lim:
            line = {"top": g[n], "bottom": g[h - 1 - n], "left": g[:, n], "right": g[:, w - 1 - n]}[side]
            if not plain(line, ref):
                break
            n += 1
        edges[side] = n + (3 if n else 0)          # a few px more to lose the ink outline
    t, b, l, r = edges["top"], edges["bottom"], edges["left"], edges["right"]
    if sum(1 for v in (t, b, l, r) if v) < 3:     # a real frame goes round the picture
        return im
    return im[t:h - b, l:w - r]

# ---- smooth zoom-out ---------------------------------------------------------------------
def smooth_zoom(img, frames, zstart, vf, out):
    """Zoom from zstart to 1.0 over `frames`, centred. Each frame is one affine resample of the
    original picture with float scale/offset, so the motion has no whole-pixel steps."""
    src = trim_border(cv2.imread(img, cv2.IMREAD_COLOR))
    sh, sw = src.shape[:2]
    cover = max(W / sw, H / sh)                 # fill 16:9 (1344x768 is a hair wider)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-vf", vf, "-frames:v", str(frames), "-c:v", "libx264",
                           "-preset", "veryfast", "-crf", "16", "-r", str(FPS), out],
                          stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    interp = cv2.INTER_LINEAR if a.fast else cv2.INTER_CUBIC
    for f in range(frames):
        p = f / max(1, frames - 1)
        z = zstart ** (1 - p)                   # geometric: same visual speed from start to end
        k = cover * z
        M = np.float32([[k, 0, W / 2 - k * sw / 2], [0, k, H / 2 - k * sh / 2]])
        fr = cv2.warpAffine(src, M, (W, H), flags=interp, borderMode=cv2.BORDER_REFLECT)
        try:
            ff.stdin.write(fr.tobytes())
        except BrokenPipeError:
            break
    ff.stdin.close()
    err = ff.stderr.read().decode()
    if ff.wait():
        raise SystemExit("ffmpeg failed on " + out + "\n" + err[-1500:])

# ---- 1. one clip per scene -------------------------------------------------------------
clips, durs, voices, lead = [], [], [], 0.25
for i, s in enumerate(scenes):
    sid = s["id"]
    v = voice_file(sid); vd = dur(v)
    hook = i < 6 and not only
    d = round(vd + (0.15 if hook else 0.45) + lead + XF, 3)   # audio plus breathing room plus overlap
    frames = int(d * FPS)
    img = os.path.join(a.img, sid + ".jpg")
    zstart = 1.18 if hook else 1.12
    vf = ["eq=saturation=1.05:contrast=1.03"]
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
    vf.append("format=yuv420p")
    out = os.path.join(tmp, f"v_{sid}.mp4")
    smooth_zoom(img, frames, zstart, ",".join(vf), out)
    clips.append(out); durs.append(d); voices.append(v)
    print(f"scene {sid}: {d:.1f}s", flush=True)

# ---- 1b. "like, share & follow" cut-scene at the first scene break from ~--cta-at seconds ---
#      (never earlier, so it lands at a sentence-group end like the end of the cold open)
if a.cta_at > 0 and not only and len(clips) > 2:
    t, k = 0.0, len(durs) - 2
    for i, dd in enumerate(durs[:-1]):
        t += dd - XF
        if t >= a.cta_at:
            k = i; break
    cta = os.path.join(tmp, "cta.mp4")
    cd = make_cutscene(cta)
    clips.insert(k + 1, cta); durs.insert(k + 1, cd); voices.insert(k + 1, None)
    print(f"cut-scene after scene {scenes[k]['id']} (~{sum(durs[:k+1]) - XF*(k+1):.1f}s)", flush=True)

# ---- 2. end card --------------------------------------------------------------------------
if a.endcard:
    ec = os.path.join(tmp, "end.mp4"); ed = 4.0
    smooth_zoom(a.endcard, int(ed*FPS), 1.06, "fade=t=in:d=0.5,format=yuv420p", ec)
    clips.append(ec); durs.append(ed); voices.append(None)
elif a.brand:
    ec = os.path.join(tmp, "end.mp4"); ed = 4.0
    t1 = os.path.join(tmp, "e1.txt"); open(t1, "w").write(a.brand.upper())
    t2 = os.path.join(tmp, "e2.txt"); open(t2, "w").write("Follow for the next story")
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x0B1324:s={W}x{H}:r={FPS}:d={ed}",
         "-vf", f"drawtext=fontfile={FB}:textfile={t1}:fontsize=96:fontcolor=0xFFC94A:x=(w-text_w)/2:y=h*0.40,"
                f"drawtext=fontfile={FB}:textfile={t2}:fontsize=48:fontcolor=white:x=(w-text_w)/2:y=h*0.55,"
                f"fade=t=in:d=0.5,format=yuv420p", "-c:v", "libx264", "-crf", "20", ec])
    clips.append(ec); durs.append(ed); voices.append(None)

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
ainputs, amix, start, na = [], [], 0.0, 0
for i, vpath in enumerate(voices):
    if vpath:
        ainputs += ["-i", vpath]
        ms = int((start + lead) * 1000)
        amix.append(f"[{na}:a]aresample=48000,adelay={ms}:all=1[a{na}]")
        na += 1
    start += durs[i] - XF
labels = "".join(f"[a{i}]" for i in range(na))
amix.append(f"{labels}amix=inputs={na}:normalize=0,apad,atrim=0:{total:.3f},loudnorm=I=-16:TP=-1.5[nar]")
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
