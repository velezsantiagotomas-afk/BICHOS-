exec(open('common_head.py').read())

VX = UP + 'cfae7d86-20261116_104153.mp4'   # estante Excellent + Royal Canin
PHOTOS = sys.argv[2].split(';') if len(sys.argv) > 2 else []
END = 15.0
RED = (215, 25, 55); RC_RED = (200, 20, 40); GOLD = (190, 150, 60)


from defan import remove_fan
import cv2


class CropClip(Clip):
    """Lee el video, borra el ventilador de la pared y recién después desenfoca."""
    def __init__(self, path, ss, dur, pre='', blur=0, dim=0.0):
        vf = (pre + ',' if pre else '') + \
            f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},eq=saturation=1.2:contrast=1.06:brightness=0.03'
        self.blur = blur
        self.n = int(round(dur * FPS)); self.dim = dim; self.last = None
        self.p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(ss), '-i', path, '-vf', vf,
                                   '-frames:v', str(self.n), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                  stdout=subprocess.PIPE)
    def frame(self):
        buf = self.p.stdout.read(W * H * 3)
        if len(buf) == W * H * 3:
            arr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            arr, _ = remove_fan(arr, dark=105, sat=80, dil=0.03)
            if self.blur:
                arr = cv2.GaussianBlur(arr, (0, 0), self.blur)
            if self.dim:
                arr = (arr * (1 - self.dim)).astype(np.uint8)
            self.last = Image.fromarray(arr).convert('RGBA')
        return self.last.copy()


def polaroid(spec, w=640, rot=0):
    path, _, cap = spec.partition('|')
    from PIL import ImageOps
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    r = w / im.width
    im = im.resize((w, int(im.height * r)), Image.LANCZOS)
    if im.height > int(w * 1.35):
        im = im.crop((0, 0, w, int(w * 1.35)))
    b, bb = 26, 90
    card_ = Image.new('RGBA', (w + 2 * b + 40, im.height + b + bb + 50), (0, 0, 0, 0))
    sh = Image.new('RGBA', card_.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 34, 20 + w + 2 * b, 34 + im.height + b + bb), 18, fill=(0, 0, 0, 150))
    card_ = Image.alpha_composite(card_, sh.filter(ImageFilter.GaussianBlur(14)))
    ImageDraw.Draw(card_).rounded_rectangle((20, 20, 20 + w + 2 * b, 20 + im.height + b + bb), 18, fill=(255, 255, 255, 255))
    card_.paste(im, (20 + b, 20 + b))
    if cap:
        ts = text_sprite(cap, 46, fill=DARK, sw=0, shadow=False)
        if ts.width > w:
            ts = ts.resize((w, int(ts.height * w / ts.width)), Image.LANCZOS)
        card_.alpha_composite(ts, (20 + b + (w - ts.width) // 2, 20 + b + im.height + (bb + b - ts.height) // 2 - 6))
    return card_


SEGS = [
    (0.0, 2.5, lambda: CropClip(VX, 0.0, 2.5), 'intro'),
    (2.5, 5.5, lambda: CropClip(VX, 0.3, 3.0), 'excellent'),
    (5.5, 8.5, lambda: CropClip(VX, 4.9, 3.0), 'royal'),
    (8.5, 12.0, lambda: CropClip(VX, 2.0, 3.5, blur=16, dim=0.25), 'photos'),
    (12.0, END, lambda: CropClip(VX, 6.0, 1.95, blur=12, dim=0.2), 'outro'),
]

S = {}
S['lleg'] = text_sprite('¡LLEGARON!', 150, fill=YELLOW, stroke=PURPLE, sw=14)
S['ex'] = pill([text_sprite('Excellent', 100, sw=0, shadow=False)], RED, pad=(54, 26))
S['y'] = text_sprite('y', 90, fill=WHITE, stroke=PURPLE, sw=10)
S['rc'] = pill([text_sprite('Royal Canin', 100, sw=0, shadow=False)], RC_RED, pad=(54, 26))
S['fire'] = emoji('🔥', 130); S['party'] = emoji('🎉', 130); S['spark'] = emoji('✨', 100)
S['dog'] = emoji('🐶', 170); S['star'] = emoji('🌟', 100); S['heart'] = emoji('❤️', 90)
S['conf'] = [emoji(c, 70) for c in ['🐾', '🦴', '⭐', '❤️', '🐾', '✨']]

S['ex_t'] = pill([emoji('🐕', 96), text_sprite('Purina Excellent', 76, sw=0, shadow=False)], RED)
S['ex_1'] = pill([text_sprite('Adult · Razas pequeñas', 60, sw=0, shadow=False)], PURPLE)
S['ex_2'] = pill([text_sprite('y medianas y grandes', 60, sw=0, shadow=False)], PURPLE)
S['ex_3'] = pill([emoji('✨', 70), text_sprite('Piel y pelaje saludables', 54, fill=DARK, sw=0, shadow=False)], YELLOW, pad=(36, 18))
S['ex_4'] = pill([emoji('🛡️', 70), text_sprite('Sistema inmune sano', 54, fill=DARK, sw=0, shadow=False)], YELLOW, pad=(36, 18))
S['kg'] = pill([text_sprite('3 kg', 70, sw=0, shadow=False)], ORANGE, pad=(36, 18))

S['rc_t'] = pill([emoji('👑', 96), text_sprite('Royal Canin', 80, sw=0, shadow=False)], RC_RED)
S['rc_1'] = pill([emoji('🌭', 72), text_sprite('Dachshund adulto', 60, sw=0, shadow=False)], GOLD)
S['rc_2'] = pill([emoji('🐶', 72), text_sprite('Puppy Mini · 2 a 10 meses', 56, sw=0, shadow=False)], (40, 150, 215))
S['rc_3'] = pill([emoji('🧠', 70), text_sprite('Desarrollo del cerebro', 54, fill=DARK, sw=0, shadow=False)], YELLOW, pad=(36, 18))

S['ph_h'] = text_sprite('¡Vení a verlos!', 120, fill=WHITE, stroke=PURPLE, sw=12)
S['camera'] = emoji('📸', 120)
pol_rots = [-7, 6, -4, 8, -6, 5]
S['pols'] = [polaroid(p, 640 if i % 2 == 0 else 600, 0) for i, p in enumerate(PHOTOS)]

S['te'] = text_sprite('¡Te esperamos!', 130, fill=WHITE, stroke=PURPLE, sw=13)
S['addr_card'] = card(940, 560, (255, 255, 255), (255, 241, 210), outline=ORANGE)
S['pin'] = emoji('📍', 170)
S['addr_h'] = text_sprite('ESTAMOS EN', 74, fill=ORANGE, stroke=WHITE, sw=7, shadow=False)
S['addr_1'] = text_sprite('Roque Sáenz Peña', 100, fill=PURPLE, stroke=WHITE, sw=8, shadow=False)
S['addr_2'] = text_sprite('y Garibaldi', 116, fill=PURPLE, stroke=WHITE, sw=9, shadow=False)
S['paw'] = emoji('🐾', 90); S['heart2'] = emoji('🧡', 80); S['heart3'] = emoji('💛', 80)

random.seed(9)
confetti = [(random.uniform(0, W), random.uniform(-1.5, 0), random.uniform(260, 520), random.uniform(-60, 60),
             random.uniform(0, 6.28), random.choice(range(6)), random.uniform(0.6, 1.1)) for _ in range(24)]
hearts = [(random.choice([random.uniform(50, 200), random.uniform(W - 200, W - 50)]), random.uniform(0, 4),
           random.uniform(160, 300), random.uniform(0.5, 0.9), random.choice(['heart2', 'heart3', 'paw'])) for _ in range(14)]


def gradient_band(frame, y0, y1, alpha=150, top=True):
    band_ = np.zeros((y1 - y0, W, 4), np.uint8)
    k = np.linspace(1, 0, y1 - y0) if top else np.linspace(0, 1, y1 - y0)
    band_[..., 0] = 30; band_[..., 1] = 10; band_[..., 2] = 50
    band_[..., 3] = (k * alpha).astype(np.uint8)[:, None]
    frame.alpha_composite(Image.fromarray(band_, 'RGBA'), (0, y0))

BANDS = {}
def band(frame, key, *specs):
    if key not in BANDS:
        b = Image.new('RGBA', (W, H))
        for sp in specs: gradient_band(b, *sp)
        BANDS[key] = b
    frame.alpha_composite(BANDS[key])

def slide(frame, sp, y, lt, t0, frm=1):
    if lt >= t0:
        kk = ease_out_back((lt - t0) / 0.45, 1.3)
        place(frame, sp, W / 2 + frm * (1 - kk) * 1100, y)


def overlay(frame, name, lt):
    if name == 'intro':
        band(frame, 'bot', (1050, H, 220, False))
        for (x, y0, vy, vr, ph, ci, sc) in confetti:
            y = y0 * H + vy * lt
            if lt > 0.3 and -100 < y < H + 100:
                place(frame, S['conf'][ci], x + 30 * math.sin(lt * 2 + ph), y, sc, rot=vr * lt)
        place(frame, S['lleg'], W / 2, 1260, ease_out_elastic((lt - 0.15) / 0.9) if lt > 0.15 else 0, rot=math.sin(lt * 6) * 3)
        place(frame, S['ex'], W / 2, 1450, pop_in(lt, 0.5), rot=-2)
        place(frame, S['y'], W / 2, 1570, pop_in(lt, 0.75))
        place(frame, S['rc'], W / 2, 1700, pop_in(lt, 0.9), rot=2)
        place(frame, S['fire'], 120, 1440, pop_in(lt, 1.1) * (0.9 + 0.1 * math.sin(lt * 10)))
        place(frame, S['party'], W - 120, 1700, pop_in(lt, 1.25), rot=math.sin(lt * 5) * 12)
        place(frame, S['spark'], W - 130, 1240, pop_in(lt, 1.3) * (0.8 + 0.2 * math.sin(lt * 9)))

    elif name in ('excellent', 'royal'):
        band(frame, 'bot2', (1080, H, 225, False))
        if name == 'excellent':
            slide(frame, S['ex_t'], 1300, lt, 0.1, -1)
            slide(frame, S['ex_1'], 1450, lt, 0.35, 1)
            slide(frame, S['ex_2'], 1565, lt, 0.5, 1)
            place(frame, S['ex_3'], W / 2, 1700, pop_in(lt, 1.0))
            place(frame, S['ex_4'], W / 2, 1815, pop_in(lt, 1.35))
            place(frame, S['kg'], W - 150, 1130, pop_in(lt, 0.8), rot=8 + math.sin(lt * 6) * 4)
        else:
            slide(frame, S['rc_t'], 1300, lt, 0.1, -1)
            slide(frame, S['rc_1'], 1460, lt, 0.35, 1)
            slide(frame, S['rc_2'], 1600, lt, 0.55, -1)
            place(frame, S['rc_3'], W / 2, 1750, pop_in(lt, 1.0))
            place(frame, S['kg'], 150, 1130, pop_in(lt, 0.8), rot=-8 - math.sin(lt * 6) * 4)
        place(frame, S['star'], W - 110, 1300 - abs(math.sin(lt * 5)) * 25, pop_in(lt, 0.9) * 0.8, rot=math.sin(lt * 4) * 12)

    elif name == 'photos':
        place(frame, S['ph_h'], W / 2, 250, ease_out_elastic((lt - 0.05) / 0.8) if lt > 0.05 else 0)
        place(frame, S['camera'], W / 2, 420, pop_in(lt, 0.2), rot=math.sin(lt * 6) * 10)
        n = len(S['pols'])
        if n:
            slot = 3.5 / n
            i = min(int(lt / slot), n - 1)
            u = lt - i * slot
            # aparece con rebote y desaparece achicándose y girando
            sin_ = ease_out_back(u / 0.3, 1.6)
            sout = 1 - ease_in((u - (slot - 0.18)) / 0.18) if i < n - 1 else 1.0
            sc = sin_ * sout
            rot = pol_rots[i % len(pol_rots)] * (1 + (1 - sout) * 2)
            # la foto anterior queda debajo, tenue
            if i > 0 and u < 0.3:
                place(frame, S['pols'][i - 1], W / 2, 1080, 1 - u / 0.3, rot=pol_rots[(i - 1) % len(pol_rots)])
            place(frame, S['pols'][i], W / 2, 1080, sc, rot=rot)
            place(frame, S['heart'], 150 if i % 2 else W - 150, 1650, pop_in(u, 0.15) * sout * 0.9)

    elif name == 'outro':
        for (x, t0, vy, sc, kind) in hearts:
            y = H + 80 - ((lt + t0) % 4.0) * vy * 1.6
            place(frame, S[kind], x + 25 * math.sin(lt * 3 + t0), y, sc, alpha=0.85)
        place(frame, S['te'], W / 2, 330, ease_out_elastic((lt - 0.1) / 0.9) if lt > 0.1 else 0)
        cy = 980
        k = ease_out_back((lt - 0.2) / 0.5, 1.5) if lt > 0.2 else 0
        place(frame, S['addr_card'], W / 2, cy + (1 - k) * 1100)
        place(frame, S['pin'], W / 2, cy - 290 - abs(math.sin(lt * 4.5)) * 50, pop_in(lt, 0.45))
        place(frame, S['addr_h'], W / 2, cy - 120, pop_in(lt, 0.6))
        place(frame, S['addr_1'], W / 2, cy + 20, pop_in(lt, 0.75))
        place(frame, S['addr_2'], W / 2, cy + 160, pop_in(lt, 0.9))
        place(frame, S['dog'], W / 2, 1560 - abs(math.sin(lt * 5)) * 45, pop_in(lt, 1.1) * 0.85, rot=math.sin(lt * 5) * 8)


out = sys.argv[1]
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-i', 'music_ex.wav', '-map', '0:v', '-map', '1:a',
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
