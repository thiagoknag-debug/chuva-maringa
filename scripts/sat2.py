"""Sonda 2: tabela de cores do GIBS (via GetCapabilities) e detalhes do RealEarth G19-ABI-FD-BAND13."""
import sys, subprocess, json, re, io, datetime as dt, requests
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pillow"], check=False)
from PIL import Image
UA = {"User-Agent": "Mozilla/5.0 (chuva-maringa-auditoria)"}; R = {}; agora = dt.datetime.now(dt.timezone.utc); LAY = "GOES-East_ABI_Band13_Clean_Infrared"
def salva(): json.dump(R, open("lab/sat2.json", "w"), ensure_ascii=False, indent=1, default=str)
def passo(nome, f):
    try: R[nome] = f()
    except Exception as e: R[nome] = {"erro": f"{type(e).__name__}: {str(e)[:300]}"}
    print(nome, json.dumps(R[nome], ensure_ascii=False, default=str)[:2500], flush=True); salva()
def caps():
    t = requests.get("https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml", headers=UA, timeout=180).text
    i = t.find(f"<ows:Identifier>{LAY}</ows:Identifier>"); a = t.rfind("<Layer>", 0, i); b = t.find("</Layer>", i); bloco = t[a:b]
    out = {"tamanho_caps": len(t), "bloco": re.sub(r"\s+", " ", bloco)[:2500]}
    cm = re.findall(r'xlink:href="([^"]*colormap[^"]*)"', bloco, re.I); out["colormaps"] = cm
    for u in cm[:2]:
        x = requests.get(u, headers=UA, timeout=60).text; ents = re.findall(r'<ColorMapEntry([^>]*)/?>', x)
        out[u] = {"n": len(ents), "primeiros": ents[:3], "ultimos": ents[-3:], "trecho": x[:400]}
    return out
passo("gibs_caps", caps)
P = "G19-ABI-FD-BAND13"
def re_info():
    out = {}
    for u in (f"https://realearth.ssec.wisc.edu/api/products?products={P}", f"https://realearth.ssec.wisc.edu/api/legend?products={P}"):
        r = requests.get(u, headers=UA, timeout=60); out[u.split("api/")[1][:30]] = {"status": r.status_code, "tipo": r.headers.get("content-type"), "cors": r.headers.get("Access-Control-Allow-Origin"),
                                                                                    "inicio": r.text[:1500] if "json" in (r.headers.get("content-type") or "") or "text" in (r.headers.get("content-type") or "") else len(r.content)}
        if "image" in (r.headers.get("content-type") or ""):
            im = Image.open(io.BytesIO(r.content)).convert("RGB"); out["legenda_tamanho"] = im.size; open("lab/sat_legenda.png", "wb").write(r.content)
    t = requests.get(f"https://realearth.ssec.wisc.edu/api/times?products={P}", headers=UA, timeout=60).json()[P][-3:]
    out["tempos"] = t
    u = f"https://realearth.ssec.wisc.edu/api/image?products={P}_{t[-1].replace('.', '_')}&bounds=-25.0,-53.5,-21.8,-50.4&width=320&height=320"
    r = requests.get(u, headers=UA, timeout=60); out["imagem"] = {"url": u, "status": r.status_code, "tipo": r.headers.get("content-type"), "cors": r.headers.get("Access-Control-Allow-Origin"), "bytes": len(r.content)}
    if r.status_code == 200:
        im = Image.open(io.BytesIO(r.content)); out["imagem"]["modo"] = im.mode; c = im.convert("RGBA").getcolors(100000)
        out["imagem"]["cores"] = len(c) if c else ">100k"; out["imagem"]["mais_comuns"] = sorted(c, reverse=True)[:12] if c else None
        open("lab/sat_re.png", "wb").write(r.content)
    for u in (f"https://realearth.ssec.wisc.edu/api/value?products={P}&lat=-23.42&lon=-51.94", f"https://realearth.ssec.wisc.edu/api/probe?products={P}&lat=-23.42&lon=-51.94"):
        r = requests.get(u, headers=UA, timeout=30); out[u.split("api/")[1][:10]] = {"status": r.status_code, "inicio": r.text[:300]}
    return out
passo("realearth", re_info)
