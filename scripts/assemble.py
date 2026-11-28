"""Assemble the full video from audio parts + EDL + cards + photos + clips.
usage: python3 scripts/assemble.py [--preview]   (preview = 960x540 fast encode)
Missing YouTube clips become labelled placeholders so the timing can be reviewed."""
import json, os, subprocess, sys, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
spec = importlib.util.spec_from_file_location("edl", "scripts/edl.py"); edl = importlib.util.module_from_spec(spec); spec.loader.exec_module(edl)
PREVIEW = "--preview" in sys.argv
Wd, Hd = (960, 540) if PREVIEW else (1920, 1080)
FPS = 30
FONT = "mg/fonts/BebasNeue-Regular.ttf"
PARTS = "ABCDEFG"
B = "build/asm"; os.makedirs(f"{B}/shots", exist_ok=True)
def sh(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode: raise SystemExit(" ".join(a)[:300] + "\n" + r.stderr[-1500:])
    return r.stdout
def dur_of(f): return float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f))

# ---------- 1. narration: trim silences between parts ----------
trim, off, acc = {}, {}, 0.0
for p in PARTS:
    segs = json.load(open(f"transcripts/parte_{p}.json"))
    words = [w for s in segs for w in s["words"]]
    a = max(0.0, words[0]["s"] - 0.30); e = min(dur_of(f"audio/parte_{p}.wav"), words[-1]["e"] + 0.55)
    trim[p] = (a, e); off[p] = acc; acc += e - a
TOTAL = acc
def G(p, t):
    a, e = trim[p]; return off[p] + min(max(t, a), e) - a
nar = f"{B}/narration.wav"
if not os.path.exists(nar):
    ins, fl = [], []
    for i, p in enumerate(PARTS):
        a, e = trim[p]; ins += ["-i", f"audio/parte_{p}.wav"]
        fl.append(f"[{i}:a]atrim={a:.3f}:{e:.3f},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[a{i}]")
    fl.append("".join(f"[a{i}]" for i in range(len(PARTS))) + f"concat=n={len(PARTS)}:v=0:a=1[out]")
    sh("ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fl), "-map", "[out]", nar)
print(f"narration {TOTAL:.2f}s", {p: round(off[p], 2) for p in PARTS})

# ---------- 2. shot list in global time ----------
cards = {c["id"]: c for c in json.load(open("mg/cards_list.json"))}
shots = []
for p in PARTS:
    for (t, kind, ref, src, desc, opt) in edl.S[p]:
        if kind == "mg": t = cards[ref]["start"]
        shots.append(dict(part=p, t=G(p, t), kind=kind, ref=ref, src=src, desc=desc, opt=opt))
shots.sort(key=lambda s: s["t"]); shots[0]["t"] = 0.0
for i, s in enumerate(shots):
    s["end"] = shots[i + 1]["t"] if i + 1 < len(shots) else TOTAL
    s["dur"] = round(s["end"] - s["t"], 3)
shots = [s for s in shots if s["dur"] > 0.05]

# ---------- 3. render shots ----------
scale = f"scale={Wd}:{Hd}:force_original_aspect_ratio=increase,crop={Wd}:{Hd},setsar=1,fps={FPS}"
enc = ["-c:v", "libx264", "-preset", "veryfast" if PREVIEW else "medium", "-crf", "28" if PREVIEW else "18", "-pix_fmt", "yuv420p", "-an"]
def esc(s): return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace("%", "\\%")
fs = Hd / 1080
stats = {"yt": 0.0, "yt_missing": 0.0, "img": 0.0, "mg": 0.0}
for i, s in enumerate(shots):
    out = f"{B}/shots/{i:03d}.mp4"; d = s["dur"]
    if s["kind"] == "mg":
        stats["mg"] += d
        sh("ffmpeg", "-y", "-v", "error", "-i", f"build/cards/{s['ref']}.mp4", "-vf", f"{scale},tpad=stop_mode=clone:stop_duration=5", "-t", f"{d:.3f}", *enc, out)
    elif s["kind"] == "img":
        stats["img"] += d
        n = int(round(d * FPS)) + 1; zin = i % 2 == 0
        z = f"'1+0.10*on/{n}'" if zin else f"'1.10-0.10*on/{n}'"
        sh("ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", f"images/{s['ref']}",
           "-vf", f"scale={Wd*2}:{Hd*2}:force_original_aspect_ratio=increase,crop={Wd*2}:{Hd*2},zoompan=z={z}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={Wd}x{Hd}:fps={FPS},setsar=1",
           "-frames:v", str(int(round(d * FPS))), *enc, out)
    else:
        clip = f"footage/clips/{s['ref']}.mp4"
        o = s["opt"]; vf = [scale]
        if os.path.exists(clip):
            stats["yt"] += d
            if o.get("slow"): vf.insert(0, f"setpts=PTS/{o['slow']}")
            if o.get("fifa"):
                vf.append(f"drawbox=x=0:y=ih-{int(70*fs)}:w=iw:h={int(70*fs)}:color=0x0a0908@0.75:t=fill,"
                          f"drawtext=fontfile={FONT}:text='IMAGENS\\: FIFA':x={int(40*fs)}:y=h-{int(54*fs)}:fontsize={int(40*fs)}:fontcolor=0xf6f2ea")
            if o.get("label"):
                vf.append(f"drawbox=x=w*0.62:y=h*0.08:w=w*0.32:h=h*0.13:color=0xf6f2ea@0.95:t=fill,"
                          f"drawtext=fontfile={FONT}:text='{esc(o['label'])}':x=w*0.78-tw/2:y=h*0.145-th/2:fontsize={int(90*fs)}:fontcolor=0x0a0908")
            sh("ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", clip, "-vf", ",".join(vf), "-t", f"{d:.3f}", *enc, out)
        else:
            stats["yt_missing"] += d
            t1 = esc(f"CLIPE {s['ref']}"); t2 = esc(s["desc"].upper()); t3 = esc("fonte: " + (s["src"] or "busca nova"))
            vf = (f"scale={Wd}:{Hd},drawtext=fontfile={FONT}:text='{t1}':x=(w-tw)/2:y=h*0.36:fontsize={int(46*fs)}:fontcolor=0xd9cfc2,"
                  f"drawtext=fontfile={FONT}:text='{t2}':x=(w-tw)/2:y=h*0.45:fontsize={int(64*fs)}:fontcolor=0xf6f2ea,"
                  f"drawtext=fontfile={FONT}:text='{t3}':x=(w-tw)/2:y=h*0.56:fontsize={int(36*fs)}:fontcolor=0x8a5a3a")
            sh("ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", "build/placeholder_bg_0.00.png", "-vf", vf, "-t", f"{d:.3f}", *enc, out)
    print(f"{i:03d} {s['part']} {s['t']:7.2f} {d:5.2f} {s['kind']:3s} {s['ref']}", flush=True)

# ---------- 4. concat + overlays + audio ----------
with open(f"{B}/list.txt", "w") as f:
    for i in range(len(shots)): f.write(f"file 'shots/{i:03d}.mp4'\n")
sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{B}/list.txt", "-c", "copy", f"{B}/video_base.mp4")
ov = [c for c in cards.values() if c.get("alpha")]
ins, fl, last = ["-i", f"{B}/video_base.mp4"], [], "0:v"
for k, c in enumerate(ov):
    t0 = G(c["part"], c["start"])
    ins += ["-itsoffset", f"{t0:.3f}", "-i", f"build/cards/{c['id']}.mov"]
    fl.append(f"[{k+1}:v]scale={Wd}:{Hd}[o{k}];[{last}][o{k}]overlay=eof_action=pass:enable='between(t,{t0:.3f},{t0 + c['dur']:.3f})'[v{k}]"); last = f"v{k}"
ins += ["-i", nar]
out = "deliverables/estadios_copa2022_preview.mp4" if PREVIEW else "deliverables/estadios_copa2022.mp4"
sh("ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fl), "-map", f"[{last}]", "-map", f"{len(ov)+1}:a",
   "-c:v", "libx264", "-preset", "veryfast" if PREVIEW else "medium", "-crf", "26" if PREVIEW else "18", "-pix_fmt", "yuv420p",
   "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{TOTAL:.3f}", "-movflags", "+faststart", out)
tot = sum(stats.values())
print("OUT", out, f"{TOTAL:.1f}s")
print({k: f"{v:.1f}s ({100*v/tot:.0f}%)" for k, v in stats.items()})
json.dump(shots, open(f"{B}/shots.json", "w"), ensure_ascii=False, indent=1)
