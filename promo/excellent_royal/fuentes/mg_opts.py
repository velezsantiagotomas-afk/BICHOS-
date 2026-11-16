"""Muestra de 4 opciones para mostrar las fotos (escena Excellent)."""
src = open('mg.py').read()
exec(src[:src.index("out = sys.argv[1]")])

CUT = {n: Image.open(f) for n, f in [('p1', 'cut/1_ex_peq_gc.png'), ('p2', 'cut/2_ex_med_gc.png'),
                                     ('p3', 'cut/3_dach_gc.png'), ('p4', 'cut/4_puppy.png')]}
def fit(im, h):
    return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
C1, C2 = fit(CUT['p1'], 820), fit(CUT['p2'], 760)

def shadowed(im, blur=18, off=(0, 30), a=140):
    pad = 60
    c = Image.new('RGBA', (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new('RGBA', c.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, a), (pad + off[0], pad + off[1]), im.getchannel('A'))
    c = Image.alpha_composite(c, sh.filter(ImageFilter.GaussianBlur(blur)))
    c.alpha_composite(im, (pad, pad))
    return c
SC1, SC2 = shadowed(C1), shadowed(C2)

def full_photo(path):
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    r = max(W / im.width, H / im.height) * 1.15
    return im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
F1, F2 = full_photo(FOT + '1_ex_peq_ok.jpg'), full_photo(FOT + '2_ex_med_ok.jpg')

def circle_photo(path, d):
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    s = d / min(im.size); im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    im = im.crop(((im.width - d) // 2, int((im.height - d) * 0.45), (im.width - d) // 2 + d, int((im.height - d) * 0.45) + d))
    m = Image.new('L', (d, d), 0); ImageDraw.Draw(m).ellipse((0, 0, d - 1, d - 1), fill=255)
    out = Image.new('RGBA', (d, d), (0, 0, 0, 0)); out.paste(im, (0, 0), m)
    return out
O1 = circle_photo(FOT + '1_ex_peq_ok.jpg', 640); O2 = circle_photo(FOT + '2_ex_med_ok.jpg', 640)

LABELS = {k: pill([text_sprite(t, 48, fill=INK, sw=0, shadow=False)], WHITE, pad=(30, 14), outline=INK, ow=4)
          for k, t in [('A', 'OPCIÓN A · Recorte flotante'), ('B', 'OPCIÓN B · Pantalla completa'),
                       ('C', 'OPCIÓN C · Foto en círculo'), ('D', 'OPCIÓN D · Carrusel deslizante')]}

def chips(frame, lt):
    slide_in(frame, S['ex_c1'], W / 2, 1465, lt, 0.9, (-1, 0))
    slide_in(frame, S['ex_c2'], W / 2, 1600, lt, 1.05, (1, 0))
    slide_in(frame, S['ex_c3'], W / 2, 1735, lt, 1.3, (0, 1), dist=700)

def title(frame, lt):
    bar_reveal(frame, WHITE, S['ex_h1'], W / 2, 300, lt, 0.1, pad=30)
    place(frame, S['ex_h2'], W / 2, 430, pop_in(lt, 0.25, 0.5))

def opt_A(frame, lt):   # bolsas recortadas que entran y flotan, con un círculo de luz atrás
    r = 380 + 20 * math.sin(lt * 3)
    glow = Image.new('RGBA', (W, H)); ImageDraw.Draw(glow).ellipse((W / 2 - r, 900 - r, W / 2 + r, 900 + r), fill=(255, 220, 120, 90))
    frame.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40)))
    title(frame, lt)
    if lt > 0.3:
        k = ease_out_back((lt - 0.3) / 0.5, 1.4)
        place(frame, SC1, 330 - (1 - k) * 900, 960 + 15 * math.sin(lt * 2.5), 0.8, rot=-6 + 3 * math.sin(lt * 2))
    if lt > 0.5:
        k = ease_out_back((lt - 0.5) / 0.5, 1.4)
        place(frame, SC2, 770 + (1 - k) * 900, 990 + 15 * math.sin(lt * 2.5 + 1.5), 0.82, rot=6 - 3 * math.sin(lt * 2 + 1))
    place(frame, S['kg'], W - 140, 640, pop_in(lt, 0.8), rot=math.sin(lt * 3) * 12)
    chips(frame, lt)

def opt_B(frame, lt):   # foto a pantalla completa con zoom lento y cambio con barrido
    img = F1 if lt < 1.75 else F2
    u = (lt % 1.75) / 1.75
    z = 1 + 0.08 * u
    cw, ch = int(W / z * 1.0), int(H / z * 1.0)
    x = (img.width - cw) // 2; y = (img.height - ch) // 2
    ph = img.crop((x, y, x + cw, y + ch)).resize((W, H), Image.BILINEAR).convert('RGBA')
    frame.paste(ph, (0, 0))
    g = np.zeros((H, W, 4), np.uint8); k = np.clip((np.arange(H) - 1050) / 600, 0, 1)
    g[..., 0] = 120; g[..., 1] = 8; g[..., 2] = 35; g[..., 3] = (k * 235).astype(np.uint8)[:, None]
    frame.alpha_composite(Image.fromarray(g, 'RGBA'))
    if 1.6 < lt < 1.9:                     # mini barrido entre fotos
        v = (lt - 1.6) / 0.3
        l = Image.new('RGBA', (W, H)); x0 = -1400 + v * 3600
        ImageDraw.Draw(l).polygon([(x0, 0), (x0 + 700, 0), (x0 + 300, H), (x0 - 400, H)], fill=YELLOW + (255,))
        frame.alpha_composite(l)
    place(frame, S['ex_h2'], W / 2, 1300, pop_in(lt, 0.2, 0.5))
    chips(frame, lt)

def opt_C(frame, lt):   # foto dentro de un círculo con anillo de colores girando
    title(frame, lt)
    img = O1 if lt < 1.75 else O2
    k = ease_out_back(((lt % 1.75) - 0.05) / 0.45, 1.6) if (lt % 1.75) > 0.05 else 0
    ring = Image.new('RGBA', (760, 760), (0, 0, 0, 0)); d = ImageDraw.Draw(ring)
    for i, col in enumerate([YELLOW, ORANGE, PINK, WHITE]):
        a0 = lt * 120 + i * 90
        d.arc((10, 10, 750, 750), a0, a0 + 70, fill=col + (255,), width=26)
    place(frame, ring, W / 2, 940, k)
    place(frame, img, W / 2, 940, k)
    place(frame, S['kg'], W - 170, 680, pop_in(lt, 0.8), rot=math.sin(lt * 3) * 12)
    chips(frame, lt)

def opt_D(frame, lt):   # carrusel: las bolsas recortadas pasan deslizándose de derecha a izquierda
    title(frame, lt)
    items = [SC1, SC2, SC1, SC2]
    pos = lt * 1.6                        # cuántas "casillas" avanzó
    for i, it in enumerate(items):
        x = W / 2 + (i - pos + 0.6) * 700
        if -400 < x < W + 400:
            dist = abs(x - W / 2) / 700
            sc = 0.95 * (1 - 0.35 * clamp(dist)); al = 1 - 0.5 * clamp(dist)
            place(frame, it, x, 960, sc, alpha=al)
    chips(frame, lt)

OPTS = [('A', opt_A), ('B', opt_B), ('C', opt_C), ('D', opt_D)]
SEG = 3.5
out = sys.argv[1]
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', '-i', 'music_mg.wav', '-map', '0:v', '-map', '1:a',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out],
                       stdin=subprocess.PIPE)
for fi in range(int(SEG * 4 * FPS)):
    t = fi / FPS; i = int(t // SEG); lt = t - i * SEG
    key, fn = OPTS[i]
    frame = background('excellent', t)
    fn(frame, lt)
    place(frame, LABELS[key], W / 2, 110)
    if lt < 0.12 and i > 0:
        frame.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(220 * (1 - lt / 0.12)))))
    enc.stdin.write(frame.convert('RGB').tobytes())
enc.stdin.close(); enc.wait()
print('done')
