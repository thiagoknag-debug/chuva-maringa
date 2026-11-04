import json, time, datetime as dt, requests
UA = {"User-Agent": "chuva-maringa-sondagem"}
O = {}
def st(u, **kw):
    try:
        r = requests.get(u, timeout=60, headers={**UA, "Origin": "https://thiagoknag-debug.github.io"}, **kw)
        return {"status": r.status_code, "tipo": r.headers.get("content-type"), "cors": r.headers.get("access-control-allow-origin"), "bytes": len(r.content)}, r
    except Exception as e:
        return {"erro": str(e)[:150]}, None
# satélite GIBS em Web Mercator
g = {}
for lay in ["GOES-East_ABI_Band13_Clean_Infrared", "GOES-East_ABI_Air_Mass", "GOES-East_ABI_GeoColor"]:
    for tms in ["GoogleMapsCompatible_Level6", "GoogleMapsCompatible_Level7", "GoogleMapsCompatible_Level8"]:
        for z, y, x in [(4, 9, 5), (5, 18, 10)]:
            k = f"{lay}|{tms}|{z}"
            g[k], _ = st(f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{lay}/default/default/{tms}/{z}/{y}/{x}.png")
O["gibs"] = {k: v for k, v in g.items() if v.get("status") == 200} or {"nenhum": list(g.items())[:3]}
# CEMADEN: estações de Maringá e CORS
d, r = st("https://resources.cemaden.gov.br/graficos/interativo/getJson2.php?uf=PR")
O["cemaden"] = d
if r is not None and r.status_code == 200:
    try:
        j = json.loads(r.text); O["cemaden"]["total"] = len(j)
        O["cemaden"]["maringa"] = [x for x in j if str(x.get("codibge")) == "4115200" or "MARING" in str(x.get("cidade", "")).upper()]
        O["cemaden"]["campos"] = list(j[0].keys()) if j else []
    except Exception as e: O["cemaden"]["parse"] = str(e)[:150]
# CORS das fontes usadas pelo site
for nome, u in [("openmeteo", "https://api.open-meteo.com/v1/forecast?latitude=-23.4&longitude=-51.9&hourly=temperature_2m&forecast_days=1"),
                ("ensemble", "https://ensemble-api.open-meteo.com/v1/ensemble?latitude=-23.4&longitude=-51.9&hourly=precipitation&models=gfs025&forecast_days=1"),
                ("inmet_avisos", "https://apiprevmet3.inmet.gov.br/avisos/ativos"),
                ("rainviewer", "https://api.rainviewer.com/public/weather-maps.json")]:
    O["cors_" + nome], _ = st(u)
# histórico do aeroporto (com pausa para não tomar limite)
time.sleep(10)
d, r = st("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py", params={"station": "SBMG", "data": ["sknt", "gust", "wxcodes"],
          "year1": 2024, "month1": 9, "day1": 1, "year2": 2024, "month2": 9, "day2": 30, "tz": "Etc/UTC", "format": "onlycomma", "report_type": [3, 4]})
if r is not None and r.status_code == 200:
    L = r.text.strip().splitlines(); d["linhas_set2024"] = len(L) - 1; d["exemplo"] = L[1:3]
    d["horas_distintas"] = len({l.split(",")[1][:13] for l in L[1:]})
O["sbmg_hist"] = d
json.dump(O, open("lab/sondagem2.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(O, ensure_ascii=False)[:2000])
