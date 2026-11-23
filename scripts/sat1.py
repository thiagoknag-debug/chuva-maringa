"""Sonda fontes de satélite infravermelho (GOES-19 = GOES-East) para detectar nuvem crescendo: atraso, formato, cores."""
import sys, subprocess, json, time, re, io, datetime as dt, requests
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pillow"], check=False)
from PIL import Image
UA = {"User-Agent": "Mozilla/5.0 (chuva-maringa-auditoria)"}; R = {}; agora = dt.datetime.now(dt.timezone.utc)
def salva(): json.dump(R, open("lab/sat1.json", "w"), ensure_ascii=False, indent=1, default=str)
def passo(nome, f):
    try: R[nome] = f()
    except Exception as e: R[nome] = {"erro": f"{type(e).__name__}: {str(e)[:300]}"}
    print(nome, json.dumps(R[nome], ensure_ascii=False, default=str)[:1500], flush=True); salva()
LAY = "GOES-East_ABI_Band13_Clean_Infrared"
def gibs_tempos():
    ini = (agora - dt.timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ"); fim = agora.strftime("%Y-%m-%dT%H:%M:%SZ")
    u = f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/wmts.cgi?SERVICE=WMTS&REQUEST=DescribeDomains&VERSION=1.0.0&LAYER={LAY}&TILEMATRIXSET=GoogleMapsCompatible_Level6&TIME={ini}--{fim}"
    r = requests.get(u, headers=UA, timeout=60); t = r.text
    dom = re.findall(r"<Domain>([^<]*)</Domain>", t) or re.findall(r"(\d{4}-\d\d-\d\dT[^<,\s]*)", t)
    return {"status": r.status_code, "dominio": dom[-3:] if dom else t[:400], "agora": agora.isoformat()}
passo("gibs_tempos", gibs_tempos)
def gibs_cores():
    r = requests.get(f"https://gibs.earthdata.nasa.gov/colormaps/v1.3/{LAY}.xml", headers=UA, timeout=60); t = r.text
    ents = re.findall(r'<ColorMapEntry rgb="([\d,]+)"[^>]*?value="([^"]*)"', t)
    return {"status": r.status_code, "n": len(ents), "primeiros": ents[:4], "ultimos": ents[-4:], "unidades": re.findall(r'units="([^"]*)"', t)[:2], "trecho": t[:300]}
passo("gibs_cores", gibs_cores)
def gibs_tile(tempo):
    # z6 / tile que contém Maringá (-23.42, -51.94)
    import math
    z = 6; n = 2 ** z; lat, lon = -23.42, -51.94
    x = int((lon + 180) / 360 * n); y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    u = f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{LAY}/default/{tempo}/GoogleMapsCompatible_Level6/{z}/{y}/{x}.png"
    r = requests.get(u, headers=UA, timeout=60)
    out = {"url": u, "status": r.status_code, "bytes": len(r.content), "cors": r.headers.get("Access-Control-Allow-Origin")}
    if r.status_code == 200:
        im = Image.open(io.BytesIO(r.content)); out["modo"] = im.mode; out["tamanho"] = im.size
        rgb = im.convert("RGB"); cores = rgb.getcolors(65536); out["cores_distintas"] = len(cores) if cores else ">65536"
    return out
passo("gibs_tile_default", lambda: gibs_tile("default"))
passo("gibs_tile_19nov_1600Z", lambda: gibs_tile("2026-11-19T16:00:00Z"))
def realearth():
    out = {}
    r = requests.get("https://realearth.ssec.wisc.edu/api/products?search=goes", headers=UA, timeout=60)
    js = r.json() if r.status_code == 200 else []
    ids = [p.get("id") for p in js if isinstance(p, dict)]
    out["n"] = len(ids); out["ir"] = [i for i in ids if re.search(r"(G19|GOES|G16).*?(IR|BAND1[34]|14|13)", str(i), re.I)][:30]
    for pid in out["ir"][:8]:
        try:
            t = requests.get(f"https://realearth.ssec.wisc.edu/api/times?products={pid}", headers=UA, timeout=30).json()
            ult = t.get(pid, [])[-1] if isinstance(t, dict) and t.get(pid) else None; out[pid] = {"ultimo": ult}
            if ult:
                tt = dt.datetime.strptime(ult, "%Y%m%d.%H%M%S").replace(tzinfo=dt.timezone.utc); out[pid]["atraso_min"] = round((agora - tt).total_seconds() / 60)
        except Exception as e: out[pid] = str(e)[:100]
    return out
passo("realearth", realearth)
def aws():
    j = agora.timetuple().tm_yday; out = {}
    for h in (agora.hour, (agora - dt.timedelta(hours=1)).hour):
        u = f"https://noaa-goes19.s3.amazonaws.com/?list-type=2&prefix=ABI-L2-CMIPF/{agora.year}/{j:03d}/{h:02d}/OR_ABI-L2-CMIPF-M6C13"
        t = requests.get(u, headers=UA, timeout=60).text; ks = re.findall(r"<Key>([^<]+)</Key>", t); sz = re.findall(r"<Size>(\d+)</Size>", t)
        out[f"{h:02d}h"] = {"arquivos": len(ks), "ultimo": ks[-1][-60:] if ks else None, "MB": round(int(sz[-1]) / 1e6, 1) if sz else None}
    return out
passo("aws_goes19", aws)
