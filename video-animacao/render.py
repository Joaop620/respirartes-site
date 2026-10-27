"""Renderiza o vídeo mudo quadro a quadro. uso: python3 render.py saida.mp4 [f0 f1]"""
import asyncio, json, os, sys, subprocess, time
from playwright.async_api import async_playwright

AQUI = os.path.dirname(os.path.abspath(__file__))
FPS = 30

async def main():
    saida = sys.argv[1]
    linha = open(os.path.join(AQUI, "linha.json"), encoding="utf-8").read()
    dur = json.loads(linha)["duracao"]
    f0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    f1 = int(sys.argv[3]) if len(sys.argv) > 3 else int(round(dur * FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-tune", "film", "-pix_fmt", "yuv420p", "-r", str(FPS), saida],
                          stdin=subprocess.PIPE)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1920, "height": 1080})
        erros = []
        pg.on("pageerror", lambda e: erros.append(str(e)))
        await pg.add_init_script("window.LINHA = " + linha + ";")
        await pg.goto("http://localhost:8766/palco.html", wait_until="networkidle")
        print("fontes", await pg.evaluate("window.pronto()"), flush=True)
        t0 = time.time()
        for i in range(f0, f1):
            await pg.evaluate(f"window.render({i / FPS})")
            jpg = await pg.screenshot(type="jpeg", quality=95)
            ff.stdin.write(jpg)
            if i % 150 == 0:
                print(f"quadro {i}/{f1}  {time.time() - t0:.0f}s  erros={len(erros)}", flush=True)
        await b.close()
    ff.stdin.close(); ff.wait()
    print("FIM", f1 - f0, "quadros", f"{time.time() - t0:.0f}s", "erros:", erros[:3], flush=True)

asyncio.run(main())
