import numpy as np, wave, sys

SR = 44100
DUR = 30.0
BPM = 140
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

# ---------- song (versión más alegre: 140 BPM, mayor, saltarina) ----------
def whistle(note, d):
    t = tt(d)
    f = midi(note) * (1 + 0.006 * np.sin(2 * np.pi * 6 * t) * np.clip((t - 0.08) / 0.1, 0, 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + 0.12 * np.sin(2 * ph)
    env = np.clip(t / 0.02, 0, 1) * np.clip((d - t) / 0.04, 0, 1)
    return s * env * 0.22

def glock(note, d=0.5):
    t = tt(d)
    f = midi(note)
    s = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 12)
    return s * np.exp(-t * 7) * np.clip(t / 0.002, 0, 1) * 0.18

def tamb():
    t = tt(0.09)
    n = rng.standard_normal(len(t)); n = n - lowpass(n, 8000)
    return n * np.exp(-t * 45) * 0.10

def stab(notes, d=0.16):
    t = tt(d)
    s = np.zeros_like(t)
    for n in notes:
        f = midi(n)
        for h in range(1, 6):
            s += np.sin(2 * np.pi * f * h * t) / h ** 1.3 * np.exp(-t * (10 + h * 3))
    return s * np.clip((d - t) / 0.02, 0, 1) * np.clip(t / 0.003, 0, 1) * 0.12

# I - IV - V - IV en Re mayor (soleado)
chords = [[62, 66, 69], [62, 67, 71], [64, 69, 73], [62, 67, 71]]
roots = [38, 43, 45, 43]
# melodías saltarinas (offset en beats, nota, largo)
melA = [(0, 74, .5), (.5, 78, .5), (1, 81, .75), (1.75, 78, .25), (2, 81, .5), (2.5, 83, .5), (3, 81, 1),
        (4, 79, .5), (4.5, 83, .5), (5, 86, .75), (5.75, 83, .25), (6, 81, .5), (6.5, 78, .5), (7, 76, 1)]
melB = [(0, 81, .25), (.25, 83, .25), (.5, 85, .5), (1, 86, .5), (1.5, 81, .5), (2, 78, .5), (2.5, 81, .5), (3, 83, 1),
        (4, 83, .5), (4.5, 81, .5), (5, 79, .5), (5.5, 76, .5), (6, 78, .5), (6.5, 76, .5), (7, 74, 1)]

bars = int(DUR / (BEAT * 4)) + 1
for b in range(bars):
    t0 = b * 4 * BEAT
    ci = b % 4
    for k in range(4):
        add(music, t0 + k * BEAT, kick(), gain=1.0)
        if k in (1, 3):
            add(music, t0 + k * BEAT, snare(), gain=0.8)
        add(music, t0 + k * BEAT, clap(), pan=0.1, gain=0.9 if k in (1, 3) else 0.45)
        add(music, t0 + (k + .5) * BEAT, hat(open_=(k == 3)), pan=0.35, gain=0.9)
        for s16 in range(4):
            add(music, t0 + (k + s16 / 4) * BEAT, tamb(), pan=-0.45, gain=1.0 if s16 % 2 else 0.5)
    # bajo saltarín en octavas
    r = roots[ci]
    for off in (0, .5, 1, 1.5, 2, 2.5, 3, 3.5):
        add(music, t0 + off * BEAT, bass(r + (12 if (off * 2) % 2 else 0), BEAT * 0.4), gain=0.9)
    # acordes staccato a contratiempo (estilo "bouncy")
    for off in (.5, 1.5, 2.5, 3.5, 3.75):
        add(music, t0 + off * BEAT, stab(chords[ci]), pan=0.25)
    # rasgueo
    for off in (0, 1, 2, 2.75, 3.25):
        for j, n in enumerate(chords[ci]):
            add(music, t0 + off * BEAT + j * 0.007, pluck(n, 0.3, bright=1.3), pan=-0.3 + j * 0.05, gain=0.55)
    # glockenspiel arpegiado
    for k, n in enumerate([chords[ci][0] + 12, chords[ci][1] + 12, chords[ci][2] + 12, chords[ci][1] + 24]):
        add(music, t0 + k * BEAT + .25 * BEAT, glock(n), pan=0.4, gain=0.8)
    # melodía silbada + campanita doblando, desde el compás 1
    if b >= 1 and (b - 1) % 2 == 0:
        mel = melA if ((b - 1) // 2) % 2 == 0 else melB
        for off, n, ln in mel:
            add(music, t0 + off * BEAT, whistle(n, ln * BEAT * 0.95), pan=0.1, gain=1.0)
            add(music, t0 + off * BEAT, bell(n + 12, ln * BEAT + 0.15), pan=-0.1, gain=0.35)

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

events = [
    (0.05, whoosh(0.6), 0), (0.40, boing(), 0), (0.65, pop(), -0.4), (0.88, pop(), 0.4), (1.1, sparkle(), 0),
    (2.2, whoosh(0.45), -0.3), (2.5, pop(), 0.3),
    (3.8, whoosh(0.45), 0.3), (4.1, pop(), -0.3),
    (5.4, whoosh(0.55), 0), (5.85, ding(), 0), (6.2, pop(), 0),
    (8.4, whoosh(0.55), 0), (8.8, ding(), 0), (9.42, pop(), -0.3), (10.7, pop(), 0.3),
    (12.4, whoosh(0.55), 0), (12.75, sparkle(), 0), (13.4, boing(), 0),
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
