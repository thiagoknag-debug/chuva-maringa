"""Sonda 5: GLM full disk (densidade e pontos) e LightningCast no RealEarth: horários, imagem e tiles com CORS. Grava lab/sondagem_fontes5.json"""
import json, requests, io
from PIL import Image
H = {"User-Agent": "Mozilla/5.0 (chuva-maringa)", "Origin": "https://thiagoknag-debug.github.io"}
out = {}
p = {x["id"]: x for x in requests.get("https://realearth.ssec.wisc.edu/api/products", headers=H, timeout=90).json()}
for pid in ["glmgroupdensity", "glmgrouppoints", "PLTGGOESEastRadF"]:
    d = {"meta": {k: p.get(pid, {}).get(k) for k in ("name", "description", "type", "displaytype", "units", "probe", "maxzoom", "legend", "colormap", "seedlatbound")}}
    r = requests.get(f"https://realearth.ssec.wisc.edu/api/times?products={pid}", headers=H, timeout=40); t = r.json().get(pid, []); d["n_times"] = len(t); d["ultimos"] = t[-6:]
    if t:
        last = t[-1]; ymd, hms = last.split(".")
        for k, u in {"image": f"https://realearth.ssec.wisc.edu/api/image?products={pid}&bounds=-25.5,-54.5,-21.5,-49.5&width=256&height=205",
                     "image_t": f"https://realearth.ssec.wisc.edu/api/image?products={pid}_{ymd}_{hms}&bounds=-25.5,-54.5,-21.5,-49.5&width=256&height=205",
                     "tile": f"https://realearth.ssec.wisc.edu/tiles/{pid}/{ymd}/{hms}/7/45/72.png",
                     "tile2": f"https://re1.ssec.wisc.edu/tiles/{pid}/{ymd}/{hms}/7/45/72.png",
                     "shapes": f"https://realearth.ssec.wisc.edu/api/shapes?products={pid}&bounds=-25.5,-54.5,-21.5,-49.5"}.items():
            try:
                rr = requests.get(u, headers=H, timeout=40); ct = rr.headers.get("Content-Type") or ""
                e = [rr.status_code, ct, rr.headers.get("Access-Control-Allow-Origin"), len(rr.content)]
                if rr.status_code == 200 and "image" in ct:
                    im = Image.open(io.BytesIO(rr.content)).convert("RGBA"); cols = {}
                    for px in im.getdata():
                        if px[3]: cols[px] = cols.get(px, 0) + 1
                    e.append(sorted(cols.items(), key=lambda a: -a[1])[:10]); im.save(f"lab/re5_{pid}_{k}.png")
                else: e.append(rr.text[:600])
                d[k] = e
            except Exception as ex: d[k] = repr(ex)
    out[pid] = d
json.dump(out, open("lab/sondagem_fontes5.json", "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(out, ensure_ascii=False, default=str)[:7000])
