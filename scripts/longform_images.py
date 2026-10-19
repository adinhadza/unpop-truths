#!/usr/bin/env python3
"""Free scene pictures for long-form episodes.
Reads a scenes JSON ({"style": "...", "character": "...", "scenes": [{"id": "01", "picture": "..."}]})
and saves one 16:9 picture per scene. Uses Pollinations (free, no key). If CF_ACCOUNT_ID and
CF_API_TOKEN are set, Cloudflare Workers AI (free daily allowance) is used as a fallback.
usage: longform_images.py scenes.json out_dir [--only 01,02] [--width 1344 --height 768]"""
import argparse, json, os, sys, time, urllib.parse, urllib.request, urllib.error, base64

ap = argparse.ArgumentParser()
ap.add_argument("scenes"); ap.add_argument("out")
ap.add_argument("--only", default="")
ap.add_argument("--width", type=int, default=1344); ap.add_argument("--height", type=int, default=768)
a = ap.parse_args()
job = json.load(open(a.scenes))
os.makedirs(a.out, exist_ok=True)
only = set(x.strip() for x in a.only.split(",") if x.strip())

def prompt_for(s):
    parts = [job.get("style", ""), s["picture"]]
    if job.get("character") and s.get("has_character", True):
        parts.append(job["character"])
    parts.append(job.get("suffix", "No text, no letters, no words, no logos, no watermark."))
    return " ".join(p.strip() for p in parts if p)

def pollinations(p, seed):
    url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(p)
           + f"?width={a.width}&height={a.height}&model=flux&nologo=true&private=true&seed={seed}")
    req = urllib.request.Request(url, headers={"User-Agent": "longform-builder"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
        if not r.headers.get("Content-Type", "").startswith("image/"):
            raise RuntimeError("not an image: " + r.headers.get("Content-Type", ""))
        return data

def cloudflare(p, seed):
    acc, tok = (os.environ.get("CF_ACCOUNT_ID") or "").strip(), "".join((os.environ.get("CF_API_TOKEN") or "").split())
    if tok.lower().startswith("bearer"): tok = tok[6:]
    if not (acc and tok):
        raise RuntimeError("no Cloudflare key")
    model = os.environ.get("CF_IMAGE_MODEL", "@cf/black-forest-labs/flux-2-klein-4b")
    fields = {"prompt": p[:2000], "width": str(a.width), "height": str(a.height), "seed": str(seed)}
    boundary = "----lf%d" % seed
    body = b"".join(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in fields.items())
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/{model}", data=body,
        headers={"Authorization": f"Bearer {tok}", "Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read(); ctype = r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]!r}")
    if ctype.startswith("image/"):
        return raw
    j = json.loads(raw)
    img = (j.get("result") or {}).get("image") or j.get("image")
    if not img:
        raise RuntimeError("no image in reply: " + raw[:300].decode(errors="ignore"))
    return base64.b64decode(img)

fails = []
for n, s in enumerate(job["scenes"]):
    sid = str(s["id"])
    if only and sid not in only:
        continue
    dst = os.path.join(a.out, f"{sid}.jpg")
    p = prompt_for(s); seed = int(s.get("seed", 1000 + n))
    ok = False
    for attempt in range(4):
        for src in ((cloudflare,) if os.environ.get('CF_API_TOKEN') else (pollinations,)):
            try:
                data = src(p, seed + attempt)
                if len(data) < 20000:
                    raise RuntimeError(f"too small ({len(data)} bytes)")
                open(dst, "wb").write(data)
                print(f"{sid}: ok via {src.__name__} ({len(data)//1024} KB)", flush=True)
                ok = True; break
            except Exception as e:
                print(f"{sid}: {src.__name__} failed: {e}", flush=True)
        if ok: break
        time.sleep(15 * (attempt + 1))
    if not ok:
        fails.append(sid)
    time.sleep(1 if os.environ.get('CF_API_TOKEN') else 6)
print("failed:", fails)
sys.exit(1 if fails else 0)
