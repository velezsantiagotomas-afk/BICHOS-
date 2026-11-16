import numpy as np, wave, sys

SR = 44100
DUR = 30.0
BPM = 124
BEAT = 60 / BPM
N = int(SR * DUR)
music = np.zeros((N, 2))
rng = np.random.default_rng(7)

def add(buf, t, sig, pan=0.0, gain=1.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i] * gain
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(sig), 0] += sig * l * 1.414
    buf[i:i + len(sig), 1] += sig * r * 1.414

def tt(d):
    return np.arange(int(d * SR)) / SR

def midi(n):
    return 440 * 2 ** ((n - 69) / 12)

def lowpass(x, cutoff):
    # simple FFT brickwall-ish lowpass with soft rolloff
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))

# ---------- instruments ----------
def kick():
    t = tt(0.35)
    f = 50 + 110 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * 0.9

def snare():
    t = tt(0.22)
    n = rng.standard_normal(len(t))
    n = n - lowpass(n, 1500)
    return (n * 0.5 + np.sin(2 * np.pi * 190 * t) * 0.5) * np.exp(-t * 20) * 0.45

def clap():
    t = tt(0.25)
    n = rng.standard_normal(len(t)); n = n - lowpass(n, 900)
    env = np.exp(-t * 18)
    for d in (0.0, 0.012, 0.024):
        env += (t >= d) * np.exp(-np.clip(t - d, 0, None) * 120) * 0.6
    return n * env * 0.22

def hat(open_=False):
    t = tt(0.25 if open_ else 0.06)
    n = rng.standard_normal(len(t)); n = n - lowpass(n, 7000)
    return n * np.exp(-t * (14 if open_ else 70)) * 0.18

def pluck(note, d=0.45, bright=1.0):
    t = tt(d)
    f = midi(note)
    s = np.zeros_like(t)
    for h in range(1, 9):
        s += np.sin(2 * np.pi * f * h * t) / h ** (1.6 / bright) * np.exp(-t * (4 + h * 2.2))
    att = np.clip(t / 0.004, 0, 1)
    return s * att * 0.28

def bell(note, d=0.6):
    t = tt(d)
    f = midi(note)
    s = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 6)
         + 0.15 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 9))
    vib = 1
    return s * np.exp(-t * 4.5) * np.clip(t / 0.005, 0, 1) * 0.30 * vib

def bass(note, d):
    t = tt(d)
    f = midi(note)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) + 0.12 * np.sign(np.sin(2 * np.pi * f * t))
    env = np.clip(t / 0.01, 0, 1) * np.exp(-t * 2.5)
    rel = np.clip((d - t) / 0.03, 0, 1)
    return lowpass(s * env * rel, 900) * 0.42

# ---------- song moderno: dance-pop 124 BPM con "pump" de sidechain ----------
def supersaw(notes, d):
    t = tt(d)
    s = np.zeros_like(t)
    for n in notes:
        for det in (-0.12, -0.05, 0, 0.05, 0.12):
            f = midi(n) * 2 ** (det / 12)
            ph = rng.uniform(0, 1)
            s += ((f * t + ph) % 1.0) * 2 - 1
    s = lowpass(s, 2600) / (len(notes) * 5)
    env = np.clip(t / 0.01, 0, 1) * np.clip((d - t) / 0.03, 0, 1)
    return s * env * 0.55

def sub(note, d):
    t = tt(d)
    f = midi(note)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.tanh(3 * np.sin(2 * np.pi * f * t))
    env = np.clip(t / 0.005, 0, 1) * np.clip((d - t) / 0.03, 0, 1)
    return s * env * 0.38

def lead(note, d):
    t = tt(d)
    f = midi(note)
    s = np.sign(np.sin(2 * np.pi * f * t)) * 0.5 + np.sin(2 * np.pi * 2 * f * t) * 0.3
    s = lowpass(s, 3200)
    return s * np.exp(-t * 7) * np.clip(t / 0.003, 0, 1) * 0.16

def snap():
    t = tt(0.08)
    n = rng.standard_normal(len(t)); n = n - lowpass(n, 2500)
    return n * np.exp(-t * 60) * 0.25

# vi - IV - I - V en Do (Am F C G)
chords = [[57, 60, 64], [53, 57, 60], [55, 60, 64], [55, 59, 62]]
roots = [33, 29, 36, 31]
hook = [(0, 76, .5), (.75, 76, .25), (1, 79, .5), (1.5, 76, .5), (2.5, 74, .25), (2.75, 72, .5), (3.25, 74, .5),
        (4, 72, .5), (4.75, 72, .25), (5, 76, .5), (5.5, 74, .5), (6.5, 72, .25), (6.75, 71, .5), (7.25, 72, .75)]

bars = int(DUR / (BEAT * 4)) + 1
for b in range(bars):
    t0 = b * 4 * BEAT
    ci = b % 4
    for k in range(4):
        add(music, t0 + k * BEAT, kick(), gain=1.15)
        if k in (1, 3):
            add(music, t0 + k * BEAT, clap(), gain=1.1)
            add(music, t0 + k * BEAT + 0.01, snap(), pan=0.2)
        add(music, t0 + (k + .5) * BEAT, hat(open_=True), pan=0.3, gain=0.8)
        for s16 in (0, 1, 3):
            add(music, t0 + (k + s16 / 4) * BEAT, hat(), pan=-0.3, gain=0.5)
    # rollito de hats al final de cada 2 compases (toque trap)
    if b % 2 == 1:
        for r in range(6):
            add(music, t0 + 3 * BEAT + r * BEAT / 6, hat(), pan=-0.2, gain=0.6)
    # acordes supersaw con bombeo (sidechain): un acorde por corchea, ducking tras cada kick
    for e in range(8):
        add(music, t0 + e * BEAT / 2, supersaw(chords[ci], BEAT / 2), gain=0.35 if e % 2 == 0 else 1.0)
    # sub bass en las corcheas a contratiempo
    for e in range(4):
        add(music, t0 + (e + .5) * BEAT, sub(roots[ci] + 12, BEAT * 0.45), gain=1.0)
    # hook pegadizo desde el compás 1
    if b >= 1 and (b - 1) % 2 == 0:
        for off, n, ln in hook:
            add(music, t0 + off * BEAT, lead(n, ln * BEAT + 0.1), pan=0.1)
            add(music, t0 + off * BEAT, bell(n + 12, ln * BEAT + 0.1), pan=-0.15, gain=0.25)

# ---------- SFX ----------
sfx = np.zeros((N, 2))

def whoosh(d=0.55):
    t = tt(d)
    n = rng.standard_normal(len(t))
    a = lowpass(n, 400); b = lowpass(n, 6000)
    m = np.sin(np.pi * t / d) ** 2
    out = a * (1 - m) + b * m
    env = np.sin(np.pi * t / d) ** 2
    return out * env * 0.55

def pop():
    t = tt(0.12)
    f = 900 * np.exp(-t * 25) + 300
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35) * 0.5

def ding():
    s = np.zeros(int(1.2 * SR))
    for n, dl in ((84, 0), (88, 0.09), (91, 0.18)):
        b = bell(n, 1.0)
        i = int(dl * SR); s[i:i + len(b)] += b
    return s * 1.1

def boing():
    t = tt(0.45)
    f = 220 + 160 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4) + 200 * np.exp(-t * 5)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6) * 0.45

def sparkle():
    s = np.zeros(int(1.0 * SR))
    for k, n in enumerate([88, 91, 93, 96, 100, 103]):
        b = bell(n, 0.5) * 0.6
        i = int(k * 0.06 * SR); s[i:i + len(b)] += b
    return s

def airhorn(d=0.5):
    t = tt(d)
    s = np.zeros_like(t)
    for f in (415, 466, 523):
        ph = 2 * np.pi * f * t * (1 + 0.004 * np.sin(2 * np.pi * 7 * t))
        s += ((ph / (2 * np.pi)) % 1.0) * 2 - 1        # diente de sierra
    s = lowpass(s, 3500)
    env = np.clip(t / 0.02, 0, 1) * np.clip((d - t) / 0.05, 0, 1)
    return np.tanh(s * env * 0.9) * 0.32

def riser(d=0.8):
    t = tt(d)
    f = 200 * (8 ** (t / d))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.15
    n = rng.standard_normal(len(t)); n = lowpass(n, 6000) - lowpass(n, 800)
    return (tone + n * 0.25) * (t / d) ** 2

def shutter():
    s = np.zeros(int(0.2 * SR))
    for dl, g in ((0.0, 1.0), (0.07, 0.7)):
        t = tt(0.05); n = rng.standard_normal(len(t)); n = n - lowpass(n, 2000)
        i0 = int(dl * SR); s[i0:i0 + len(t)] += n * np.exp(-t * 90) * 0.45 * g
    return s

events = [
    (0.05, airhorn(0.16), 0), (0.27, airhorn(0.16), 0), (0.49, airhorn(0.5), 0),
    (0.6, pop(), -0.3), (0.95, pop(), 0.3), (1.3, sparkle(), 0),
    (2.3, whoosh(0.45), 0), (2.65, pop(), -0.3), (3.0, pop(), 0.3), (3.35, pop(), 0),
    (5.3, whoosh(0.45), 0), (5.65, pop(), 0.3), (6.0, pop(), -0.3), (6.35, pop(), 0),
    (7.6, riser(0.8), 0), (8.5, whoosh(0.4), 0),
    (8.6, shutter(), -0.3), (9.45, shutter(), 0.3), (10.3, shutter(), -0.3), (11.15, shutter(), 0.3),
    (11.8, whoosh(0.55), 0), (12.1, ding(), 0), (12.9, sparkle(), 0),
]
for t0, s, p in events:
    add(sfx, t0, s, pan=p)

mix = music * 0.55 + sfx * 0.8
# fade in/out
fade = np.ones(N)
fi = int(0.05 * SR); fade[:fi] = np.linspace(0, 1, fi)
END = float(sys.argv[2]) if len(sys.argv) > 2 else 29.5
fo0 = int((END - 1.2) * SR); fo1 = int(END * SR)
fade[fo0:fo1] = np.linspace(1, 0, fo1 - fo0) ** 1.5
fade[fo1:] = 0
mix *= fade[:, None]
mix = np.tanh(mix * 1.3) / np.tanh(1.3)
mix = mix / np.max(np.abs(mix)) * 0.89
pcm = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('ok')
