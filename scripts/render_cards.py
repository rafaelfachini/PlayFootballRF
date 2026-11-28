"""Render cards from mg/cards_list.json. usage: render_cards.py [--stills] [ids...]"""
import json, subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor
L = json.load(open("mg/cards_list.json"))
stills = "--stills" in sys.argv
ids = [a for a in sys.argv[1:] if not a.startswith("--")]
os.makedirs("build/cards", exist_ok=True); os.makedirs("build/cardstills", exist_ok=True)
def run(c):
    p = dict(c["p"]); p["dur"] = c["dur"]
    if stills:
        out = f"build/cardstills/{c['id']}.png"; extra = ["--stills", str(round(c["dur"] * .75, 2))]
    else:
        out = f"build/cards/{c['id']}." + ("mov" if c.get("alpha") else "mp4"); extra = ["30"]
    args = ["node", "scripts/render_mg.js", "mg/cards.html", out, *extra, "--hash", json.dumps(p, ensure_ascii=False)]
    if c.get("alpha"): args.append("--alpha")
    r = subprocess.run(args, capture_output=True, text=True)
    return c["id"], [l for l in (r.stdout + r.stderr).splitlines() if "rror" in l][:2]
with ThreadPoolExecutor(3) as ex:
    for i, e in ex.map(run, [c for c in L if not ids or c["id"] in ids]): print(i, e, flush=True)
