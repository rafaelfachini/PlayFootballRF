"""Download only the listed YouTube cuts (with padding) on a home connection.
    python3 -m pip install -U yt-dlp      (ffmpeg must be on PATH)
    python3 scripts/baixar_cortes.py
Reads deliverables/lista_cortes_youtube.md, writes footage/cuts/NN_k.mp4 (<=1080p) and footage/cuts/manifest.json."""
import os, re, json, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
PAD = 4
os.makedirs("footage/cuts", exist_ok=True)
def sec(s):
    p = [int(x) for x in s.split(":")]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]
items = []
for line in open("deliverables/lista_cortes_youtube.md", encoding="utf-8"):
    m = re.match(r"(\d+)\. https://youtu\.be/([\w-]+)\S* — (.+?) — (.+)$", line.strip())
    if not m: continue
    n, vid, cuts, desc = m.groups()
    for k, (a, b) in enumerate(re.findall(r"(\d+:\d+)–(\d+:\d+)", cuts), 1):
        items.append(dict(n=int(n), k=k, id=vid, start=max(0, sec(a) - PAD), end=sec(b) + PAD, desc=desc))
manifest, fails = [], []
for it in items:
    out = f"footage/cuts/{it['n']:02d}_{it['k']}.mp4"
    if not os.path.exists(out):
        r = subprocess.run(["yt-dlp", "-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]", "--merge-output-format", "mp4",
                            "--download-sections", f"*{it['start']}-{it['end']}", "--force-keyframes-at-cuts",
                            "-o", out, f"https://www.youtube.com/watch?v={it['id']}"])
        if r.returncode or not os.path.exists(out):
            fails.append(out); print("FALHOU", out, file=sys.stderr); continue
    it["file"] = out; manifest.append(it); print("ok", out, flush=True)
json.dump(manifest, open("footage/cuts/manifest.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(manifest)} cortes baixados, {len(fails)} falhas", fails)
