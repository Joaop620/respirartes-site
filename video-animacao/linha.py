"""Monta a linha do tempo do vídeo a partir da narração do Carlos.
Saída: linha.json (cenas, transições, marcos, palavras e blocos de legenda), em tempo de vídeo."""
import json, re, unicodedata, difflib, sys

OFF = 1.8          # a narração começa 1,8 s depois do início do vídeo
FIM = 120.0        # duração total

W = [w for s in json.load(open("carlos_small.json")) for w in s["palavras"]]

# (cena, texto como deve aparecer na legenda)
FRASES = [
    ("abertura", "Ji-Paraná, interior de Rondônia."),
    ("abertura", "Aqui, um grupo de artistas | cabe inteiro numa frase,"),
    ("abertura", "porque eu preciso respirar arte."),
    ("origem", "Antes do nome, | era só um hábito,"),
    ("origem", "gente se reunindo numa casa,"),
    ("origem", "para tocar violão,"),
    ("origem", "para discutir política cultural,"),
    ("origem", "para escrever projetos."),
    ("2014", "Em 2014, desses encontros, | nasceram o Grupo Parafernália de Teatro | e o Cineclube Ano 41."),
    ("2022", "Em 2022, o nome chegou."),
    ("2022", "Veio de dois versos | de um poema de Carlos Reis."),
    ("2022", "E estreou nos créditos de um curta: | Flores."),
    ("2025", "Em 2025, veio o reconhecimento:"),
    ("2025", "Ponto de Cultura, | pelo Ministério da Cultura, | na Política Nacional Cultura Viva."),
    ("pessoas", "Hoje, são 12 artistas."),
    ("pessoas", "Audiovisual, música, teatro, | circo, literatura."),
    ("filmes", "E sete filmes, | todos feitos aqui."),
    ("f-flores", "Flores,"),
    ("f-lidia", "Dona Lídia,"),
    ("f-fita", "Fita,"),
    ("f-camadas", "Camadas,"),
    ("f-toto", "Deus, eu e o cachorro Totó,"),
    ("f-olhares", "o documentário Olhares"),
    ("f-folia", "e Devoção e Folia de Reis."),
    ("temas", "Histórias de luto, | de violência contra a mulher, | de fé, de música."),
    ("temas", "Temas pouco explorados | no cinema feito em Rondônia."),
    ("mostras", "Devoção e Folia de Reis foi além."),
    ("mostras", "Passou pela Mostra Internacional | de Cinema Negro"),
    ("mostras", "e pela Mostra Sesc | Amazônia das Artes, | em dez estados brasileiros."),
    ("escola", "Mas o Respirartes | não cabe só na tela."),
    ("escola", "Já colocou som, livros | e equipamentos de cinema no carro"),
    ("escola", "e levou tudo até | a Escola Jorge Teixeira, | no distrito de Nova Londrina."),
    ("acoes", "E segue levando música, | circo, teatro e literatura"),
    ("acoes", "para escolas, aldeias, | feiras e fóruns de cultura."),
    ("futuro", "E vem mais por aí:"),
    ("futuro", "a volta do Cineclube, | agora como Cineclube Respirartes, | em parceria com a UNIR."),
    ("futuro", "A Mostra Curta Rio Ji-Paraná, | com filmes da cidade."),
    ("futuro", "E a mostra fotográfica | Do Oriente a Belém, | com a Companhia de Santos Reis."),
    ("fecho", "Coletivo Respirartes,"),
    ("fecho", "Ponto de Cultura de Ji-Paraná,"),
    ("fecho", "porque eu preciso respirar arte."),
]

def letras(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s)

# --- alinhamento letra a letra entre o texto canônico e o que o Whisper ouviu ---
ouv_chars, ouv_idx = [], []
for k, w in enumerate(W):
    for c in letras(w["w"]):
        ouv_chars.append(c); ouv_idx.append(k)
ouv = "".join(ouv_chars)

can_words = []   # (frase_idx, palavra_texto)
QUEBRAS = set()  # índice da palavra que começa um novo bloco
for fi, (cena, txt) in enumerate(FRASES):
    for p in txt.split():
        if p == "|":
            QUEBRAS.add(len(can_words)); continue
        can_words.append((fi, p))
can_chars, can_idx = [], []
for k, (fi, p) in enumerate(can_words):
    for c in letras(p):
        can_chars.append(c); can_idx.append(k)
can = "".join(can_chars)

sm = difflib.SequenceMatcher(None, can, ouv, autojunk=False)
mapa = {}
for a, b, n in sm.get_matching_blocks():
    for j in range(n):
        mapa[a + j] = b + j

tempos = [[None, None] for _ in can_words]
for ci, k in enumerate(can_idx):
    if ci in mapa:
        wk = ouv_idx[mapa[ci]]
        ini, fim = W[wk]["i"], W[wk]["f"]
        if tempos[k][0] is None: tempos[k][0] = ini
        tempos[k][1] = fim
# preenche palavras sem correspondência por interpolação
for k in range(len(tempos)):
    if tempos[k][0] is None:
        ant = next((tempos[j][1] for j in range(k - 1, -1, -1) if tempos[j][1] is not None), 0)
        pro = next((tempos[j][0] for j in range(k + 1, len(tempos)) if tempos[j][0] is not None), ant + .3)
        tempos[k] = [ant, max(ant + .05, pro)]
# corrige sobreposições: a palavra começa depois do início da anterior
for k in range(1, len(tempos)):
    if tempos[k][0] < tempos[k - 1][0]: tempos[k][0] = tempos[k - 1][0] + 0.02
    if tempos[k][1] < tempos[k][0]: tempos[k][1] = tempos[k][0] + 0.1

palavras = []
for k, (fi, p) in enumerate(can_words):
    palavras.append({"w": p, "i": round(tempos[k][0] + OFF, 3), "f": round(tempos[k][1] + OFF, 3), "frase": fi, "cena": FRASES[fi][0], "quebra": k in QUEBRAS})

def pal_da_cena(cena):
    return [p for p in palavras if p["cena"] == cena]

def w(cena, texto, n=0, campo="i"):
    """tempo (vídeo) da n-ésima palavra da cena que começa com 'texto'"""
    alvo = letras(texto)
    achadas = [p for p in pal_da_cena(cena) if letras(p["w"]).startswith(alvo)]
    if len(achadas) <= n:
        raise SystemExit(f"palavra não achada: {cena} {texto} {n}")
    return achadas[n][campo]

def inicio(cena):
    return pal_da_cena(cena)[0]["i"]

# --- cenas: a troca acontece um pouco antes da primeira palavra ---
ordem = ["abertura", "origem", "2014", "2022", "2025", "pessoas", "filmes",
         "f-flores", "f-lidia", "f-fita", "f-camadas", "f-toto", "f-olhares", "f-folia",
         "temas", "mostras", "escola", "acoes", "futuro", "fecho"]
antes = {"origem": .32, "2014": .38, "2022": .3, "2025": .38, "pessoas": .32, "filmes": .28,
         "f-flores": .06, "f-lidia": .06, "f-fita": .06, "f-camadas": .06, "f-toto": .06, "f-olhares": .06, "f-folia": .06,
         "temas": .32, "mostras": .32, "escola": .2, "acoes": .3, "futuro": .32, "fecho": .36}
ini = {"abertura": 0.0}
for c in ordem[1:]:
    ini[c] = round(inicio(c) - antes[c], 3)
cenas = []
for k, c in enumerate(ordem):
    fim = ini[ordem[k + 1]] if k + 1 < len(ordem) else FIM
    cenas.append({"id": c, "ini": ini[c], "fim": round(fim, 3)})

trans = {"origem": "iris", "2014": "cortina", "2022": "flash", "2025": "wipe", "pessoas": "zoom", "filmes": "iris",
         "f-flores": "flash", "f-lidia": "whip", "f-fita": "whip", "f-camadas": "whip", "f-toto": "whip", "f-olhares": "whip", "f-folia": "whip",
         "temas": "cortina", "mostras": "zoom", "escola": "iris", "acoes": "wipe", "futuro": "wipe", "fecho": "flash"}
for c in cenas:
    c["trans"] = trans.get(c["id"])

# --- marcos visuais (tempo de vídeo) ---
M = {}
M["abertura"] = {
    "local": OFF + 0.0, "letras": w("abertura", "artistas") - 0.25, "lema": w("abertura", "porque"),
    "lema_fim": w("abertura", "arte", campo="f"),
}
M["origem"] = {
    "habito": w("origem", "habito"), "casa_txt": w("origem", "gente"), "casa": w("origem", "casa"),
    "chip1": w("origem", "para", 0), "chip2": w("origem", "para", 1), "chip3": w("origem", "para", 2),
}
M["2014"] = {"ano": w("2014", "2014", campo="f"), "grupo": w("2014", "grupo"), "cine": w("2014", "cineclube"),
             "nota": w("2014", "41", campo="f")}
M["2022"] = {"ano": w("2022", "2022", campo="f"), "verso": w("2022", "veio"), "verso_fim": w("2022", "reis", campo="f"),
             "flores": w("2022", "flores")}
M["2025"] = {"ano": w("2025", "2025", campo="f"), "rotulo": w("2025", "reconhecimento"), "ponto": w("2025", "ponto"),
             "check": w("2025", "ministerio"), "linha": w("2025", "politica")}
M["pessoas"] = {"num": w("pessoas", "12", campo="f"), "artistas": w("pessoas", "artistas"),
                "b1": w("pessoas", "audiovisual"), "b2": w("pessoas", "musica"), "b3": w("pessoas", "teatro"),
                "b4": w("pessoas", "circo"), "b5": w("pessoas", "literatura")}
M["filmes"] = {"num": w("filmes", "sete", campo="f"), "sub": w("filmes", "todos")}
M["temas"] = {"p1": w("temas", "luto"), "p2": w("temas", "violencia"), "p3": w("temas", "fe"), "p4": w("temas", "musica"),
              "frase": w("temas", "temas")}
M["mostras"] = {"titulo": w("mostras", "devocao"), "m1": w("mostras", "internacional"), "m2": w("mostras", "sesc"),
                "estados": w("mostras", "dez")}
M["escola"] = {"cinema": w("escola", "cinema"), "carro_ini": w("escola", "levou"), "carro_fim": w("escola", "teixeira", campo="f"),
               "local": w("escola", "jorge")}
M["acoes"] = {"rotulo": w("acoes", "segue"), "c1": w("acoes", "musica"), "c2": w("acoes", "circo"), "c3": w("acoes", "teatro"),
              "c4": w("acoes", "literatura"), "f1": w("acoes", "escolas"), "f2": w("acoes", "aldeias"),
              "f3": w("acoes", "feiras"), "f4": w("acoes", "foruns")}
M["futuro"] = {"ano": w("futuro", "ai", campo="f"), "r1": w("futuro", "volta"), "r1b": w("futuro", "unir"),
               "r2": w("futuro", "mostra", 0), "r3": w("futuro", "fotografica")}
M["fecho"] = {"letras": w("fecho", "coletivo") - 0.2, "ponto": w("fecho", "ponto"), "lema": w("fecho", "porque"),
              "lema_fim": w("fecho", "arte", campo="f")}
for c in cenas:
    if c["id"].startswith("f-"):
        M[c["id"]] = {"titulo": c["ini"] + 0.06}

# --- blocos de legenda (até 7 palavras, quebrando de preferência em vírgulas) ---
blocos = []
for fi, (cena, txt) in enumerate(FRASES):
    if cena.startswith("f-"):
        continue
    ps = [p for p in palavras if p["frase"] == fi]
    atual = []
    manual = any(p["quebra"] for p in ps)
    for k, p in enumerate(ps):
        if atual and (p["quebra"] or (not manual and len(atual) >= 7)):
            blocos.append(atual); atual = []
        atual.append(p)
    if atual:
        blocos.append(atual)
leg = []
for k, b in enumerate(blocos):
    i0 = b[0]["i"] - 0.12
    f0 = b[-1]["f"] + 0.55
    if k + 1 < len(blocos):
        f0 = min(f0, blocos[k + 1][0]["i"] - 0.12)
    f0 = max(f0, b[-1]["f"] + 0.05)
    if leg and leg[-1]["fim"] > i0: leg[-1]["fim"] = round(i0, 3)
    leg.append({"ini": round(i0, 3), "fim": round(f0, 3),
                "palavras": [{"w": p["w"], "i": p["i"], "f": p["f"]} for p in b]})

linha = {"duracao": FIM, "off": OFF, "cenas": cenas, "marcos": M, "palavras": palavras, "legendas": leg}
json.dump(linha, open("linha.json", "w"), ensure_ascii=False, indent=1)

for c in cenas:
    print(f'{c["id"]:<10} {c["ini"]:7.2f} → {c["fim"]:7.2f}  ({c["fim"]-c["ini"]:5.2f}s)  {c["trans"] or ""}')
print("legendas:", len(leg))
for b in leg: print(f'  {b["ini"]:7.2f}-{b["fim"]:7.2f} ' + " ".join(p["w"] for p in b["palavras"]))
