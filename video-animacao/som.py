"""Trilha (musica.wav) e efeitos (sfx.wav) a partir da linha do tempo."""
import json, numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000
L = json.load(open("linha.json", encoding="utf-8"))
DUR = L["duracao"]
N = int(DUR * SR) + SR
C = {c["id"]: c for c in L["cenas"]}
M = L["marcos"]
rng = np.random.default_rng(7)

def tt(n): return np.arange(n) / SR
def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], btype="band", fs=SR, output="sos"), x)
def lp(x, f, o=2): return sosfilt(butter(o, f, btype="low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, btype="high", fs=SR, output="sos"), x)
def put(buf, x, t0, g=1.0, pan=0.0):
    i = int(t0 * SR)
    if i < 0: x = x[-i:]; i = 0
    n = min(len(x), buf.shape[0] - i)
    if n <= 0: return
    l, r = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
    buf[i:i + n, 0] += x[:n] * g * l * 1.414
    buf[i:i + n, 1] += x[:n] * g * r * 1.414

# ───────────────────────── MÚSICA ─────────────────────────
BPM = 90.0; BEAT = 60 / BPM; BAR = 4 * BEAT
ACORDES = [(50, [50, 54, 57, 62, 66]),   # D
           (47, [47, 50, 54, 59, 62]),   # Bm
           (43, [43, 50, 55, 59, 62]),   # G
           (45, [45, 49, 52, 57, 61])]   # A
NIVEL = {"abertura": 1, "origem": 1.5, "2014": 2, "2022": 1.5, "2025": 2, "pessoas": 2.5, "filmes": 2,
         "f-flores": 3, "f-lidia": 3, "f-fita": 3, "f-camadas": 3, "f-toto": 3, "f-olhares": 3, "f-folia": 3,
         "temas": 1, "mostras": 1.5, "escola": 2.5, "acoes": 3, "futuro": 2, "fecho": 1}

def nivel_em(t):
    for c in L["cenas"]:
        if c["ini"] <= t < c["fim"]: return NIVEL[c["id"]]
    return 1
# curva de nível suavizada (amostrada a 100 Hz)
tg = np.arange(0, DUR + 1, .01)
nv = np.array([nivel_em(x) for x in tg])
k = np.ones(40) / 40
nvs = np.convolve(np.pad(nv, (20, 20), mode="edge"), k, mode="same")[20:-20]
def nivel(t): return np.interp(t, tg, nvs)
def ganho(lim, t, larg=.5): return np.clip((nivel(t) - lim + larg) / larg, 0, 1)

FIM_MUS = M["fecho"]["lema_fim"] + 0.05   # acorde final
mus = np.zeros((N, 2))

def saw(f, n, fase=0):
    x = (tt(n) * f + fase) % 1.0
    return 2 * x - 1

# pad
nb = int(np.ceil(FIM_MUS / BAR))
for b in range(nb):
    t0 = b * BAR
    raiz, notas = ACORDES[b % 4]
    n = int((BAR + 1.2) * SR); x = tt(n)
    env = np.minimum(1, x / .5) * np.clip((BAR + 1.2 - x) / 1.0, 0, 1)
    for ch, det in ((0, -6), (1, 6)):
        sig = np.zeros(n)
        for m in notas[1:4]:
            f = mtof(m + 12)
            for d in (-det, 0, det):
                sig += saw(f * 2 ** (d / 1200), n, rng.random())
        sig = lp(sig, 1500) * env * .045
        i = int(t0 * SR); m_ = min(n, N - i)
        g = ganho(0.5, t0 + x[:m_]) * (0.8 + .25 * (nivel(t0) < 1.6))
        mus[i:i + m_, ch] += sig[:m_] * g

# violão (pluck aditivo)
def pluck(f, dur=1.6, brilho=1.0):
    n = int(dur * SR); x = tt(n); s = np.zeros(n)
    for h in range(1, 9):
        fh = f * h * (1 + .0006 * h * h)
        if fh > SR / 2.2: break
        s += np.sin(2 * np.pi * fh * x) * (brilho / h ** 1.25) * np.exp(-x * (2.2 + h * 1.4))
    ruido = rng.standard_normal(n) * np.exp(-x / .004) * .3
    s += hp(ruido, 2000)
    return s * np.minimum(1, x / .002)
PADRAO = [0, 2, 3, 4, 3, 1, 3, 2]
for b in range(nb):
    raiz, notas = ACORDES[b % 4]
    for j in range(8):
        t0 = b * BAR + j * BEAT / 2
        if t0 > FIM_MUS - .1: break
        m = notas[PADRAO[j]] + 12
        g = ganho(1.0, t0) * (.13 if j % 2 == 0 else .095) * (1.15 if nivel(t0) >= 2.5 else 1)
        if g > 0.002: put(mus, pluck(mtof(m), 1.4, 1.0), t0 + rng.normal(0, .004), g, .32)

# baixo
for b in range(nb):
    raiz, _ = ACORDES[b % 4]
    for j, ac in ((0, 1), (2, .8), (3.5, .6)):
        t0 = b * BAR + j * BEAT
        if t0 > FIM_MUS - .1: break
        g = ganho(1.5, t0) * .28 * ac
        if g < .002: continue
        n = int(.9 * SR); x = tt(n); f = mtof(raiz - 12 + 12)
        s = (np.sin(2 * np.pi * f * x) + .35 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 3.2) * np.minimum(1, x / .006)
        put(mus, np.tanh(s * 1.4), t0, g, 0)

# bateria
def bumbo():
    n = int(.45 * SR); x = tt(n); f = 45 + 80 * np.exp(-x * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9) + hp(rng.standard_normal(n), 3000) * np.exp(-x / .003) * .2
def caixa():
    n = int(.3 * SR); x = tt(n)
    return bp(rng.standard_normal(n), 1200, 7000) * np.exp(-x * 18) * .7 + np.sin(2 * np.pi * 185 * x) * np.exp(-x * 25) * .5
def chimbal(aberto=False):
    n = int((.18 if aberto else .05) * SR); x = tt(n)
    return hp(rng.standard_normal(n), 7000) * np.exp(-x * (14 if aberto else 70))
BU, CX = bumbo(), caixa()
nbeats = int(FIM_MUS / BEAT)
for i in range(nbeats):
    t0 = i * BEAT
    lv = nivel(t0)
    gk = ganho(2.0, t0) * (.55 if lv < 2.4 else .85)
    if gk > .01 and (i % 4 in (0, 2) or (lv >= 2.9 and i % 4 == 3 and i % 8 == 7)):
        put(mus, BU, t0, gk, 0)
    gs = ganho(2.5, t0) * .5
    if gs > .01 and i % 4 in (1, 3): put(mus, CX, t0, gs, .05)
    gh = ganho(2.0, t0) * .16
    if gh > .005:
        put(mus, chimbal(), t0, gh, -.25)
        put(mus, chimbal(i % 2 == 1 and lv >= 2.9), t0 + BEAT / 2, gh * .7, -.25)

# sininho (abertura e fecho)
def sino(f, dur=2.4):
    n = int(dur * SR); x = tt(n)
    return (np.sin(2 * np.pi * f * x) + .4 * np.sin(2 * np.pi * f * 2.76 * x) * np.exp(-x * 3) + .2 * np.sin(2 * np.pi * f * 5.4 * x) * np.exp(-x * 6)) * np.exp(-x * 1.8) * np.minimum(1, x / .003)
for k, m in enumerate([78, 81, 86, 85]):
    put(mus, sino(mtof(m)), .4 + k * BEAT, .06, -.2 + .15 * k)
for k, m in enumerate([78, 81, 85, 86]):
    put(mus, sino(mtof(m)), M["fecho"]["lema"] + k * BEAT * .75, .05, .2 - .12 * k)

# subida antes da montagem
a, b = C["filmes"]["ini"] + .3, C["f-flores"]["ini"]
n = int((b - a) * SR); x = tt(n)
rz = rng.standard_normal(n)
sweep = np.zeros(n)
for j in range(0, n, 2400):
    seg = rz[j:j + 2400]; fc = 400 + 7000 * (j / n) ** 2
    sweep[j:j + len(seg)] = bp(seg, fc * .7, min(fc * 1.4, 20000))
put(mus, sweep * (x / x[-1]) ** 2 * .35, a, 1, 0)
tom = np.sin(2 * np.pi * np.cumsum(220 + 440 * (x / x[-1]) ** 2) / SR) * (x / x[-1]) ** 2 * .06
put(mus, tom, a, 1, 0)
# prato na entrada da montagem e do fecho
def prato(dur=2.5):
    n = int(dur * SR); x = tt(n)
    return hp(rng.standard_normal(n), 4000) * np.exp(-x * 1.6) * .5
put(mus, prato(), C["f-flores"]["ini"], .35, .1)
put(mus, BU, C["f-flores"]["ini"], .9, 0)

# acorde final
t0 = FIM_MUS
raiz, notas = ACORDES[0]
n = int((DUR - t0 + .5) * SR); x = tt(n)
env = np.minimum(1, x / .08) * np.exp(-x * .45)
fin = np.zeros(n)
for m in notas:
    fin += pluck(mtof(m + 12), DUR - t0 + .5, .8)[:n] * .5
    fin += lp(saw(mtof(m + 12), n), 1800) * env * .05
put(mus, fin, t0, .55, 0)
put(mus, sino(mtof(86), 4), t0 + .05, .07, 0)
put(mus, BU, t0, .5, 0)

# fade geral do fim
fade_i = int((DUR - 1.2) * SR)
mus[fade_i:] *= np.linspace(1, 0, N - fade_i)[:, None]

# reverb curto (convolução)
nr = int(1.6 * SR); xr = tt(nr)
ir = rng.standard_normal((nr, 2)) * np.exp(-xr * 3.2)[:, None]
ir[:, 0] = lp(ir[:, 0], 6000); ir[:, 1] = lp(ir[:, 1], 6000)
wet = np.stack([fftconvolve(mus[:, c], ir[:, c])[:N] for c in range(2)], 1)
mus = mus + wet * .045
mus /= np.max(np.abs(mus)) / .9
wavfile.write("musica.wav", SR, mus.astype(np.float32))
print("musica ok", mus.shape[0] / SR)

# ───────────────────────── EFEITOS ─────────────────────────
fx = np.zeros((N, 2))
def whoosh(dur=.7, pico=.55, lo=300, hi=6000, cheio=1.0):
    n = int(dur * SR); x = tt(n); r = rng.standard_normal(n)
    out = np.zeros(n)
    for j in range(0, n, 1200):
        fc = lo * (hi / lo) ** (j / n)
        seg = r[j:j + 1200]; out[j:j + len(seg)] = bp(seg, max(40, fc * .6), min(fc * 1.6, 22000), 1)
    env = np.where(x < pico * dur, (x / (pico * dur)) ** 2, np.exp(-(x - pico * dur) / (dur * .18)))
    return out * env * cheio
def baque(f=55, dur=.6, g=1.0):
    n = int(dur * SR); x = tt(n)
    s = np.sin(2 * np.pi * np.cumsum(f + 40 * np.exp(-x * 20)) / SR) * np.exp(-x * 6) + lp(rng.standard_normal(n), 900) * np.exp(-x * 30) * .4
    return s * g
def brilho(dur=1.2):
    n = int(dur * SR); x = tt(n); s = np.zeros(n)
    for f in (2093, 2637, 3136, 3951, 4699):
        s += np.sin(2 * np.pi * f * x + rng.random() * 6) * np.exp(-x * (3 + rng.random() * 3))
    return s * np.minimum(1, x / .01) * .2
def plim(f=1320):
    n = int(.35 * SR); x = tt(n)
    return (np.sin(2 * np.pi * f * x) + .3 * np.sin(2 * np.pi * f * 2 * x)) * np.exp(-x * 14) * np.minimum(1, x / .002)
def clique(g=1.0):
    n = int(.012 * SR); x = tt(n)
    return hp(rng.standard_normal(n), 2500) * np.exp(-x * 600) * g
def tique():
    n = int(.03 * SR); x = tt(n)
    return (bp(rng.standard_normal(n), 2000, 6000) * np.exp(-x * 250) + np.sin(2 * np.pi * 1800 * x) * np.exp(-x * 300) * .4)

PAN = {"iris": 0, "cortina": -.4, "flash": 0, "wipe": .4, "zoom": 0, "whip": .3}
for c in L["cenas"]:
    tr = c["trans"]
    if not tr: continue
    if tr == "whip":
        put(fx, whoosh(.32, .5, 600, 9000), c["ini"] - .16, .32, .3)
        put(fx, clique(1.0), c["ini"], .5, 0)
    elif tr == "flash":
        put(fx, whoosh(.6, .7, 400, 8000), c["ini"] - .42, .3, 0)
        put(fx, brilho(), c["ini"], .55, 0)
    else:
        put(fx, whoosh(.85, .6, 250, 7000), c["ini"] - .5, .42, PAN[tr])

# impactos: pousos dos odômetros e batidas da câmera
impactos = [M["2014"]["ano"], M["2022"]["ano"], M["2025"]["ano"], M["pessoas"]["num"], M["filmes"]["num"], M["futuro"]["ano"],
            M["abertura"]["letras"] + .75, M["fecho"]["letras"] + .75, M["2022"]["flores"] + .35]
for T in impactos: put(fx, baque(52, .7), T, .55, 0)
# tique-tique dos odômetros
for T, d in ((M["2014"]["ano"], 1.6), (M["2022"]["ano"], 1.1), (M["2025"]["ano"], 1.0), (M["pessoas"]["num"], 1.0), (M["filmes"]["num"], .9), (M["futuro"]["ano"], 1.0)):
    t = T - d
    while t < T - .03:
        p = (t - (T - d)) / d
        put(fx, tique(), t, .18, .2)
        t += .03 + .17 * p ** 2
# chips, blocos, cartões, painéis
for k, nome in enumerate(["chip1", "chip2", "chip3"]): put(fx, plim(1047 * 2 ** (k * 4 / 12)), M["origem"][nome], .2, -.2)
put(fx, plim(1568), M["origem"]["casa"], .18, .3)
for k in range(5): put(fx, baque(70 + 12 * k, .4), M["pessoas"]["b%d" % (k + 1)], .45, -.6 + .3 * k)
for k in range(4): put(fx, plim(880 * 2 ** ([0, 4, 7, 12][k] / 12)), M["acoes"]["c%d" % (k + 1)], .18, -.3)
for k in range(4):
    put(fx, baque(90, .35) * .6, M["acoes"]["f%d" % (k + 1)] - .08, .5, .2 + .1 * k)
    put(fx, whoosh(.25, .6, 1500, 6000) * .5, M["acoes"]["f%d" % (k + 1)] - .2, .5, .2 + .1 * k)
for k in range(4): put(fx, baque(48, .8), M["temas"]["p%d" % (k + 1)], .5, -.5 + .33 * k)
for nome in ("m1", "m2"): put(fx, plim(660), M["mostras"][nome], .14, 0)
put(fx, plim(1760), M["2025"]["check"] + .95, .22, .4)
for k, nome in enumerate(["r1", "r2", "r3"]): put(fx, whoosh(.4, .7, 2000, 9000), M["futuro"][nome] - .25, .16, .4)
# digitação
def digita(T0, n, cps):
    for i in range(n):
        put(fx, clique(.7 + .3 * rng.random()), T0 + i / cps + rng.normal(0, .004), .22, .1)
digita(M["abertura"]["local"], 31, 28); digita(M["2014"]["cine"] + .7, 28, 30); digita(M["2025"]["rotulo"], 16, 30)
digita(M["2025"]["check"] + .2, 68, 34); digita(M["escola"]["local"], 48, 34); digita(M["acoes"]["rotulo"] - .2, 15, 30)
digita(M["fecho"]["ponto"], 39, 30); digita(M["fecho"]["lema_fim"] + .55, 15, 14)
# carrinho
a, b = M["escola"]["carro_ini"], M["escola"]["carro_fim"]
n = int((b - a + .3) * SR); x = tt(n); f = 70 + 40 * (x / x[-1])
motor = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * .5
motor = lp(motor, 900) * np.minimum(1, x / .2) * np.clip((x[-1] - x) / .3, 0, 1)
put(fx, motor, a, .07, .5)
put(fx, plim(1175) + plim(1480) * .7, b, .2, .7)
# projetor na montagem
a, b = C["f-flores"]["ini"], C["temas"]["ini"]
t = a
while t < b:
    put(fx, clique(.5), t, .08, -.1); t += 1 / 24
# respiro no fim: brilho ao terminar a URL
put(fx, brilho(2.0), M["fecho"]["lema_fim"] + .55 + 15 / 14, .4, 0)

fx /= max(1e-9, np.max(np.abs(fx))) / .9
wavfile.write("sfx.wav", SR, fx.astype(np.float32))
print("sfx ok")
