"""Muestra de 5 fondos distintos (contenido: opción A, recorte flotante)."""
src = open('mg_opts.py').read()
exec(src[:src.index("OPTS = [")])
import cv2
S['ex_h2'] = text_sprite('Excellent', 130, fill=WHITE, stroke=RED2, sw=10)
S['kg'] = starburst(120, WHITE, '3 kg')

VBG = UP + 'ea5b05fa-20261116_110057.mp4'
from defan import remove_fan

# ---- 1: degradé animado que fluye (violeta / naranja / rosa) ----
def bg_gradient(t):
    h, w = 96, 54
    yy, xx = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    a = 0.5 + 0.5 * np.sin(2 * math.pi * (xx * 0.8 + yy * 1.2) + t * 1.6)
    b = 0.5 + 0.5 * np.sin(2 * math.pi * (xx * 1.3 - yy * 0.7) - t * 1.2 + 1.0)
    c1, c2, c3 = np.array((110, 50, 220)), np.array((255, 120, 40)), np.array((255, 70, 150))
    img = c1 * (1 - a)[..., None] + c2 * a[..., None]
    img = img * (1 - 0.5 * b)[..., None] + c3 * (0.5 * b)[..., None]
    img = cv2.resize(img.astype(np.uint8), (W, H), interpolation=cv2.INTER_CUBIC)
    return Image.fromarray(img).convert('RGBA')

# ---- 2: rayos de sol que giran (clásico de ofertas) ----
def bg_sunburst(t):
    base = Image.new('RGBA', (W, H), (255, 150, 30, 255))
    l = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(l)
    cx, cy, R = W / 2, 950, 2400
    n = 24
    for i in range(n):
        if i % 2: continue
        a0 = math.radians(i * 360 / n + t * 12); a1 = math.radians((i + 1) * 360 / n + t * 12)
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))],
                  fill=(255, 200, 60, 255))
    base.alpha_composite(l)
    v = Image.new('RGBA', (W, H)); ImageDraw.Draw(v).ellipse((cx - 700, cy - 700, cx + 700, cy + 700), fill=(255, 240, 180, 160))
    base.alpha_composite(v.filter(ImageFilter.GaussianBlur(120)))
    return base

# ---- 3: manchas líquidas de colores en movimiento (estilo moderno) ----
BLOBS = [((255, 90, 160), 0.0), ((110, 60, 230), 1.3), ((255, 170, 40), 2.6), ((40, 190, 200), 3.9), ((255, 110, 60), 5.2)]
def bg_blobs(t):
    sw, sh = 135, 240
    im = Image.new('RGB', (sw, sh), (35, 15, 70)); d = ImageDraw.Draw(im)
    for col, ph in BLOBS:
        x = sw / 2 + sw * 0.4 * math.sin(t * 0.7 + ph); y = sh / 2 + sh * 0.35 * math.cos(t * 0.5 + ph * 1.3)
        r = 45 + 12 * math.sin(t + ph)
        d.ellipse((x - r, y - r, x + r, y + r), fill=col)
    im = im.filter(ImageFilter.GaussianBlur(22)).resize((W, H), Image.BICUBIC)
    return im.convert('RGBA')

# ---- 4: patrón de huellitas y huesitos que se desliza ----
_pat = Image.new('RGBA', (W + 300, H + 300), (255, 214, 64, 255))
_pp = emoji('🐾', 90); _pb = emoji('🦴', 80)
for j, yy in enumerate(range(0, H + 300, 150)):
    for i, xx in enumerate(range(0, W + 300, 150)):
        spr = (_pp if (i + j) % 2 == 0 else _pb).rotate(((i * 37 + j * 53) % 60) - 30, expand=True)
        a = spr.getchannel('A').point(lambda v: int(v * 0.35)); spr = spr.copy(); spr.putalpha(a)
        _pat.alpha_composite(spr, (xx + (75 if j % 2 else 0) - spr.width // 2, yy - spr.height // 2))
def bg_paws(t):
    off = int((t * 50) % 300)
    return _pat.crop((off, off, off + W, off + H)).copy()

# ---- 5: el local desenfocado con un tinte de color ----
class _LocalBG:
    def __init__(self):
        vf = f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}'
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', '0.5', '-i', VBG, '-vf', vf, '-frames:v', '120',
                                   '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
        self.last = None
    def frame(self):
        buf = self.p.stdout.read(W * H * 3)
        if len(buf) == W * H * 3:
            arr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            arr, _ = remove_fan(arr, dark=105, sat=80, dil=0.03, touch_top=False, top_frac=0.05)
            arr = cv2.GaussianBlur(arr, (0, 0), 22)
            tint = np.array((90, 30, 140), np.float32)
            arr = (arr * 0.55 + tint * 0.45).astype(np.uint8)
            self.last = Image.fromarray(arr).convert('RGBA')
        return self.last.copy()
_local = None
def bg_local(t):
    global _local
    if _local is None: _local = _LocalBG()
    return _local.frame()

FONDOS = [('1', 'Degradé que fluye', bg_gradient), ('2', 'Rayos de sol', bg_sunburst), ('3', 'Manchas de colores', bg_blobs),
          ('4', 'Huellitas y huesitos', bg_paws), ('5', 'El local desenfocado', bg_local)]
LBL = {k: pill([text_sprite(f'FONDO {k} · {txt}', 48, fill=INK, sw=0, shadow=False)], WHITE, pad=(30, 14), outline=INK, ow=4)
       for k, txt, _ in FONDOS}

SEG = 3.0
out = sys.argv[1]
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-i', 'music_mg.wav', '-map', '0:v', '-map', '1:a',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out],
                       stdin=subprocess.PIPE)
for fi in range(int(SEG * len(FONDOS) * FPS)):
    t = fi / FPS; i = int(t // SEG); lt = t - i * SEG
    key, _, fn = FONDOS[i]
    frame = fn(lt)
    opt_A(frame, lt)
    place(frame, LBL[key], W / 2, 110)
    if lt < 0.12 and i > 0:
        frame.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(220 * (1 - lt / 0.12)))))
    enc.stdin.write(frame.convert('RGB').tobytes())
enc.stdin.close(); enc.wait()
print('done')
