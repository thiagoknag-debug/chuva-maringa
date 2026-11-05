"""Ingredientes de granizo para Maringá numa janela (padrão: agora até amanhã 08h). Grava lab/sondagem_granizo.json."""
import json, statistics as st, datetime as dt, requests
UA = {"User-Agent": "chuva-maringa"}
B = {"latitude": -23.42, "longitude": -51.94, "timezone": "America/Sao_Paulo"}
M = ["ecmwf_ifs", "ecmwf_ifs025", "gfs_seamless", "icon_seamless", "meteofrance_seamless", "ukmo_seamless", "jma_seamless", "gem_seamless", "cma_grapes_global", "best_match"]
V = ["precipitation", "cape", "lifted_index", "convective_inhibition", "freezing_level_height", "wind_gusts_10m",
     "temperature_850hPa", "temperature_500hPa", "dew_point_850hPa", "wind_speed_850hPa", "wind_direction_850hPa",
     "wind_speed_500hPa", "wind_direction_500hPa", "wind_speed_10m", "wind_direction_10m", "weather_code"]
out = {"gerado": dt.datetime.now(dt.timezone.utc).isoformat()}
f = requests.get("https://api.open-meteo.com/v1/forecast", params={**B, "forecast_days": 2, "models": ",".join(M), "hourly": ",".join(V), "wind_speed_unit": "ms"}, headers=UA, timeout=120).json()
H = f["hourly"]; T = H["time"]
agora = dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))).replace(tzinfo=None, minute=0, second=0, microsecond=0)
fim = (agora + dt.timedelta(days=1)).replace(hour=9)
import math
def uv(s, d): r = math.radians(d); return -s * math.sin(r), -s * math.cos(r)
horas = []
for i, t in enumerate(T):
    tt = dt.datetime.fromisoformat(t)
    if tt < agora or tt > fim: continue
    lin = {"hora": t[5:16]}
    for m in M:
        g = lambda v: (H.get(f"{v}_{m}") or [None] * len(T))[i]
        cape, li, cin, fz, pr, gu = g("cape"), g("lifted_index"), g("convective_inhibition"), g("freezing_level_height"), g("precipitation"), g("wind_gusts_10m")
        t85, t50 = g("temperature_850hPa"), g("temperature_500hPa")
        sh = None
        if None not in (g("wind_speed_500hPa"), g("wind_direction_500hPa"), g("wind_speed_10m"), g("wind_direction_10m")):
            a = uv(g("wind_speed_500hPa"), g("wind_direction_500hPa")); b = uv(g("wind_speed_10m"), g("wind_direction_10m"))
            sh = round(math.hypot(a[0] - b[0], a[1] - b[1]), 1)
        lin[m] = {"cape": cape, "li": li, "cin": cin, "isoterma0_m": fz, "chuva": pr, "rajada_kmh": round(gu * 3.6) if gu is not None else None,
                  "lapse_850_500": round(t85 - t50, 1) if None not in (t85, t50) else None, "t500": t50, "cisalh_0_6km_ms": sh, "wcode": g("weather_code")}
    horas.append(lin)
out["horas"] = horas
# resumo por hora (mediana/máximo entre modelos)
res = []
for h in horas:
    def col(k): return [h[m][k] for m in M if m in h and h[m][k] is not None]
    r = {"hora": h["hora"]}
    for k in ["cape", "li", "cin", "isoterma0_m", "chuva", "rajada_kmh", "lapse_850_500", "t500", "cisalh_0_6km_ms"]:
        c = col(k); r[k] = (round(st.median(c), 1), round(max(c), 1), round(min(c), 1)) if c else None
    r["modelos_cape>=1500_e_chuva>=1"] = sum(1 for m in M if m in h and (h[m]["cape"] or 0) >= 1500 and (h[m]["chuva"] or 0) >= 1)
    r["modelos_li<=-4_e_chuva>=0.5"] = sum(1 for m in M if m in h and h[m]["li"] is not None and h[m]["li"] <= -4 and (h[m]["chuva"] or 0) >= 0.5)
    r["wcodes"] = col("wcode")
    res.append(r)
out["resumo"] = res
# conjuntos: fração de membros com CAPE alto + chuva por hora
ens = {}
for e in ["ecmwf_ifs025", "gfs025", "gem_global", "ukmo_global_ensemble_20km"]:
    try:
        h = requests.get("https://ensemble-api.open-meteo.com/v1/ensemble", params={**B, "forecast_days": 2, "models": e, "hourly": "precipitation,cape,wind_gusts_10m"}, headers=UA, timeout=120).json()["hourly"]
    except Exception as x: ens[e] = repr(x); continue
    lst = []
    for i, t in enumerate(h["time"]):
        tt = dt.datetime.fromisoformat(t)
        if tt < agora or tt > fim: continue
        n = s = c2 = 0
        for k in h:
            if not k.startswith("precipitation"): continue
            suf = k[len("precipitation"):]; p = h[k][i]; c = (h.get("cape" + suf) or [None] * len(h["time"]))[i]
            if p is None or c is None: continue
            n += 1; s += (c >= 1500 and p >= 1); c2 += (c >= 2500 and p >= 1)
        if n: lst.append({"hora": t[5:16], "membros": n, "%cape1500+chuva": round(100 * s / n), "%cape2500+chuva": round(100 * c2 / n)})
    ens[e] = lst
out["conjuntos"] = ens
try:
    av = requests.get("https://apiprevmet3.inmet.gov.br/avisos/ativos", headers=UA, timeout=40).json()
    out["avisos_inmet"] = [{k: a.get(k) for k in ["descricao", "severidade", "data_inicio", "hora_inicio", "data_fim", "hora_fim", "riscos", "instrucoes"]}
                           for a in av.get("hoje", []) + av.get("futuro", []) if "Maringá - PR" in (a.get("municipios") or "")]
except Exception as x: out["avisos_erro"] = repr(x)
try: out["metar"] = requests.get("https://aviationweather.gov/api/data/metar", params={"ids": "SBMG", "hours": 6, "format": "raw"}, headers=UA, timeout=30).text.strip().splitlines()
except Exception as x: out["metar_erro"] = repr(x)
json.dump(out, open("lab/sondagem_granizo.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in out if k != "horas"}, ensure_ascii=False)[:5000])
