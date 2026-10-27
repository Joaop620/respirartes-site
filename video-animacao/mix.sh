#!/bin/bash
set -e
cd "$(dirname "$0")"
DUR=$(python3 -c "import json; print(json.load(open('linha.json'))['duracao'])")
ffmpeg -y -loglevel error -i carlos.wav -i musica.wav -i sfx.wav -filter_complex "
  [0:a]aresample=48000,aformat=channel_layouts=stereo,adelay=1800|1800,apad=pad_dur=8,highpass=f=70,
       equalizer=f=250:t=q:w=1:g=-1,equalizer=f=3200:t=q:w=1.2:g=1.2,
       acompressor=threshold=-18dB:ratio=2:attack=8:release=150:makeup=1,
       loudnorm=I=-16:TP=-2:LRA=9,aresample=48000,asplit=2[voz][chave];
  [voz]aecho=0.9:0.5:32|57:0.05|0.03[vozr];
  [1:a]apad=pad_dur=6,volume=0.36[mus];
  [mus][chave]sidechaincompress=threshold=0.02:ratio=5:attack=40:release=450:makeup=1[musd];
  [2:a]apad=pad_dur=6,volume=0.5[fx];
  [vozr][musd][fx]amix=inputs=3:duration=longest:normalize=0,
       loudnorm=I=-14.5:TP=-1.5:LRA=10,aresample=48000,alimiter=limit=0.9,atrim=0:$DUR,asetpts=N/SR/TB,afade=t=out:st=$(python3 -c "print($DUR-0.6)"):d=0.6[out]" \
  -map "[out]" -ar 48000 -c:a pcm_s16le audio.wav
echo AUDIO_OK
