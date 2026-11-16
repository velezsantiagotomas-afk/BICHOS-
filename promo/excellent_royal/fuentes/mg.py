"""Versión motion graphics: Excellent + Royal Canin (15 s, vertical)."""
exec(open('common_head.py').read())
from PIL import ImageOps

END = 15.0
FOT = 'ex/fotos2/'
RED = (215, 25, 55); RED2 = (150, 10, 40); GOLD = (200, 160, 70); GOLD2 = (120, 90, 30)
BLUE = (40, 150, 215); CREAM = (255, 246, 228); INK = (45, 20, 70)
random.seed(21)

# escenas: (inicio, fin, nombre)
SCENES = [(0.0, 2.5, 'intro'), (2.5, 6.0, 'excellent'), (6.0, 9.5, 'royal'), (9.5, 12.0, 'grid'), (12.0, END, 'map')]
CUTS = [s for s, _, _ in SCENES[1:]]


# ---------------- fondos ----------------
def vgrad(top, bot):
    k = np.linspace(0, 1, H)[:, None, None]
    g = np.array(top)[None, None] * (1 - k) + np.array(bot)[None, None] * k
    return np.repeat(g, W, 1).astype(np.uint8)

BG = {
    'intro': vgrad((110, 60, 220), (40, 15, 90)),
    'excellent': vgrad((235, 45, 75), (120, 8, 35)),
    'royal': vgrad((225, 190, 110), (110, 80, 25)),
    'grid': vgrad((60, 30, 120), (20, 10, 45)),
    'map': vgrad((255, 248, 232), (250, 225, 190)),
}

# patrón de puntitos que se desliza en diagonal
_dots = Image.new('RGBA', (W + 120, H + 120), (0, 0, 0, 0))
_dd = ImageDraw.Draw(_dots)
for yy in range(0, H + 120, 60):
    for xx in range(0, W + 120, 60):
        _dd.ellipse((xx - 5, yy - 5, xx + 5, yy + 5), fill=(255, 255, 255, 38))

# círculos/anillos flotantes
RINGS = [(random.uniform(0, W), random.uniform(0, H), random.uniform(60, 220), random.uniform(0.2, 0.6),
          random.uniform(0, 6.28), random.choice([0, 1])) for _ in range(9)]


def background(name, t):
    fr = Image.fromarray(BG[name]).convert('RGBA')
    off = int((t * 40) % 60)
    fr.alpha_composite(_dots.crop((off, off, off + W, off + H)))
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = 70 if name != 'map' else 45
    col = (255, 255, 255, a) if name != 'map' else (255, 140, 0, a)
    for (x, y, r, sp, ph, kind) in RINGS:
        cx = x + 40 * math.sin(t * sp + ph); cy = (y - t * 60 * sp) % (H + 400) - 200
        rr = r * (1 + 0.1 * math.sin(t * 2 + ph))
        if kind:
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=col, width=10)
        else:
            d.ellipse((cx - rr * 0.4, cy - rr * 0.4, cx + rr * 0.4, cy + rr * 0.4), fill=col)
    fr.alpha_composite(layer)
    return fr


# ---------------- transiciones: barras diagonales de colores ----------------
WIPE_COLS = [YELLOW, ORANGE, PINK, PURPLE]
def wipe(frame, t):
    for c in CUTS:
        u = (t - c) / 0.32                    # -1 .. 1 alrededor del corte
        if -1 <= u <= 1:
            layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            for i, col in enumerate(WIPE_COLS):
                x = (u - i * 0.12 + 0.18) * 2600
                d.polygon([(x - 1500, 0), (x + 300, 0), (x - 300, H), (x - 2100, H)], fill=col + (255,))
            frame.alpha_composite(layer)


# ---------------- elementos ----------------
def letters(txt, size, fill, stroke, sw):
    f = font(size)
    out, x = [], 0
    for ch in txt:
        adv = f.getlength(ch)
        out.append((text_sprite(ch, size, fill=fill, stroke=stroke, sw=sw) if ch != ' ' else None, x + adv / 2))
        x += adv
    return out, x

def bar_reveal(frame, bg_col, txt_spr, cx, cy, lt, t0, pad=40):
    """barra de color que crece y el texto sube desde adentro (clásico motion graphics)."""
    if lt < t0:
        return
    bw, bh = txt_spr.width + pad * 2, txt_spr.height + 10
    k = ease_out((lt - t0) / 0.35)
    w = max(2, int(bw * k))
    bar = Image.new('RGBA', (w, bh), bg_col + (255,))
    frame.alpha_composite(bar, (int(cx - bw / 2), int(cy - bh / 2)))
    kt = ease_out((lt - t0 - 0.15) / 0.35)
    if kt > 0:
        vis = int(txt_spr.height * kt)
        piece = txt_spr.crop((0, 0, txt_spr.width, vis))
        frame.alpha_composite(piece, (int(cx - txt_spr.width / 2), int(cy - bh / 2 + 5 + (txt_spr.height - vis))))

def photo_card(path, w, cap=None):
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    im = im.crop((0, 0, w, min(im.height, int(w * 1.33))))
    b = 18
    c = Image.new('RGBA', (w + 2 * b + 40, im.height + 2 * b + 50), (0, 0, 0, 0))
    sh = Image.new('RGBA', c.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 34, 20 + w + 2 * b, 34 + im.height + 2 * b), 30, fill=(0, 0, 0, 150))
    c = Image.alpha_composite(c, sh.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(c).rounded_rectangle((20, 20, 20 + w + 2 * b, 20 + im.height + 2 * b), 30, fill=(255, 255, 255, 255))
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 20, fill=255)
    c.paste(im, (20 + b, 20 + b), m)
    return c

def starburst(r, col, txt):
    s = Image.new('RGBA', (2 * r + 20, 2 * r + 20), (0, 0, 0, 0))
    pts = []
    for i in range(32):
        a = i * math.pi / 16; rr = r if i % 2 == 0 else r * 0.82
        pts.append((r + 10 + rr * math.cos(a), r + 10 + rr * math.sin(a)))
    ImageDraw.Draw(s).polygon(pts, fill=col + (255,))
    ts = text_sprite(txt, int(r * 0.62), fill=INK, stroke=WHITE, sw=0, shadow=False)
    s.alpha_composite(ts, (s.width // 2 - ts.width // 2, s.height // 2 - ts.height // 2))
    return s

def chip(emo, txt, bg, fg=WHITE, size=54):
    return pill([emoji(emo, int(size * 1.3)), text_sprite(txt, size, fill=fg, sw=0, shadow=False)], bg, pad=(34, 18))


S = {}
S['lleg'], S['lleg_w'] = letters('¡LLEGARON!', 150, YELLOW, INK, 14)
S['ex_txt'] = text_sprite('Excellent', 110, fill=WHITE, stroke=WHITE, sw=0, shadow=False)
S['rc_txt'] = text_sprite('Royal Canin', 110, fill=WHITE, stroke=WHITE, sw=0, shadow=False)
S['y'] = text_sprite('&', 100, fill=YELLOW, stroke=INK, sw=8)
S['dog'] = emoji('🐶', 170); S['fire'] = emoji('🔥', 120); S['spark'] = emoji('✨', 100); S['party'] = emoji('🎉', 120)

S['ex_h1'] = text_sprite('PURINA', 70, fill=RED2, stroke=WHITE, sw=0, shadow=False)
S['ex_h2'] = text_sprite('Excellent', 130, fill=WHITE, stroke=WHITE, sw=0, shadow=False)
S['ex_p1'] = photo_card(FOT + '1_ex_peq_ok.jpg', 470)
S['ex_p2'] = photo_card(FOT + '2_ex_med_ok.jpg', 470)
S['ex_c1'] = chip('🐕', 'Razas pequeñas', PURPLE)
S['ex_c2'] = chip('🐕‍🦺', 'Medianas y grandes', PURPLE)
S['ex_c3'] = chip('✨', 'Piel y pelaje saludables', YELLOW, INK)
S['ex_c4'] = chip('🛡️', 'Sistema inmune sano', YELLOW, INK)
S['kg'] = starburst(120, YELLOW, '3 kg')

S['rc_h1'] = text_sprite('ROYAL', 120, fill=WHITE, stroke=WHITE, sw=0, shadow=False)
S['rc_h2'] = text_sprite('CANIN', 120, fill=WHITE, stroke=WHITE, sw=0, shadow=False)
S['rc_p1'] = photo_card(FOT + '3_dach_ok.jpg', 470)
S['rc_p2'] = photo_card(FOT + '4_puppy_ok.jpg', 470)
S['rc_c1'] = chip('🌭', 'Dachshund: perros salchicha', RED)
S['rc_c2'] = chip('🐶', 'Puppy Mini · 2 a 10 meses', BLUE)
S['rc_c3'] = chip('🧠', 'Desarrollo del cerebro', YELLOW, INK)

S['gr_h'] = text_sprite('¡Vení a verlos!', 120, fill=WHITE, stroke=PURPLE, sw=12)
S['grid'] = [photo_card(FOT + f, 420) for f in ['1_ex_peq_ok.jpg', '2_ex_med_ok.jpg', '3_dach_ok.jpg', '4_puppy_ok.jpg']]
S['camera'] = emoji('📸', 110)

S['te'] = text_sprite('¡Te esperamos!', 120, fill=PURPLE, stroke=WHITE, sw=10)
S['pin'] = emoji('📍', 190)
S['st1'] = text_sprite('ROQUE SÁENZ PEÑA', 42, fill=WHITE, stroke=WHITE, sw=0, shadow=False)
S['st2'] = text_sprite('GARIBALDI', 52, fill=WHITE, stroke=WHITE, sw=0, shadow=False).rotate(90, expand=True)
S['addr'] = pill([emoji('📍', 70), text_sprite('Roque Sáenz Peña y Garibaldi', 58, sw=0, shadow=False)], PURPLE, pad=(36, 22))
S['paw'] = emoji('🐾', 80); S['heart'] = emoji('🧡', 80)


def slide_in(frame, spr, x, y, lt, t0, frm=(-1, 0), rot0=0, rot1=0, dur=0.5, dist=1300):
    if lt < t0: return
    k = ease_out_back((lt - t0) / dur, 1.4)
    place(frame, spr, x + frm[0] * (1 - k) * dist, y + frm[1] * (1 - k) * dist, rot=rot0 + (rot1 - rot0) * k)

def kinetic(frame, key, cx, cy, lt, t0, step=0.05):
    lets, total = S[key], S[key + '_w']
    for i, (sp, xc) in enumerate(lets):
        if sp is None: continue
        u = lt - t0 - i * step
        if u <= 0: continue
        k = ease_out_back(u / 0.35, 2.2)
        place(frame, sp, cx - total / 2 + xc, cy - (1 - k) * 160, clamp(k * 1.0, 0, 1.3), rot=(1 - clamp(k)) * 30)


def scene(frame, name, lt, t):
    if name == 'intro':
        # anillos que explotan desde el centro
        for i, col in enumerate([YELLOW, ORANGE, PINK]):
            u = lt - i * 0.12
            if 0 < u < 1.0:
                r = ease_out(u / 1.0) * 1300
                l = Image.new('RGBA', (W, H)); ImageDraw.Draw(l).ellipse((W / 2 - r, 900 - r, W / 2 + r, 900 + r),
                                                                           outline=col + (int(255 * (1 - u)),), width=40)
                frame.alpha_composite(l)
        kinetic(frame, 'lleg', W / 2, 620, lt, 0.15)
        bar_reveal(frame, RED, S['ex_txt'], W / 2, 900, lt, 0.75)
        place(frame, S['y'], W / 2, 1060, pop_in(lt, 1.0))
        bar_reveal(frame, (200, 20, 40), S['rc_txt'], W / 2, 1220, lt, 1.1)
        place(frame, S['dog'], W / 2, 1520 - abs(math.sin(lt * 5)) * 60, pop_in(lt, 1.4), rot=math.sin(lt * 5) * 8)
        place(frame, S['fire'], 150, 420, pop_in(lt, 1.5) * (0.9 + 0.1 * math.sin(lt * 10)))
        place(frame, S['party'], W - 150, 420, pop_in(lt, 1.6), rot=math.sin(lt * 5) * 12)

    elif name == 'excellent':
        bar_reveal(frame, WHITE, S['ex_h1'], W / 2, 190, lt, 0.1, pad=30)
        place(frame, S['ex_h2'], W / 2, 330, pop_in(lt, 0.25, 0.5))
        slide_in(frame, S['ex_p1'], 300, 860, lt, 0.4, (-1, 0), -25, -6)
        slide_in(frame, S['ex_p2'], 780, 900, lt, 0.6, (1, 0), 25, 6)
        place(frame, S['kg'], W - 150, 560, pop_in(lt, 0.9), rot=math.sin(lt * 3) * 12)
        slide_in(frame, S['ex_c1'], W / 2, 1330, lt, 1.0, (-1, 0))
        slide_in(frame, S['ex_c2'], W / 2, 1465, lt, 1.15, (1, 0))
        slide_in(frame, S['ex_c3'], W / 2, 1600, lt, 1.5, (0, 1), dist=700)
        slide_in(frame, S['ex_c4'], W / 2, 1735, lt, 1.7, (0, 1), dist=700)

    elif name == 'royal':
        bar_reveal(frame, RED, S['rc_h1'], W / 2 - 170, 220, lt, 0.1, pad=30)
        bar_reveal(frame, (200, 20, 40), S['rc_h2'], W / 2 + 190, 360, lt, 0.25, pad=30)
        slide_in(frame, S['rc_p1'], 300, 900, lt, 0.4, (0, -1), -20, -6, dist=1500)
        slide_in(frame, S['rc_p2'], 780, 940, lt, 0.6, (0, 1), 20, 6, dist=1500)
        place(frame, S['kg'], 150, 560, pop_in(lt, 0.9), rot=-math.sin(lt * 3) * 12)
        slide_in(frame, S['rc_c1'], W / 2, 1440, lt, 1.0, (-1, 0))
        slide_in(frame, S['rc_c2'], W / 2, 1570, lt, 1.2, (1, 0))
        slide_in(frame, S['rc_c3'], W / 2, 1710, lt, 1.5, (0, 1), dist=700)

    elif name == 'grid':
        place(frame, S['gr_h'], W / 2, 200, ease_out_elastic((lt - 0.05) / 0.8) if lt > 0.05 else 0)
        place(frame, S['camera'], W / 2, 350, pop_in(lt, 0.15), rot=math.sin(lt * 6) * 10)
        pos = [(290, 760, -5), (790, 760, 5), (290, 1400, 4), (790, 1400, -4)]
        for i, (x, y, r) in enumerate(pos):
            t_in = 0.2 + i * 0.3; t_out = 1.85 + i * 0.08
            if lt < t_in: continue
            k = ease_out_back((lt - t_in) / 0.35, 1.8)
            ko = 1 - ease_in((lt - t_out) / 0.2)
            place(frame, S['grid'][i], x, y, k * ko, rot=r + (1 - ko) * 40)

    elif name == 'map':
        # dos calles que se dibujan y se cruzan
        cx, cy = W / 2, 1000
        k1 = ease_out(lt / 0.6); k2 = ease_out((lt - 0.2) / 0.6)
        l = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(l)
        x0 = -50; x1 = x0 + (W + 100) * k1
        d.rectangle((x0, cy - 70, x1, cy + 70), fill=(70, 60, 85, 255))
        for xx in range(-40, int(x1), 120):
            if xx < 20 + S['st1'].width + 10: continue
            d.rectangle((xx, cy - 6, xx + 60, cy + 6), fill=(255, 255, 255, 230))
        if k2 > 0:
            y1 = H + 50 - (H + 100) * k2
            d.rectangle((cx - 70, y1, cx + 70, H + 50), fill=(70, 60, 85, 255))
            for yy in range(H, int(y1), -120):
                if 1170 < yy < 1190 + S['st2'].height + 60: continue
                d.rectangle((cx - 6, yy - 60, cx + 6, yy), fill=(255, 255, 255, 230))
        frame.alpha_composite(l)
        if lt > 0.5:
            frame.alpha_composite(S['st1'], (20, int(cy - S['st1'].height / 2)))
        if lt > 0.7:
            frame.alpha_composite(S['st2'], (int(cx - S['st2'].width / 2), 1180))
        # pin cae en la esquina + ondas
        if lt > 0.8:
            u = lt - 0.8
            y = cy - 110 - (1 - ease_out_back(u / 0.5, 2.0)) * 900
            for j in range(3):
                v = (u - 0.4 - j * 0.35) % 1.2
                if u > 0.4:
                    r = v * 300
                    rl = Image.new('RGBA', (W, H))
                    ImageDraw.Draw(rl).ellipse((cx - r, cy - r * 0.5, cx + r, cy + r * 0.5),
                                               outline=ORANGE + (int(220 * (1 - v / 1.2)),), width=8)
                    frame.alpha_composite(rl)
            place(frame, S['pin'], cx, y)
        place(frame, S['te'], W / 2, 330, ease_out_elastic((lt - 0.1) / 0.9) if lt > 0.1 else 0)
        place(frame, S['addr'], W / 2, 1700, pop_in(lt, 1.3))
        place(frame, S['paw'], 140, 560, pop_in(lt, 1.5), rot=-20)
        place(frame, S['heart'], W - 140, 560, pop_in(lt, 1.6) * (1 + 0.1 * math.sin(lt * 8)))


out = sys.argv[1]
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-i', 'music_mg.wav', '-map', '0:v', '-map', '1:a',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out],
                       stdin=subprocess.PIPE)
for fi in range(int(END * FPS)):
    t = fi / FPS
    s, e, name = [sc for sc in SCENES if sc[0] <= t < sc[1]][0] if t < END else SCENES[-1]
    lt = t - s
    frame = background(name, t)
    scene(frame, name, lt, t)
    wipe(frame, t)
    if t < 0.15:
        frame.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * (1 - t / 0.15)))))
    if t > END - 0.4:
        frame.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * clamp((t - (END - 0.4)) / 0.4)))))
    enc.stdin.write(frame.convert('RGB').tobytes())
enc.stdin.close(); enc.wait()
print('done')
