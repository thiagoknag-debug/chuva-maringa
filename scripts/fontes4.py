"""Sonda 4: RealEarth (LightningCast / GLM full disk) — horários, valor no ponto e tiles. Grava lab/sondagem_fontes4.json"""
import json, requests, io
from PIL import Image
H = {"User-Agent": "Mozilla/5.0 (chuva-maringa)", "Origin": "https://thiagoknag-debug.github.io"}
out = {}
p = requests.get("https://realearth.ssec.wisc.edu/api/products", headers=H, timeout=90).json()
cand = [x for x in p if any(s in (x.get("id", "") + " " + x.get("name", "")).upper() for s in ("GLM", "LIGHTN", "PLTG", "FLASH"))]
out["todos"] = [[x.get("id"), x.get("name")] for x in cand]
alvo = [x["id"] for x in cand if any(s in x["id"] for s in ("RadF", "FD", "FullDisk", "FULL", "OCONUS"))] + ["PLTGGOESEastRadF"]
out["detalhe"] = {}
for pid in list(dict.fromkeys(alvo))[:12]:
    d = {}
    try:
        r = requests.get(f"https://realearth.ssec.wisc.edu/api/times?products={pid}", headers=H, timeout=40); d["times"] = r.text[:300]; d["acao_times"] = r.headers.get("Access-Control-Allow-Origin")
        t = r.json().get(pid, [])
        if t:
            last = t[-1]; d["ultimo"] = last
            for k, u in {"value": f"https://realearth.ssec.wisc.edu/api/value?products={pid}_{last.replace('.', '_')}&lat=-23.42&lon=-51.94",
                         "value2": f"https://realearth.ssec.wisc.edu/api/value?products={pid}&lat=-23.42&lon=-51.94",
                         "image": f"https://realearth.ssec.wisc.edu/api/image?products={pid}&bounds=-25.5,-54.5,-21.5,-49.5&width=200&height=160"}.items():
                rr = requests.get(u, headers=H, timeout=40); d[k] = [rr.status_code, rr.headers.get("Content-Type"), rr.headers.get("Access-Control-Allow-Origin"), rr.text[:300] if "image" not in (rr.headers.get("Content-Type") or "") else len(rr.content)]
                if k == "image" and rr.status_code == 200 and "image" in (rr.headers.get("Content-Type") or ""):
                    im = Image.open(io.BytesIO(rr.content)).convert("RGBA"); cols = {}
                    for px in im.getdata():
                        if px[3]: cols[px] = cols.get(px, 0) + 1
                    d["cores"] = sorted(cols.items(), key=lambda a: -a[1])[:12]; im.save(f"lab/re_{pid}.png")
        meta = [x for x in cand if x["id"] == pid][0]; d["meta"] = {k: meta.get(k) for k in ("name", "description", "units", "probe", "maxzoom", "seedlatbound", "categories")}
    except Exception as e: d["erro"] = repr(e)
    out["detalhe"][pid] = d
json.dump(out, open("lab/sondagem_fontes4.json", "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(out, ensure_ascii=False, default=str)[:6000])
