"""Sonda RainViewer: tabela de cores, CORS dos tiles, esquemas e zooms disponíveis. Grava lab/sondagem_rv.json"""
import io, re, json, requests
from PIL import Image
UA = {"User-Agent": "chuva-maringa", "Origin": "https://thiagoknag-debug.github.io"}
out = {}
h = requests.get("https://www.rainviewer.com/api/color-schemes.html", headers=UA, timeout=30).text
out["links_csv"] = sorted(set(re.findall(r'["\']([^"\']+\.csv)["\']', h)))
out["scripts"] = sorted(set(re.findall(r'src=["\']([^"\']+\.js)["\']', h)))[:20]
for u in out["links_csv"]:
    full = u if u.startswith("http") else "https://www.rainviewer.com" + (u if u.startswith("/") else "/api/" + u)
    try: out.setdefault("csv", {})[full] = requests.get(full, headers=UA, timeout=30).text[:20000]
    except Exception as e: out.setdefault("csv", {})[full] = repr(e)
j = requests.get("https://api.rainviewer.com/public/weather-maps.json", headers=UA, timeout=30)
out["maps_headers"] = {k: v for k, v in j.headers.items() if k.lower().startswith("access-control") or k.lower() in ("cache-control", "age")}
j = j.json(); out["maps_keys"] = list(j.keys()); out["radar_keys"] = list(j["radar"].keys()); out["n_past"] = len(j["radar"]["past"]); out["nowcast"] = len(j["radar"].get("nowcast", []))
out["ultimos"] = j["radar"]["past"][-3:]; out["generated"] = j.get("generated")
f = j["radar"]["past"][-1]
res = {}
for size in (256, 512):
    for z in (6, 7, 8):
        x, y = {6: (22, 36), 7: (45, 72), 8: (91, 145)}[z]
        for sc in (0, 1, 2, 4):
            u = f"{j['host']}{f['path']}/{size}/{z}/{x}/{y}/{sc}/0_0.png"
            r = requests.get(u, headers=UA, timeout=30)
            k = f"{size}/z{z}/c{sc}"
            d = {"status": r.status_code, "acao": r.headers.get("Access-Control-Allow-Origin"), "len": len(r.content), "ctype": r.headers.get("Content-Type")}
            if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image"):
                im = Image.open(io.BytesIO(r.content)).convert("RGBA"); cols = {}
                for px in im.getdata():
                    if px[3] > 0: cols[px] = cols.get(px, 0) + 1
                d["n_cores"] = len(cols); d["top_cores"] = sorted(cols.items(), key=lambda a: -a[1])[:25]
                d["modo"] = im.mode
            res[k] = d
out["tiles"] = res
json.dump(out, open("lab/sondagem_rv.json", "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: out[k] for k in out if k not in ("csv", "tiles")}, default=str)[:3000])
for k, v in res.items(): print(k, {a: v.get(a) for a in ("status", "acao", "len", "n_cores")})
