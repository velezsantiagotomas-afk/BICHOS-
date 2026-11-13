import os
exec(open('common_head.py').read())

VB = UP + 'c046b3ce-20261113_093259.mp4'   # bolsas Old Prince
GOLDEN = sys.argv[2] if len(sys.argv) > 2 else None
END = 15.0
TEAL_OP = (30, 150, 185); GREEN_OP = (110, 160, 60)


class CropClip(Clip):
    def __init__(self, path, ss, dur, pre='', blur=0, dim=0.0):
        vf = (pre + ',' if pre else '') + \
            f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},eq=saturation=1.2:contrast=1.06:brightness=0.03'
        if blur:
            vf += f',gblur=sigma={blur}'
        self.n = int(round(dur * FPS)); self.dim = dim; self.last = None
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(ss), '-i', path, '-vf', vf,
                                   '-frames:v', str(self.n), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                  stdout=subprocess.PIPE)


class Photo:
    """Foto con zoom lento (Ken Burns), recortada a vertical."""
    def __init__(self, path, dur, focus=(0.5, 0.5)):
        im = Image.open(path).convert('RGB')
        r = max(W / im.width, H / im.height) * 1.18
        self.im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
        self.n = int(dur * FPS); self.i = 0; self.focus = focus
    def frame(self):
        k = self.i / max(1, self.n - 1); self.i += 1
        z = 1.0 + 0.12 * k                      # zoom-in suave
        cw, ch = int(W * 1.18 / z), int(H * 1.18 / z)
        cw = min(cw, self.im.width); ch = min(ch, self.im.height)
        cx = int(self.focus[0] * self.im.width); cy = int(self.focus[1] * self.im.height)
        x = clamp(cx - cw // 2, 0, self.im.width - cw); y = clamp(cy - ch // 2, 0, self.im.height - ch)
        return self.im.crop((x, y, x + cw, y + ch)).resize((W, H), Image.BILINEAR).convert('RGBA')


SEGS = [
    (0.0, 3.0, lambda: CropClip(VB, 0.0, 3.0), 'intro'),
    (3.0, 6.0, lambda: CropClip(VB, 8.0, 3.0, blur=14, dim=0.2), 'sizes'),
    (6.0, 9.0, lambda: CropClip(VB, 3.3, 3.0, pre='crop=640:1138:200:620'), 'puppy'),
    (9.0, 12.0, lambda: CropClip(VB, 7.0, 3.0, pre='crop=700:1244:300:420'), 'small'),
    (12.0, END, (lambda: Photo(GOLDEN, END - 12.0, focus=(0.42, 0.45))) if GOLDEN else (lambda: CropClip(VB, 5.0, 3.1, blur=8, dim=0.2)), 'outro'),
]

# ---------------- sprites ----------------
S = {}
S['inc'] = text_sprite('¡INCORPORAMOS!', 120, fill=YELLOW, stroke=PURPLE, sw=12)
S['op'] = text_sprite('Old Prince', 170, fill=WHITE, stroke=PURPLE, sw=15)
S['pn'] = pill([text_sprite('PROTEÍNAS NOVELES', 66, sw=0, shadow=False)], ORANGE)
S['party'] = emoji('🎉', 150); S['spark'] = emoji('✨', 110); S['star'] = emoji('🌟', 110)
S['dog'] = emoji('🐶', 200); S['bone'] = emoji('🦴', 90)
S['conf'] = [emoji(c, 70) for c in ['🐾', '🦴', '⭐', '🐾', '💙', '💚']]

S['sz_card'] = card(960, 1060, (255, 255, 255), (235, 246, 255), outline=ORANGE)
S['sz_h'] = text_sprite('EN BOLSAS DE', 84, fill=ORANGE, stroke=WHITE, sw=8, shadow=False)
S['sz_pup'] = pill([emoji('🐶', 90), text_sprite('CACHORRO', 70, sw=0, shadow=False)], TEAL_OP)
S['sz_pup_kg'] = text_sprite('3 kg', 120, fill=PURPLE, stroke=WHITE, sw=8, shadow=False)
S['sz_sm'] = pill([emoji('🐕', 90), text_sprite('ADULTO SMALL', 70, sw=0, shadow=False)], GREEN_OP)
S['sz_sm_kg'] = text_sprite('3 kg y 7,5 kg', 120, fill=PURPLE, stroke=WHITE, sw=8, shadow=False)
S['bag'] = emoji('🛍️', 120)

S['pup_t'] = pill([emoji('🐶', 100), text_sprite('PUPPY · Cachorros', 72, sw=0, shadow=False)], TEAL_OP)
S['pup_1'] = pill([emoji('🧠', 96), text_sprite('Incrementa el desarrollo', 62, sw=0, shadow=False)], PURPLE)
S['pup_2'] = pill([text_sprite('del sistema cognitivo', 62, sw=0, shadow=False)], PURPLE)

S['sm_t'] = pill([emoji('🐕', 100), text_sprite('ADULT · Small Breeds', 72, sw=0, shadow=False)], GREEN_OP)
S['sm_1'] = pill([emoji('✨', 96), text_sprite('Mejora la piel', 66, sw=0, shadow=False)], PURPLE)
S['sm_2'] = pill([text_sprite('y el pelo', 66, sw=0, shadow=False), emoji('🐾', 80)], PURPLE)
S['lamb'] = pill([emoji('🐑', 70), text_sprite('Cordero y arroz integral', 54, sw=0, shadow=False), emoji('🍚', 70)],
                 ORANGE, pad=(34, 18))

S['te'] = text_sprite('¡Vení a conocerla!', 112, fill=WHITE, stroke=PURPLE, sw=12)
S['heart'] = emoji('💛', 110); S['heart2'] = emoji('🧡', 80); S['paw'] = emoji('🐾', 90)
S['o_addr'] = pill([emoji('📍', 70), text_sprite('Roque Sáenz Peña y Garibaldi', 56, sw=0, shadow=False)], PURPLE, pad=(36, 22))
S['credit'] = text_sprite('Foto: Easton (CC BY 3.0, Wikimedia Commons)', 30, fill=WHITE, stroke=DARK, sw=3, shadow=False)
S['o_op'] = pill([text_sprite('Old Prince · Proteínas Noveles', 60, sw=0, shadow=False)], ORANGE, pad=(36, 20))

random.seed(5)
confetti = [(random.uniform(0, W), random.uniform(-1.5, 0), random.uniform(260, 520), random.uniform(-60, 60),
             random.uniform(0, 6.28), random.choice(range(6)), random.uniform(0.6, 1.1)) for _ in range(24)]
hearts = [(random.choice([random.uniform(50, 210), random.uniform(W - 210, W - 50)]), random.uniform(0, 4), random.uniform(160, 300), random.uniform(0.5, 1.0),
           random.choice(['heart', 'heart2', 'paw'])) for _ in range(14)]

def gradient_band(frame, y0, y1, alpha=150, top=True):
    band = np.zeros((y1 - y0, W, 4), np.uint8)
    k = np.linspace(1, 0, y1 - y0) if top else np.linspace(0, 1, y1 - y0)
    band[..., 0] = 30; band[..., 1] = 10; band[..., 2] = 50
    band[..., 3] = (k * alpha).astype(np.uint8)[:, None]
    frame.alpha_composite(Image.fromarray(band, 'RGBA'), (0, y0))

BANDS = {}
def band(frame, key, *specs):
    if key not in BANDS:
        b = Image.new('RGBA', (W, H))
        for sp in specs: gradient_band(b, *sp)
        BANDS[key] = b
    frame.alpha_composite(BANDS[key])

def slide(frame, sp, y, lt, t0, frm=1):
    kk = ease_out_back((lt - t0) / 0.45, 1.3)
    if lt >= t0:
        place(frame, sp, W / 2 + frm * (1 - kk) * 1100, y)

def overlay(frame, name, lt):
    if name == 'intro':
        band(frame, 'top', (0, 1050, 200, True))
        for (x, y0, vy, vr, ph, ci, sc) in confetti:
            y = y0 * H + vy * lt
            if lt > 0.3 and -100 < y < H + 100:
                place(frame, S['conf'][ci], x + 30 * math.sin(lt * 2 + ph), y, sc, rot=vr * lt)
        place(frame, S['inc'], W / 2, 300, ease_out_elastic((lt - 0.2) / 0.9) if lt > 0.2 else 0, rot=math.sin(lt * 6) * 3)
        place(frame, S['op'], W / 2, 500, ease_out_elastic((lt - 0.5) / 0.9) if lt > 0.5 else 0, rot=-math.sin(lt * 6) * 2)
        place(frame, S['pn'], W / 2, 690, pop_in(lt, 0.9))
        place(frame, S['party'], 140, 140, pop_in(lt, 1.1), rot=math.sin(lt * 5) * 12)
        place(frame, S['spark'], W - 130, 160, pop_in(lt, 1.2) * (0.8 + 0.2 * math.sin(lt * 9)))
        place(frame, S['star'], W - 140, 820, pop_in(lt, 1.35) * (0.8 + 0.2 * math.sin(lt * 9 + 2)))
        place(frame, S['dog'], 170, 860 - abs(math.sin(lt * 5.5)) * 50, pop_in(lt, 1.3) * 0.75, rot=math.sin(lt * 5.5) * 8)

    elif name == 'sizes':
        cy = 1000
        k = ease_out_back(lt / 0.5, 1.5)
        place(frame, S['sz_card'], W / 2, cy + (1 - k) * 1100)
        place(frame, S['bag'], W / 2, 400 - abs(math.sin(lt * 5)) * 40, pop_in(lt, 0.2), rot=math.sin(lt * 5) * 8)
        place(frame, S['sz_h'], W / 2, 590, pop_in(lt, 0.35))
        slide(frame, S['sz_pup'], 760, lt, 0.6, -1)
        slide(frame, S['sz_pup_kg'], 900, lt, 0.75, 1)
        slide(frame, S['sz_sm'], 1100, lt, 1.2, -1)
        slide(frame, S['sz_sm_kg'], 1240, lt, 1.35, 1)
        place(frame, S['lamb'], W / 2, 1720, pop_in(lt, 1.7))

    elif name in ('puppy', 'small'):
        band(frame, 'bot', (1100, H, 210, False))
        p = 'pup' if name == 'puppy' else 'sm'
        slide(frame, S[p + '_t'], 1330, lt, 0.15, -1)
        slide(frame, S[p + '_1'], 1500, lt, 0.45, 1)
        slide(frame, S[p + '_2'], 1640, lt, 0.6, 1)
        icon = S['spark'] if name == 'small' else S['star']
        place(frame, icon, W - 130, 1180 - abs(math.sin(lt * 5)) * 30, pop_in(lt, 0.9) * 0.8, rot=math.sin(lt * 4) * 12)
        place(frame, S['paw'], 130, 1180 - abs(math.sin(lt * 5 + 1)) * 30, pop_in(lt, 1.0) * 0.8, rot=-math.sin(lt * 4) * 12)

    elif name == 'outro':
        band(frame, 'outro', (0, 900, 190, True), (1250, H, 200, False))
        for (x, t0, vy, sc, kind) in hearts:
            y = H + 80 - ((lt + t0) % 4.0) * vy * 1.6
            place(frame, S[kind], x + 25 * math.sin(lt * 3 + t0), y, sc, alpha=0.85)
        place(frame, S['te'], W / 2, 330, ease_out_elastic((lt - 0.15) / 0.9) if lt > 0.15 else 0)
        place(frame, S['o_op'], W / 2, 500, pop_in(lt, 0.5))
        place(frame, S['o_addr'], W / 2, 1640, pop_in(lt, 1.0))
        if GOLDEN:
            place(frame, S['credit'], W / 2, 1860, alpha=0.85)

out = sys.argv[1]
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-i', 'music_op.wav', '-map', '0:v', '-map', '1:a',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out],
                       stdin=subprocess.PIPE)
seg_i = -1; clip = None
for fi in range(int(END * FPS)):
    t = fi / FPS
    while seg_i + 1 < len(SEGS) and t >= SEGS[seg_i + 1][0]:
        seg_i += 1; clip = SEGS[seg_i][2]()
    s, e, _, name = SEGS[seg_i]
    lt = t - s
    frame = clip.frame()
    if lt < 0.2 and seg_i > 0:
        z = 1 + 0.12 * (1 - ease_out(lt / 0.2)); zw, zh = int(W * z), int(H * z)
        frame = frame.resize((zw, zh), Image.BILINEAR).crop(((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
    overlay(frame, name, lt)
    if seg_i > 0 and lt < 0.15:
        frame.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(200 * (1 - lt / 0.15)))))
    if t < 0.2:
        frame.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * (1 - t / 0.2)))))
    if t > END - 0.5:
        frame.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * clamp((t - (END - 0.5)) / 0.5)))))
    enc.stdin.write(frame.convert('RGB').tobytes())
enc.stdin.close(); enc.wait()
print('done')
