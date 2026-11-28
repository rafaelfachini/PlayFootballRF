import sys, json, subprocess, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[1], device="cpu", compute_type="int8", cpu_threads=4)
for p in sys.argv[2:]:
    a=np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",f"audio/parte_{p}.wav","-ac","1","-ar","16000","-f","s16le","-"],capture_output=True).stdout,np.int16).astype(np.float32)/32768
    segs, info = m.transcribe(a, language="pt", word_timestamps=True, vad_filter=False)
    out=[]
    for s in segs:
        out.append({"start":s.start,"end":s.end,"text":s.text,"words":[{"w":w.word,"s":w.start,"e":w.end} for w in s.words]})
        print(p, f"{s.start:7.2f}-{s.end:7.2f}", s.text, flush=True)
    json.dump(out, open(f"transcripts/parte_{p}.json","w"), ensure_ascii=False, indent=1)
