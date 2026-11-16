import subprocess, math, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

UP = '/root/.claude/uploads/42ed5d36-5767-587d-83b9-7655974e4434/'
V1 = UP + 'd68d6f8f-20261112_131030.mp4'   # puerta, góndolas, mostrador
V2 = UP + '7d5cafcb-20261112_131136.mp4'   # recorrido completo
V3 = UP + '276cc5f0-20261112_131133.mp4'   # estante gatos
FONT = 'fonts/Fredoka.ttf'
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
W, H, FPS = 1080, 1920, 30
END = 15.0

ORANGE = (255, 138, 0); YELLOW = (255, 214, 64); TEAL = (20, 178, 165)
PINK = (255, 84, 140); PURPLE = (108, 63, 209); WHITE = (255, 255, 255); DARK = (40, 22, 60)

random.seed(3)

# ---------------- helpers ----------------
def font(size, wght=700, wdth=100):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([wght, wdth])
    return f

_emo = ImageFont.truetype(EMOJI, 109)
_ecache = {}
def emoji(ch, size):
    key = (ch, size)
    if key not in _ecache:
        im = Image.new('RGBA', (300, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10, 10), ch, font=_emo, embedded_color=True)
        im = im.crop(im.getbbox())
        r = size / max(im.size)
        _ecache[key] = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    return _ecache[key]

def text_sprite(txt, size, fill=WHITE, stroke=DARK, sw=None, wght=700, shadow=True):
    f = font(size, wght)
    sw = sw if sw is not None else max(4, size // 9)
    d = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    l, t, r, b = d.textbbox((0, 0), txt, font=f, stroke_width=sw)
    pad = 24
    im = Image.new('RGBA', (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    if shadow:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + 6, pad - t + 10), txt, font=f, fill=(0, 0, 0, 120),
                                stroke_width=sw, stroke_fill=(0, 0, 0, 120))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(6)))
        dr = ImageDraw.Draw(im)
    dr.text((pad - l, pad - t), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
    return im

def pill(content, bg, pad=(46, 26), radius=None, outline=WHITE, ow=6):
    """content: list of sprites placed in a row"""
    gap = 14
    w = sum(c.width for c in content) + gap * (len(content) - 1) + pad[0] * 2
    h = max(c.height for c in content) + pad[1] * 2
    radius = radius or h // 2
    sh = 14
    im = Image.new('RGBA', (w + sh * 2, h + sh * 2 + 10), (0, 0, 0, 0))
    shadow = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((sh, sh + 10, sh + w, sh + h + 10), radius, fill=(0, 0, 0, 110))
    im = Image.alpha_composite(im, shadow.filter(ImageFilter.GaussianBlur(9)))
    ImageDraw.Draw(im).rounded_rectangle((sh, sh, sh + w, sh + h), radius, fill=bg + (255,), outline=outline, width=ow)
    x = sh + pad[0]
    for c in content:
        im.alpha_composite(c, (x, sh + (h - c.height) // 2))
        x += c.width + gap
    return im

def card(w, h, top, bottom, radius=60, outline=WHITE):
    im = Image.new('RGBA', (w + 60, h + 80), (0, 0, 0, 0))
    shadow = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((30, 50, 30 + w, 50 + h), radius, fill=(0, 0, 0, 140))
    im = Image.alpha_composite(im, shadow.filter(ImageFilter.GaussianBlur(16)))
    grad = Image.new('RGBA', (w, h))
    g = np.zeros((h, w, 4), np.uint8)
    k = np.linspace(0, 1, h)[:, None]
    for c in range(3):
        g[..., c] = (np.array(top[c]) * (1 - k) + np.array(bottom[c]) * k).astype(np.uint8)
    g[..., 3] = 240
    grad = Image.fromarray(g, 'RGBA')
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=255)
    body = Image.new('RGBA', (w, h), (0, 0, 0, 0)); body.paste(grad, (0, 0), mask)
    im.alpha_composite(body, (30, 30))
    ImageDraw.Draw(im).rounded_rectangle((30, 30, 30 + w, 30 + h), radius, outline=outline, width=10)
    return im

# easing
def clamp(x, a=0, b=1): return max(a, min(b, x))
def ease_out_back(x, s=1.9):
    x = clamp(x); x -= 1
    return x * x * ((s + 1) * x + s) + 1
def ease_out_elastic(x):
    x = clamp(x)
    if x in (0, 1): return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi) / 3) + 1
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in(x): x = clamp(x); return x ** 3

_rcache = {}
def place(frame, spr, cx, cy, scale=1.0, rot=0.0, alpha=1.0, flip=False):
    if scale <= 0.01 or alpha <= 0.01:
        return
    key = (id(spr), round(scale, 3), round(rot, 1), flip)
    im = _rcache.get(key)
    if im is None:
        im = spr.transpose(Image.FLIP_LEFT_RIGHT) if flip else spr
        if abs(scale - 1) > 0.002:
            im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
        if abs(rot) > 0.05:
            im = im.rotate(rot, Image.BICUBIC, expand=True)
        if len(_rcache) > 4000:
            _rcache.clear()
        _rcache[key] = im
    if alpha < 0.999:
        im = im.copy()
        a = im.getchannel('A').point(lambda v: int(v * alpha))
        im.putalpha(a)
    x = int(cx - im.width / 2); y = int(cy - im.height / 2)
    frame.alpha_composite(im, (x, y)) if (x >= 0 and y >= 0 and x + im.width <= W and y + im.height <= H) \
        else _safe_composite(frame, im, x, y)

def _safe_composite(frame, im, x, y):
    l, t = max(0, -x), max(0, -y)
    r, b = min(im.width, W - x), min(im.height, H - y)
    if r <= l or b <= t: return
    frame.alpha_composite(im.crop((l, t, r, b)), (x + l, y + t))

def pop_in(t, t0, dur=0.45):
    return ease_out_back((t - t0) / dur) if t >= t0 else 0.0

# ---------------- video sources ----------------
class Clip:
    def __init__(self, path, ss, dur, blur=0, speed=1.0, dim=0.0):
        vf = f'setpts=PTS/{speed},fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},eq=saturation=1.22:contrast=1.06:brightness=0.02'
        if blur:
            vf += f',gblur=sigma={blur}'
        self.n = int(round(dur * FPS))
        self.dim = dim
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(ss), '-i', path, '-vf', vf,
                                   '-frames:v', str(self.n), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                  stdout=subprocess.PIPE)
        self.last = None
    def frame(self):
        buf = self.p.stdout.read(W * H * 3)
        if len(buf) == W * H * 3:
            arr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            if self.dim:
                arr = (arr * (1 - self.dim)).astype(np.uint8)
            self.last = Image.fromarray(arr).convert('RGBA')
        return self.last.copy()

