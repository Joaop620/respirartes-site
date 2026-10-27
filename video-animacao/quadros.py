"""Renderiza quadros avulsos do palco para conferência.
uso: python3 quadros.py saida_prefixo t1 t2 t3 ...   (gera uma prancha com todos)"""
import asyncio, json, sys, os
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:8766/palco.html"

async def main():
    pref = sys.argv[1]; ts = [float(x) for x in sys.argv[2:]]
    linha = open(os.path.join(AQUI, os.environ.get("LT", "linha.json")), encoding="utf-8").read()
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1920, "height": 1080})
        erros = []
        pg.on("pageerror", lambda e: erros.append(str(e)))
        pg.on("console", lambda m: erros.append("console: " + m.text) if m.type == "error" else None)
        await pg.add_init_script("window.LINHA = " + linha + ";")
        await pg.goto(URL, wait_until="networkidle")
        print("fontes", await pg.evaluate("window.pronto()"))
        arqs = []
        for t in ts:
            await pg.evaluate(f"window.render({t})")
            a = f"{pref}_{t:07.2f}.jpg"
            await pg.screenshot(path=a, type="jpeg", quality=88)
            arqs.append((t, a))
        print("erros:", erros[:5])
        await b.close()
    # prancha
    n = len(arqs); cols = 4; rows = (n + cols - 1) // cols
    S = Image.new("RGB", (cols * 480, rows * 290), "white"); d = ImageDraw.Draw(S)
    for k, (t, a) in enumerate(arqs):
        im = Image.open(a).resize((480, 270)); x, y = (k % cols) * 480, (k // cols) * 290
        S.paste(im, (x, y + 20)); d.text((x + 4, y + 4), f"{t:.2f}s", fill="black")
    S.save(pref + "_prancha.jpg", quality=85)

asyncio.run(main())
