#!/usr/bin/env python3
"""Behind the Billions "Like, share & follow" cut-scene (16:9, ~4 s, silent).

Logo pops in, the page name rises under it, LIKE / SHARE / FOLLOW pop in one by one, then a
FOLLOW button gets tapped: it fills gold, turns into FOLLOWING and a checkmark draws itself.
Frames are drawn with PIL at 2x and scaled down, so every edge and motion is smooth.

usage: cta_cutscene.py OUT.mp4 [--logo btb-profile.png] [--fonts DIR] [--seconds 4.0]
Also importable: make_cutscene(out, logo, fonts, seconds) -> duration."""
import argparse, math, os, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, SS = 1920, 1080, 30, 2          # SS = supersampling factor
BG = (5, 7, 12)                              # #05070C, same as the logo background
GOLD = (232, 185, 74)                        # #E8B94A
CREAM = (244, 238, 226)                      # #F4EEE2
HERE = os.path.dirname(os.path.abspath(__file__))


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, length):
    return clamp((t - start) / length)


def ease_out(p):                             # cubic ease-out
    return 1 - (1 - p) ** 3


def ease_back(p, s=1.6):                     # overshoot then settle ("pop")
    p -= 1
    return p * p * ((s + 1) * p + s) + 1


def lerp(a, b, p):
    return tuple(int(round(a[i] + (b[i] - a[i]) * p)) for i in range(len(a)))


def paste_scaled(base, im, cx, cy, scale, alpha):
    if scale <= 0.01 or alpha <= 0.003:
        return
    w, h = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    s = im.resize((w, h), Image.LANCZOS)
    if alpha < 1:
        a = s.getchannel("A").point(lambda v: int(v * alpha))
        s.putalpha(a)
    base.alpha_composite(s, (int(cx - w / 2), int(cy - h / 2)))


def text_sprite(txt, font, fill, spacing=0):
    """Text on a transparent sprite, letter-spaced, tightly cropped."""
    widths = [font.getlength(c) for c in txt]
    tw = int(sum(widths) + spacing * (len(txt) - 1)) + 8
    asc, desc = font.getmetrics()
    im = Image.new("RGBA", (tw, asc + desc + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 4
    for c, w in zip(txt, widths):
        d.text((x, 4), c, font=font, fill=fill)
        x += w + spacing
    return im


def glow(radius, color, strength):
    """Soft round glow sprite (drawn small, blurred, scaled up)."""
    n = 256
    g = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse((n * 0.3, n * 0.3, n * 0.7, n * 0.7), fill=color + (int(255 * strength),))
    g = g.filter(ImageFilter.GaussianBlur(n * 0.13))
    return g.resize((radius * 2, radius * 2), Image.BICUBIC)


def draw_check(d, cx, cy, size, p, width, fill):
    """Checkmark drawn progressively (p = 0..1 of its total stroke length)."""
    pts = [(cx - 0.42 * size, cy + 0.02 * size), (cx - 0.12 * size, cy + 0.32 * size), (cx + 0.45 * size, cy - 0.30 * size)]
    segs = [(pts[0], pts[1]), (pts[1], pts[2])]
    lens = [math.dist(a, b) for a, b in segs]
    left = p * sum(lens)
    r = width / 2
    for (a, b), L in zip(segs, lens):
        if left <= 0:
            break
        f = min(1, left / L)
        e = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        d.line([a, e], fill=fill, width=int(width))
        for q in (a, e):
            d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=fill)
        left -= L


def make_cutscene(out, logo=None, fonts=None, seconds=4.0):
    logo = logo or os.path.join(HERE, "..", "assets", "behind-the-billions", "btb-profile.png")
    fonts = fonts or os.path.join(HERE, "..", "assets", "fonts")
    S = SS
    fb = lambda px: ImageFont.truetype(os.path.join(fonts, "Poppins-Bold.ttf"), px * S)

    # --- sprites (all at supersampled size) ---
    lg = Image.open(logo).convert("RGBA")
    # crop to the keyhole + its glow and fade the square edges into the background
    m = Image.new("L", lg.size, 0)
    ImageDraw.Draw(m).ellipse((40, 40, lg.width - 40, lg.height - 40), fill=255)
    lg.putalpha(m.filter(ImageFilter.GaussianBlur(60)))
    logo_px = 470 * S
    lg = lg.resize((logo_px, logo_px), Image.LANCZOS)

    name = text_sprite("BEHIND THE BILLIONS", fb(74), GOLD, spacing=5 * S)
    words = [text_sprite(w, fb(40), CREAM, spacing=6 * S) for w in ("LIKE", "SHARE", "FOLLOW")]
    dot = text_sprite("•", fb(40), GOLD)
    btn_follow = text_sprite("+  FOLLOW", fb(40), GOLD, spacing=4 * S)
    btn_following = text_sprite("FOLLOWING", fb(40), BG, spacing=4 * S)
    halo = glow(700 * S, GOLD, 0.16)

    # --- layout (supersampled coords) ---
    cxs = W * S / 2
    logo_y = 300 * S
    name_y = 590 * S
    words_y = 690 * S
    btn_y, btn_w, btn_h = 850 * S, 470 * S, 104 * S
    gap = 46 * S
    row_w = sum(w.width for w in words) + 2 * (dot.width + 2 * gap)
    xs, x = [], cxs - row_w / 2
    for i, w in enumerate(words):
        xs.append(x + w.width / 2)
        x += w.width
        if i < 2:
            xs.append(x + gap + dot.width / 2)
            x += 2 * gap + dot.width

    n = int(round(seconds * FPS))
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", "-r", str(FPS), out], stdin=subprocess.PIPE)
    TAP = 2.25                                     # moment the button is tapped
    for f in range(n):
        t = f / FPS
        im = Image.new("RGBA", (W * S, H * S), BG + (255,))
        # breathing halo behind the logo
        ha = 0.55 + 0.45 * ease_out(prog(t, 0, 0.8))
        paste_scaled(im, halo, cxs, logo_y, 1.0 + 0.04 * math.sin(t * 2.2), ha)
        # logo pop + slow drift up
        p = prog(t, 0.0, 0.7)
        paste_scaled(im, lg, cxs, logo_y - 10 * S * ease_out(prog(t, 0.7, 3.0)),
                     0.55 + 0.45 * ease_back(p), ease_out(clamp(p * 1.6)))
        # page name rises
        p = ease_out(prog(t, 0.45, 0.6))
        paste_scaled(im, name, cxs, name_y + (1 - p) * 40 * S, 1.0, p)
        # LIKE • SHARE • FOLLOW pop one by one
        items = [words[0], dot, words[1], dot, words[2]]
        starts = [1.0, 1.15, 1.25, 1.4, 1.5]
        for it, xx, st in zip(items, xs, starts):
            p = prog(t, st, 0.4)
            paste_scaled(im, it, xx, words_y, 0.6 + 0.4 * ease_back(p), clamp(p * 2))
        # FOLLOW button: appears, gets pressed, fills, check draws
        p_in = prog(t, 1.65, 0.45)
        if p_in > 0:
            press = math.sin(math.pi * prog(t, TAP - 0.12, 0.24))      # quick squish around the tap
            fill_p = ease_out(prog(t, TAP, 0.3))
            pop = 1 + 0.07 * math.sin(math.pi * prog(t, TAP + 0.05, 0.35))
            sc = (0.7 + 0.3 * ease_back(p_in)) * (1 - 0.06 * press) * pop
            a = clamp(p_in * 2)
            layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            bw, bh = btn_w * sc, btn_h * sc
            box = (cxs - bw / 2, btn_y - bh / 2, cxs + bw / 2, btn_y + bh / 2)
            d.rounded_rectangle(box, radius=bh / 2, fill=GOLD + (int(255 * fill_p),),
                                outline=GOLD + (255,), width=int(5 * S * sc))
            # tap ripple
            rp = prog(t, TAP, 0.6)
            if 0 < rp < 1:
                rr = bh * (0.25 + 0.75 * ease_out(rp))
                d.ellipse((cxs + bw * 0.18 - rr, btn_y - rr, cxs + bw * 0.18 + rr, btn_y + rr),
                          outline=CREAM + (int(150 * (1 - rp)),), width=int(4 * S))
            # label: "+ FOLLOW" cross-fades to check + "FOLLOWING"
            lab = Image.new("RGBA", im.size, (0, 0, 0, 0))
            paste_scaled(lab, btn_follow, cxs, btn_y, sc, 1 - prog(t, TAP, 0.1))
            if fill_p > 0:
                tw = btn_following.width * sc
                ck = 52 * S * sc
                total = ck + 22 * S * sc + tw
                left = cxs - total / 2
                paste_scaled(lab, btn_following, left + ck + 22 * S * sc + tw / 2, btn_y, sc, prog(t, TAP + 0.08, 0.2))
                draw_check(ImageDraw.Draw(lab), left + ck / 2, btn_y, ck, ease_out(prog(t, TAP + 0.1, 0.4)),
                           11 * S * sc, BG + (255,))
            layer.alpha_composite(lab)
            if a < 1:
                layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
            im.alpha_composite(layer)
        # gentle fade-in from black (the crossfade in the episode does the rest)
        frame = im.convert("RGB").resize((W, H), Image.LANCZOS)
        fi = ease_out(prog(t, 0, 0.25))
        if fi < 1:
            frame = Image.blend(Image.new("RGB", (W, H), BG), frame, fi)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    if ff.wait():
        raise SystemExit("ffmpeg failed while writing the cut-scene")
    return n / FPS


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--logo"); ap.add_argument("--fonts")
    ap.add_argument("--seconds", type=float, default=4.0)
    a = ap.parse_args()
    print(f"cut-scene: {make_cutscene(a.out, a.logo, a.fonts, a.seconds):.2f}s -> {a.out}")
