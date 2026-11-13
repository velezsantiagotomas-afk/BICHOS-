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
END = 29.5

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

# segments: (start, end, clip factory, name)
SEGS = [
    (0.0, 4.0, lambda: Clip(V1, 1.6, 4.0), 'intro'),
    (4.0, 7.5, lambda: Clip(V2, 2.0, 3.5), 'cap1'),
    (7.5, 11.0, lambda: Clip(V2, 5.0, 3.5), 'cap2'),
    (11.0, 13.5, lambda: Clip(V3, 0.0, 2.5, speed=0.6), 'cap3'),
    (13.5, 19.0, lambda: Clip(V1, 7.5, 5.5, blur=14, dim=0.25), 'address'),
    (19.0, 25.5, lambda: Clip(V2, 7.0, 6.5, blur=14, dim=0.25, speed=1.0), 'hours'),
    (25.5, END, lambda: Clip(V1, 4.5, END - 25.5 + 0.1, blur=10, dim=0.2), 'outro'),
]

# ---------------- pre-built sprites ----------------
S = {}
S['nuevo'] = text_sprite('¡NUEVO', 190, fill=YELLOW, stroke=PURPLE, sw=16)
S['local'] = text_sprite('LOCAL!', 190, fill=WHITE, stroke=PURPLE, sw=16)
S['forr'] = pill([text_sprite('FORRAJERÍA', 74, fill=WHITE, stroke=DARK, sw=0, shadow=False)], ORANGE)
S['dog'] = emoji('🐶', 230); S['cat'] = emoji('🐱', 230)
S['spark'] = emoji('✨', 110); S['party'] = emoji('🎉', 120)
CONF = ['🐾', '🦴', '💛', '🐾', '⭐', '🧡']
S['conf'] = [emoji(c, 70) for c in CONF]

caps = [
    ('cap1', '🛍️', 'Alimento suelto', 'y por bolsa', TEAL, '🐕'),
    ('cap2', '🦮', 'Correas, ropita', 'y accesorios', PINK, '🐈'),
    ('cap3', '🐱', '¡Todo para', 'perros y gatos!', ORANGE, None),
]
for name, e, l1, l2, col, runner in caps:
    S[name + '_a'] = pill([emoji(e, 96), text_sprite(l1, 76, sw=0, shadow=False)], col)
    S[name + '_b'] = pill([text_sprite(l2, 76, sw=0, shadow=False)], PURPLE)
    S[name + '_run'] = emoji(runner, 170) if runner else None
S['bone'] = emoji('🦴', 80)

# address
S['addr_card'] = card(940, 860, (255, 255, 255), (255, 241, 210), outline=ORANGE)
S['pin'] = emoji('📍', 210)
S['addr_h'] = text_sprite('NUEVA DIRECCIÓN', 82, fill=ORANGE, stroke=WHITE, sw=8, shadow=False)
S['addr_1'] = text_sprite('Roque Sáenz Peña', 104, fill=PURPLE, stroke=WHITE, sw=8, shadow=False)
S['addr_y'] = text_sprite('y', 90, fill=ORANGE, stroke=WHITE, sw=8, shadow=False)
S['addr_2'] = text_sprite('Garibaldi', 140, fill=PURPLE, stroke=WHITE, sw=10, shadow=False)
S['addr_e1'] = emoji('🏠', 120); S['addr_e2'] = emoji('🐾', 100)
S['addr_top'] = text_sprite('¡NOS MUDAMOS!', 110, fill=WHITE, stroke=PURPLE, sw=12)

# hours
S['hrs_card'] = card(960, 1180, (40, 190, 175), (108, 63, 209))
S['clock'] = emoji('🕗', 170)
S['hrs_h'] = text_sprite('HORARIOS', 120, fill=YELLOW, stroke=DARK, sw=11)
S['lv'] = pill([emoji('📅', 70), text_sprite('LUNES A VIERNES', 66, fill=DARK, sw=0, shadow=False)], YELLOW, outline=WHITE)
S['lv1'] = text_sprite('8:30 a 13 hs', 100, fill=WHITE, stroke=DARK, sw=9)
S['lv2'] = text_sprite('16:30 a 21 hs', 100, fill=WHITE, stroke=DARK, sw=9)
S['sa'] = pill([emoji('📅', 70), text_sprite('SÁBADOS', 66, fill=DARK, sw=0, shadow=False)], YELLOW, outline=WHITE)
S['sa1'] = text_sprite('9 a 13 hs', 100, fill=WHITE, stroke=DARK, sw=9)
S['sa2'] = text_sprite('16:30 a 21 hs', 100, fill=WHITE, stroke=DARK, sw=9)
S['sun'] = emoji('☀️', 80); S['moon'] = emoji('🌙', 80)

# outro
S['te'] = text_sprite('¡Te esperamos', 128, fill=WHITE, stroke=PURPLE, sw=13)
S['con'] = text_sprite('con la amabilidad', 100, fill=YELLOW, stroke=PURPLE, sw=11)
S['de'] = text_sprite('de siempre!', 128, fill=WHITE, stroke=PURPLE, sw=13)
S['heart'] = emoji('💛', 90); S['heart2'] = emoji('🧡', 80)
S['paw'] = emoji('🐾', 90)
S['o_dog'] = emoji('🐶', 200); S['o_cat'] = emoji('🐱', 200)
S['o_addr'] = pill([emoji('📍', 64), text_sprite('Roque Sáenz Peña y Garibaldi', 54, sw=0, shadow=False)], PURPLE, pad=(36, 20))

confetti = [(random.uniform(0, W), random.uniform(-1.5, 0), random.uniform(240, 520), random.uniform(-60, 60),
             random.uniform(0, 6.28), random.choice(range(len(CONF))), random.uniform(0.6, 1.1)) for _ in range(26)]
hearts = [(random.uniform(60, W - 60), random.uniform(0, 4), random.uniform(160, 300), random.uniform(0.5, 1.0),
           random.choice(['heart', 'heart2', 'paw'])) for _ in range(18)]

# ---------------- per-segment overlays ----------------
def gradient_band(frame, y0, y1, alpha=150, top=True):
    band = np.zeros((y1 - y0, W, 4), np.uint8)
    k = np.linspace(1, 0, y1 - y0) if top else np.linspace(0, 1, y1 - y0)
    band[..., 0] = 30; band[..., 1] = 10; band[..., 2] = 50
    band[..., 3] = (k * alpha).astype(np.uint8)[:, None]
    frame.alpha_composite(Image.fromarray(band, 'RGBA'), (0, y0))

BANDS = {}
def overlay(frame, name, t, lt):
    if name == 'intro':
        if 'top' not in BANDS:
            b = Image.new('RGBA', (W, H)); gradient_band(b, 0, 1000, 190, True); gradient_band(b, 1400, H, 160, False)
            BANDS['top'] = b
        frame.alpha_composite(BANDS['top'])
        # confetti
        for (x, y0, vy, vr, ph, ci, sc) in confetti:
            y = (y0 * H) + vy * lt
            if 0.3 < lt and -100 < y < H + 100:
                place(frame, S['conf'][ci], x + 30 * math.sin(lt * 2 + ph), y, sc, rot=vr * lt)
        s1 = ease_out_elastic((lt - 0.35) / 0.9) if lt > 0.35 else 0
        s2 = ease_out_elastic((lt - 0.6) / 0.9) if lt > 0.6 else 0
        wob = math.sin(lt * 6) * 3
        place(frame, S['nuevo'], W / 2, 390, s1, rot=wob)
        place(frame, S['local'], W / 2, 590, s2, rot=-wob)
        place(frame, S['forr'], W / 2, 790, pop_in(lt, 1.25))
        bounce = abs(math.sin(lt * 5.5)) * 60
        place(frame, S['dog'], 230, 1640 - bounce, pop_in(lt, 0.9), rot=math.sin(lt * 5.5) * 8)
        place(frame, S['cat'], W - 230, 1640 - abs(math.sin(lt * 5.5 + 1.5)) * 60, pop_in(lt, 1.2),
              rot=-math.sin(lt * 5.5 + 1.5) * 8)
        place(frame, S['spark'], 150, 250, pop_in(lt, 1.6) * (0.8 + 0.2 * math.sin(lt * 9)))
        place(frame, S['spark'], W - 140, 700, pop_in(lt, 1.75) * (0.8 + 0.2 * math.sin(lt * 9 + 2)))
        place(frame, S['party'], W - 150, 230, pop_in(lt, 1.9), rot=math.sin(lt * 4) * 12)

    elif name.startswith('cap'):
        if 'bot' not in BANDS:
            b = Image.new('RGBA', (W, H)); gradient_band(b, 1150, H, 200, False); BANDS['bot'] = b
        frame.alpha_composite(BANDS['bot'])
        ka = ease_out_back((lt - 0.15) / 0.5, 1.4); kb = ease_out_back((lt - 0.35) / 0.5, 1.4)
        out = ease_in((lt - (SEG_LEN[name] - 0.35)) / 0.35)
        xa = -600 + (W / 2 + 600) * ka + out * 1400
        xb = W + 600 - (W / 2 + 600) * kb - out * 1400
        place(frame, S[name + '_a'], xa, 1360)
        place(frame, S[name + '_b'], xb, 1510)
        # runner crossing the bottom
        if S[name + '_run'] is None:
            return
        # emoji fijo en el centro inferior: salta y se balancea sin desplazarse
        x = W / 2
        hop = abs(math.sin(lt * 7)) * 55
        sq = 1 + 0.06 * math.sin(lt * 14)
        place(frame, S[name + '_run'], x, 1760 - hop, pop_in(lt, 0.3) * sq, rot=math.sin(lt * 7) * 8,
              flip=name != 'cap2')
        # huellitas y huesos fijos a los costados, con un leve rebote
        for k, (dx, kind) in enumerate([(-230, 'paw'), (-380, 'bone'), (230, 'bone'), (380, 'paw')]):
            y = 1800 - abs(math.sin(lt * 7 + k)) * 20
            place(frame, S[kind], x + dx, y, pop_in(lt, 0.4 + k * 0.08) * 0.6, rot=math.sin(lt * 5 + k) * 12)

    elif name == 'address':
        cy = 1000
        k = ease_out_back(lt / 0.55, 1.5)
        place(frame, S['addr_top'], W / 2, 250, pop_in(lt, 0.15), rot=math.sin(lt * 5) * 3)
        place(frame, S['addr_card'], W / 2, cy + (1 - k) * 900)
        if lt > 0.3:
            pin_y = cy - 340 - abs(math.sin(lt * 4.5)) * 70
            place(frame, S['pin'], W / 2, pin_y, pop_in(lt, 0.3))
        place(frame, S['addr_h'], W / 2, cy - 140, pop_in(lt, 0.55))
        place(frame, S['addr_1'], W / 2, cy + 20, pop_in(lt, 0.8))
        place(frame, S['addr_y'], W / 2, cy + 140, pop_in(lt, 1.0))
        place(frame, S['addr_2'], W / 2, cy + 270, pop_in(lt, 1.15) * (1 + 0.04 * math.sin(lt * 6)))
        place(frame, S['addr_e1'], 150, 1640, pop_in(lt, 1.4), rot=math.sin(lt * 4) * 10)
        place(frame, S['addr_e2'], W - 150, 1640, pop_in(lt, 1.6), rot=-math.sin(lt * 4) * 10)
        fade_out(frame, lt, SEG_LEN[name])

    elif name == 'hours':
        cy = 1010
        k = ease_out_back(lt / 0.55, 1.5)
        place(frame, S['hrs_card'], W / 2, cy + (1 - k) * 1100)
        place(frame, S['clock'], W / 2, 330, pop_in(lt, 0.25), rot=math.sin(lt * 7) * 10)
        place(frame, S['hrs_h'], W / 2, 520, pop_in(lt, 0.45))
        def slide(sp, y, t0, frm=1):
            kk = ease_out_back((lt - t0) / 0.5, 1.3)
            if lt >= t0:
                place(frame, sp, W / 2 + frm * (1 - kk) * 1100, y)
        slide(S['lv'], 690, 1.15, -1)
        slide(S['lv1'], 820, 1.35, 1); slide(S['lv2'], 945, 1.5, 1)
        place(frame, S['sun'], 170, 820, pop_in(lt, 1.6)); place(frame, S['moon'], 170, 945, pop_in(lt, 1.7))
        slide(S['sa'], 1110, 2.95, -1)
        slide(S['sa1'], 1240, 3.15, 1); slide(S['sa2'], 1365, 3.3, 1)
        place(frame, S['sun'], 170, 1240, pop_in(lt, 3.4)); place(frame, S['moon'], 170, 1365, pop_in(lt, 3.5))
        bounce = abs(math.sin(lt * 5)) * 40
        place(frame, S['dog'], 230, 1750 - bounce, pop_in(lt, 0.8) * 0.7)
        place(frame, S['cat'], W - 230, 1750 - abs(math.sin(lt * 5 + 1.4)) * 40, pop_in(lt, 1.0) * 0.7)
        fade_out(frame, lt, SEG_LEN[name])

    elif name == 'outro':
        for (x, t0, vy, sc, kind) in hearts:
            y = H + 80 - ((lt + t0) % 4.0) * vy * 1.6
            place(frame, S[kind], x + 25 * math.sin(lt * 3 + t0), y, sc, alpha=0.85)
        place(frame, S['te'], W / 2, 520, ease_out_elastic((lt - 0.2) / 0.9) if lt > 0.2 else 0)
        place(frame, S['con'], W / 2, 690, ease_out_elastic((lt - 0.5) / 0.9) if lt > 0.5 else 0)
        place(frame, S['de'], W / 2, 860, ease_out_elastic((lt - 0.8) / 0.9) if lt > 0.8 else 0)
        place(frame, S['heart'], W / 2, 1090, pop_in(lt, 1.1) * (1.6 + 0.25 * abs(math.sin(lt * 7))))
        place(frame, S['o_dog'], 260, 1300 - abs(math.sin(lt * 5)) * 50, pop_in(lt, 1.2), rot=math.sin(lt * 5) * 10)
        place(frame, S['o_cat'], W - 260, 1300 - abs(math.sin(lt * 5 + 1.5)) * 50, pop_in(lt, 1.35),
              rot=-math.sin(lt * 5 + 1.5) * 10)
        place(frame, S['o_addr'], W / 2, 1600, pop_in(lt, 1.6))
        # paw trail walking across the top
        steps = int(lt / 0.22)
        for s in range(min(steps, 12)):
            px = 80 + s * 85; py = 230 + (30 if s % 2 else -30)
            place(frame, S['paw'], px, py, 0.6, rot=-90, alpha=0.9)

def fade_out(frame, lt, L):
    pass

SEG_LEN = {n: e - s for s, e, _, n in SEGS}

# ---------------- render ----------------
out = sys.argv[1]
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-i', 'music.wav', '-map', '0:v', '-map', '1:a',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out],
                       stdin=subprocess.PIPE)
total = int(END * FPS)
seg_i = -1; clip = None
for fi in range(total):
    t = fi / FPS
    while seg_i + 1 < len(SEGS) and t >= SEGS[seg_i + 1][0]:
        seg_i += 1
        clip = SEGS[seg_i][2]()
    s, e, _, name = SEGS[seg_i]
    lt = t - s
    frame = clip.frame()
    # punch-in transition
    if lt < 0.2 and seg_i > 0:
        z = 1 + 0.12 * (1 - ease_out(lt / 0.2))
        zw, zh = int(W * z), int(H * z)
        frame = frame.resize((zw, zh), Image.BILINEAR).crop(((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
    overlay(frame, name, t, lt)
    # white flash at cuts
    if seg_i > 0 and lt < 0.15:
        a = int(200 * (1 - lt / 0.15))
        frame.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, a)))
    if t < 0.25:
        frame.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * (1 - t / 0.25)))))
    if t > END - 0.6:
        frame.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * clamp((t - (END - 0.6)) / 0.6)))))
    enc.stdin.write(frame.convert('RGB').tobytes())
    if fi % 60 == 0:
        print(f'{t:.1f}s', flush=True)
enc.stdin.close(); enc.wait()
print('done')
