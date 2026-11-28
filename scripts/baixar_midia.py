"""Download the source footage (YouTube) and photos (Wikimedia Commons) for the video.
Run on a home connection (cloud IPs are blocked by YouTube and Wikimedia):
    pip install -U yt-dlp
    python3 scripts/baixar_midia.py            # everything
    python3 scripts/baixar_midia.py --so-videos
Requires ffmpeg on PATH. Videos go to footage/raw/<id>.mp4 (max 1080p), photos to images/."""
import importlib.util, os, subprocess, sys, json, time, re, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
spec = importlib.util.spec_from_file_location("edl", "scripts/edl.py"); edl = importlib.util.module_from_spec(spec); spec.loader.exec_module(edl)

ids = []
for part in edl.S.values():
    for (_, kind, _, src, _, _) in part:
        if kind == "yt":
            ids += [i for i in src.split() if i not in ids]
EXTRA_SEARCHES = [  # shots with no candidate yet: grab the top fan videos
    "ytsearch3:torcida Flamengo Doha Intercontinental 2025 arquibancada",
    "ytsearch3:torcida Palmeiras Catar Mundial 2021 Education City",
]
if "--so-fotos" not in sys.argv:
    os.makedirs("footage/raw", exist_ok=True)
    base = ["yt-dlp", "-f", "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080]", "--merge-output-format", "mp4",
            "-o", "footage/raw/%(id)s.%(ext)s", "--no-overwrites", "--write-info-json", "--sleep-requests", "1"]
    for i, vid in enumerate(ids):
        print(f"[{i+1}/{len(ids)}] {vid}", flush=True)
        subprocess.run(base + [f"https://www.youtube.com/watch?v={vid}"])
    for q in EXTRA_SEARCHES:
        subprocess.run(base + ["--max-downloads", "3", "--match-filter", "duration < 900", q])

if "--so-videos" not in sys.argv:
    UA = {"User-Agent": "PFRF-video-research/1.0 (educational video editing)"}
    def get(url): return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
    Q = [("Lusail Stadium", "lusail", 5), ("Al Bayt Stadium", "albayt", 4), ("Ahmad bin Ali Stadium", "ahmadbinali", 3),
         ("Khalifa International Stadium", "khalifa", 4), ("Al Thumama Stadium", "althumama", 4), ("Stadium 974", "s974", 5),
         ("Education City Stadium night", "educationcity_n", 3), ("Lusail Boulevard", "lusailcity", 3), ("Hamad International Airport", "airport", 2)]
    os.makedirs("images", exist_ok=True)
    for q, pre, n in Q:
        api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search",
              "gsrsearch": f"filetype:bitmap {q}", "gsrnamespace": 6, "gsrlimit": n * 3, "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 1920})
        pages = sorted(json.loads(get(api)).get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
        got = 0
        for p in pages:
            ii = p["imageinfo"][0]; em = ii.get("extmetadata", {}); lic = em.get("LicenseShortName", {}).get("value", "")
            if ii["width"] < 1200 or ii["width"] < ii["height"] or not re.search(r"CC|Public domain|PD", lic, re.I): continue
            url = ii.get("thumburl") or ii["url"]; ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower() or ".jpg"
            fn = f"{pre}_{got+1:02d}{ext}"
            open(f"images/{fn}", "wb").write(get(url))
            with open("images/credits.jsonl", "a") as f:
                f.write(json.dumps({"file": fn, "title": p["title"], "license": lic, "artist": re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", "")).strip(), "source": ii.get("descriptionurl")}, ensure_ascii=False) + "\n")
            print(fn, p["title"], lic); got += 1; time.sleep(2)
            if got >= n: break
print("pronto")
