#!/bin/bash
cd "$(dirname "$0")"
T='Coletivo Respirartes - Porque eu preciso respirar arte'
ffmpeg -y -loglevel error -i mudo.mp4 -i audio.wav -map 0:v -map 1:a -c:v libx264 -preset medium -b:v 5500k -maxrate 8000k -bufsize 11000k -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -metadata title="$T" Respirartes_v3_alta_qualidade.mp4 && echo ALTA_OK
ffmpeg -y -loglevel error -i mudo.mp4 -i audio.wav -map 0:v -map 1:a -c:v libx264 -preset medium -crf 25 -maxrate 3500k -bufsize 7000k -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart -metadata title="$T" respirartes_v3_web.mp4 && echo WEB_OK
ffmpeg -y -loglevel error -i mudo.mp4 -i audio.wav -map 0:v -map 1:a -vf scale=1280:720:flags=lanczos -c:v libx264 -preset medium -b:v 1600k -maxrate 2300k -bufsize 3200k -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart -metadata title="$T" Respirartes_720p.mp4 && echo CHAT_OK
