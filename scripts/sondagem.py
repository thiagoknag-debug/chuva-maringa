"""Sondagem das fontes de dados (roda no GitHub Actions). Grava lab/sondagem.json."""
import io, json, math, os, time, datetime as dt
import requests

LAT, LON = -23.42, -51.94
OUT = {"gerado": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")}
UA = {"User-Agent": "chuva-maringa-sondagem"}

def get(url, **kw):
    t = time.time()
    try:
        r = requests.get(url, timeout=kw.pop("timeout", 60), headers=UA, **kw)
        return r, round(time.time() - t, 1)
    except Exception as e:
        return e, round(time.time() - t, 1)

def resumo(r):
    if isinstance(r, Exception): return {"erro": str(r)[:200]}
    return {"status": r.status_code, "tipo": r.headers.get("content-type", ""), "bytes": len(r.content),
            "inicio": r.text[:200] if "json" in r.headers.get("content-type", "") or "text" in r.headers.get("content-type", "") else ""}

# 1. conjuntos (ensembles)
ens = {}
for mid in ["ecmwf_ifs025", "ecmwf_aifs025", "ecmwf_aifs025_ensemble", "gfs025", "icon_seamless", "gem_global",
            "gem_global_ensemble", "ukmo_global_ensemble_20km", "bom_access_global_ensemble", "ncep_aigefs025"]:
    r, s = get("https://ensemble-api.open-meteo.com/v1/ensemble", params={"latitude": LAT, "longitude": LON,
               "timezone": "America/Sao_Paulo", "hourly": "precipitation,wind_gusts_10m,cape", "forecast_days": 3, "models": mid})
    d = {"seg": s}
    if isinstance(r, Exception) or r.status_code != 200:
        d.update(resumo(r))
    else:
        h = r.json().get("hourly", {})
        def conta(var):
            ks = [k for k in h if k.startswith(var)]
            nn = [sum(v is not None for v in h[k]) for k in ks]
            return {"membros": len(ks), "horas_com_dado_media": round(sum(nn) / len(nn), 1) if nn else 0,
                    "exemplo_chave": ks[1] if len(ks) > 1 else (ks[0] if ks else None)}
        d.update({"status": 200, "horas": len(h.get("time", [])), "chuva": conta("precipitation"),
                  "rajada": conta("wind_gusts_10m"), "cape": conta("cape")})
    ens[mid] = d
    time.sleep(0.5)
OUT["conjuntos"] = ens

# 2. modelos determinísticos: rajada e CAPE disponíveis?
r, s = get("https://api.open-meteo.com/v1/forecast", params={"latitude": LAT, "longitude": LON, "timezone": "America/Sao_Paulo",
           "hourly": "wind_gusts_10m,cape,lifted_index,convective_inhibition", "forecast_days": 2,
           "models": "ecmwf_ifs,ecmwf_ifs025,ecmwf_aifs025_single,gfs_seamless,icon_seamless,meteofrance_seamless,ukmo_seamless,jma_seamless,gem_seamless,cma_grapes_global,best_match"})
det = {}
if not isinstance(r, Exception) and r.status_code == 200:
    h = r.json()["hourly"]
    for k, v in h.items():
        if k == "time": continue
        det[k] = {"n": sum(x is not None for x in v), "max": max([x for x in v if x is not None], default=None)}
else: det = resumo(r)
OUT["deterministicos"] = det

# 3. o que os modelos previram na véspera para 2/11 (rajada, CAPE, chuva)
r, s = get("https://previous-runs-api.open-meteo.com/v1/forecast", params={"latitude": LAT, "longitude": LON, "timezone": "America/Sao_Paulo",
           "start_date": "2026-11-01", "end_date": "2026-11-02",
           "hourly": "precipitation_previous_day1,wind_gusts_10m_previous_day1,cape_previous_day1",
           "models": "ecmwf_ifs,ecmwf_ifs025,ecmwf_aifs025_single,gfs_seamless,icon_seamless,meteofrance_seamless,ukmo_seamless,jma_seamless,gem_seamless,cma_grapes_global,best_match"})
caso = {}
if not isinstance(r, Exception) and r.status_code == 200:
    h = r.json()["hourly"]; t = h["time"]
    idx = [i for i, x in enumerate(t) if x.startswith("2026-11-02")]
    for k, v in h.items():
        if k == "time": continue
        vals = [v[i] for i in idx if v[i] is not None]
        if not vals: caso[k] = None; continue
        caso[k] = round(sum(vals), 1) if k.startswith("precipitation") else round(max(vals), 1)
else: caso = resumo(r)
OUT["caso_2_11_vespera"] = caso

# 4. radar RainViewer: cobertura e chuva no pixel de Maringá
def tile(lat, lon, z):
    n = 2 ** z; x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return int(x), int(y), int((x % 1) * 256), int((y % 1) * 256)
rv = {}
r, s = get("https://api.rainviewer.com/public/weather-maps.json")
rv["lista"] = resumo(r)
try:
    from PIL import Image
    j = r.json(); host = j["host"]; past = j["radar"]["past"]; rv["quadros"] = len(past)
    x, y, px, py = tile(LAT, LON, 7)
    rc, _ = get(f"{host}/v2/coverage/0/256/7/{x}/{y}/0/0_0.png")
    rv["cobertura_tile"] = resumo(rc)
    if not isinstance(rc, Exception) and rc.status_code == 200:
        im = Image.open(io.BytesIO(rc.content)).convert("RGBA")
        rv["cobertura_pixel_maringa_rgba"] = im.getpixel((px, py))
        rv["cobertura_transparente_maringa"] = im.getpixel((px, py))[3] < 50
        a = [im.getpixel((min(255, max(0, px + dx)), min(255, max(0, py + dy))))[3] for dx in range(-20, 21, 5) for dy in range(-20, 21, 5)]
        rv["fracao_coberta_arredores"] = round(sum(v < 50 for v in a) / len(a), 2)
    rt, _ = get(f"{host}{past[-1]['path']}/256/7/{x}/{y}/2/1_1.png")
    rv["radar_tile"] = resumo(rt)
except Exception as e:
    rv["erro"] = str(e)[:200]
OUT["radar"] = rv

# 5. satélite e mapa
OUT["satelite"] = resumo(get("https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/GOES-East_ABI_Band13_Clean_Infrared/default/default/GoogleMapsCompatible_Level7/4/9/5.png")[0])
OUT["satelite_alt"] = resumo(get("https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/GOES-East_ABI_Band13_Clean_Infrared/default/GoogleMapsCompatible_Level7/4/9/5.png")[0])
OUT["mapa_base"] = resumo(get("https://a.basemaps.cartocdn.com/light_all/4/5/9.png")[0])
OUT["leaflet"] = resumo(get("https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js")[0])

# 6. aeroporto SBMG (METAR, arquivo do Iowa Environmental Mesonet)
r, s = get("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py", params={"station": "SBMG", "data": ["sknt", "gust", "wxcodes", "metar"],
           "year1": 2026, "month1": 11, "day1": 1, "year2": 2026, "month2": 11, "day2": 3, "tz": "Etc/UTC", "format": "onlycomma",
           "latlon": "no", "missing": "empty", "trace": "empty", "direct": "no", "report_type": [3, 4]}, timeout=120)
sb = resumo(r)
if not isinstance(r, Exception) and r.status_code == 200:
    linhas = r.text.strip().splitlines(); sb["linhas"] = len(linhas) - 1; sb["primeiras"] = linhas[:3]
    sb["dia_2_11"] = [l for l in linhas if "2026-11-02 0" in l][:12]
sb["seg"] = s
r2, _ = get("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py", params={"station": "SBMG", "data": "sknt", "year1": 2024, "month1": 9,
            "day1": 1, "year2": 2024, "month2": 9, "day2": 3, "tz": "Etc/UTC", "format": "onlycomma", "report_type": [3, 4]}, timeout=120)
sb["historico_2024"] = (len(r2.text.strip().splitlines()) - 1) if not isinstance(r2, Exception) and r2.status_code == 200 else resumo(r2)
OUT["aeroporto_SBMG"] = sb

# 7. CEMADEN (pluviômetros automáticos)
cem = {}
for u in ["https://resources.cemaden.gov.br/graficos/interativo/getJson2.php?uf=PR",
          "http://sjc.salvar.cemaden.gov.br/resources/graficos/interativo/getJson2.php?uf=PR",
          "https://mapainterativo.cemaden.gov.br/MapainterativoCemaden/",
          "https://sws.cemaden.gov.br/PED/rest/pcds-cadastro/municipio?codibge=4115200"]:
    r, s = get(u, timeout=40); d = resumo(r); d["seg"] = s
    if not isinstance(r, Exception) and r.status_code == 200 and "json" in r.headers.get("content-type", ""):
        try:
            j = r.json(); itens = j if isinstance(j, list) else j.get("datas", j.get("items", []))
            mga = [x for x in itens if "MARING" in json.dumps(x, ensure_ascii=False).upper()]
            d["maringa"] = mga[:5]; d["total"] = len(itens)
        except Exception as e: d["parse"] = str(e)[:100]
    cem[u] = d
OUT["cemaden"] = cem

# 8. INMET
inm = {}
r, s = get("https://apitempo.inmet.gov.br/estacao/2026-11-01/2026-11-03/A835", timeout=60)
d = resumo(r)
if not isinstance(r, Exception) and r.status_code == 200:
    try:
        j = r.json(); d["horas"] = len(j)
        d["dia_2_11"] = [{k: x.get(k) for k in ("DT_MEDICAO", "HR_MEDICAO", "CHUVA", "VEN_RAJ", "VEN_VEL")} for x in j if x.get("DT_MEDICAO") == "2026-11-02"][:12]
    except Exception as e: d["parse"] = str(e)[:100]
inm["apitempo"] = d
r = requests.head("https://portal.inmet.gov.br/uploads/dadoshistoricos/2026.zip", timeout=60, headers=UA, allow_redirects=True)
inm["arquivo_2026"] = {"status": r.status_code, "tamanho": r.headers.get("content-length"), "modificado": r.headers.get("last-modified")}
OUT["inmet"] = inm

os.makedirs("lab", exist_ok=True)
json.dump(OUT, open("lab/sondagem.json", "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(OUT, ensure_ascii=False, default=str)[:3000])
