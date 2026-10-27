import sys, json
from faster_whisper import WhisperModel
m=WhisperModel(sys.argv[3] if len(sys.argv)>3 else "small", device="cpu", compute_type="int8")
import subprocess, numpy as np
raw=subprocess.run(["ffmpeg","-v","error","-i",sys.argv[1],"-ac","1","-ar","16000","-f","f32le","-"],capture_output=True).stdout
audio=np.frombuffer(raw,dtype=np.float32)
segs,_=m.transcribe(audio, language="pt", beam_size=5, word_timestamps=True, vad_filter=False)
out=[]
for s in segs:
    out.append({"ini":s.start,"fim":s.end,"texto":s.text.strip(),"palavras":[{"w":w.word.strip(),"i":round(w.start,3),"f":round(w.end,3),"p":round(w.probability,3)} for w in s.words]})
    print(f"{s.start:7.2f}-{s.end:7.2f} {s.text.strip()}", flush=True)
json.dump(out,open(sys.argv[2],"w"),ensure_ascii=False,indent=1)
