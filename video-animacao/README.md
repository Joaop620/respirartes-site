# Vídeo de apresentação · código da animação

O vídeo de 2 minutos do site é gerado por código: uma página HTML animada quadro a quadro, sincronizada palavra por palavra com a narração de Carlos Reis.

## Como funciona

1. `transcrever.py` reconhece a narração com o faster-whisper e gera os tempos de cada palavra (`carlos_small.json`).
2. `linha.py` alinha esses tempos ao texto do roteiro e monta `linha.json`, com as cenas, as transições, os momentos de cada animação e as legendas.
3. `palco/palco.html` desenha o vídeo. A função `window.render(t)` posiciona tudo para o instante `t`, sem animações automáticas do navegador, então cada quadro sai sempre igual.
4. `render.py` abre o palco no Chromium (Playwright), captura os 3.600 quadros (30 fps) e envia ao ffmpeg.
5. `som.py` compõe a trilha (violão, baixo, bateria e pad em Ré maior) e os efeitos sonoros a partir da mesma linha do tempo.
6. `mix.sh` mistura voz, trilha e efeitos, com a música abaixando sob a voz, e normaliza em -14 LUFS.
7. `codificar.sh` gera as versões 1080p, web e 720p.

`quadros.py` renderiza quadros avulsos para conferência.

## Requisitos

- Python 3.11+ com `numpy`, `scipy`, `playwright` e `faster-whisper`
- ffmpeg
- Chromium para o Playwright

## Gerar o vídeo

O arquivo de voz (`carlos.wav`) não está no repositório. Coloque-o nesta pasta e rode:

```bash
python3 transcrever.py carlos.wav carlos_small.json small
python3 linha.py
python3 som.py
./mix.sh
python3 -m http.server 8766 --directory palco &
python3 render.py mudo.mp4
./codificar.sh
```
