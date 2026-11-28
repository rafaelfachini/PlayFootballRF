"""Search Wikimedia Commons and download images + license metadata.
usage: python3 commons.py <outdir> "<query>" <n> [prefix]"""
import sys, json, os, re, urllib.request, urllib.parse
UA = {"User-Agent": "PFRF-video-research/1.0 (educational video editing)"}
import time
def fetch(url):
    for i in range(6):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(20 * (i + 1))
    raise SystemExit("gave up " + url)
def get(url):
    return json.loads(fetch(url))
out, q, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
prefix = sys.argv[4] if len(sys.argv) > 4 else re.sub(r'\W+', '_', q)[:30]
os.makedirs(out, exist_ok=True)
api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
    "action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:bitmap {q}",
    "gsrnamespace": 6, "gsrlimit": n * 3, "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 1280})
pages = sorted(get(api).get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
meta_path = os.path.join(out, "credits.jsonl")
got = 0
for p in pages:
    ii = p["imageinfo"][0]
    if ii["width"] < 1200 or ii["width"] < ii["height"]:
        continue
    em = ii.get("extmetadata", {})
    lic = em.get("LicenseShortName", {}).get("value", "")
    if not re.search(r"CC|Public domain|PD", lic, re.I):
        continue
    url = ii["url"] if ii["width"] <= 4200 else ii.get("thumburl", ii["url"])
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower() or ".jpg"
    fn = f"{prefix}_{got+1:02d}{ext}"
    open(os.path.join(out, fn), "wb").write(fetch(url))
    artist = re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", "")).strip()
    with open(meta_path, "a") as f:
        f.write(json.dumps({"file": fn, "title": p["title"], "license": lic, "artist": artist,
                            "source": ii.get("descriptionurl")}, ensure_ascii=False) + "\n")
    print(fn, "|", p["title"], "|", lic, "|", artist[:40])
    got += 1
    time.sleep(6)
    if got >= n:
        break
