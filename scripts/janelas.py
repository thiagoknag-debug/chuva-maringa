"""Janelas de chuva e tempestade hora a hora (hoje e amanhã). Grava lab/sondagem_janelas.json."""
import json, statistics as st, datetime as dt, requests
B = {"latitude": -23.42, "longitude": -51.94, "timezone": "America/Sao_Paulo"}
M = ["ecmwf_ifs", "ecmwf_ifs025", "ecmwf_aifs025_single", "gfs_seamless", "icon_seamless", "meteofrance_seamless",
     "ukmo_seamless", "jma_seamless", "gem_seamless", "cma_grapes_global", "best_match"]
ENS = ["ecmwf_ifs025", "ecmwf_aifs025", "gfs025", "icon_seamless", "gem_global", "ukmo_global_ensemble_20km"]
UA = {"User-Agent": "chuva-maringa"}
PJ = json.load(open("lab/pesos.json")); FR = PJ.get("vento", {}).get("fator_rajada", {})
f = requests.get("https://api.open-meteo.com/v1/forecast", params={**B, "forecast_days": 3, "models": ",".join(M),
                 "hourly": "precipitation,wind_gusts_10m,cape"}, headers=UA, timeout=90).json()["hourly"]
T = f["time"]
mem = []
for e in ENS:
    try:
        h = requests.get("https://ensemble-api.open-meteo.com/v1/ensemble", params={**B, "forecast_days": 3, "models": e,
                         "hourly": "precipitation,wind_gusts_10m,cape"}, headers=UA, timeout=90).json()["hourly"]
    except Exception: continue
    ix = {t: i for i, t in enumerate(h["time"])}
    for k in [k for k in h if k.startswith("precipitation")]:
        suf = k[len("precipitation"):]
        p = [h[k][ix[t]] if t in ix else None for t in T]
        if sum(x is not None for x in p[:48]) < 44: continue
        g = h.get("wind_gusts_10m" + suf); c = h.get("cape" + suf)
        mem.append((p, [g[ix[t]] if g and t in ix else None for t in T], [c[ix[t]] if c and t in ix else None for t in T]))
agora = dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))).replace(tzinfo=None)
horas = []
for i, t in enumerate(T):
    tt = dt.datetime.fromisoformat(t)
    if tt < agora.replace(minute=0, second=0, microsecond=0) or tt.date() > (agora + dt.timedelta(days=1)).date(): continue
    r = [f[f"precipitation_{m}"][i] for m in M if f.get(f"precipitation_{m}") and f[f"precipitation_{m}"][i] is not None]
    g = [f[f"wind_gusts_10m_{m}"][i] * FR.get(m, 1) for m in M if f.get(f"wind_gusts_10m_{m}") and f[f"wind_gusts_10m_{m}"][i] is not None]
    c = [f[f"cape_{m}"][i] for m in M if f.get(f"cape_{m}") and f[f"cape_{m}"][i] is not None]
    pm = [x for x in mem if x[0][i] is not None]
    pc = round(100 * sum(x[0][i] >= 0.2 for x in pm) / len(pm)) if pm else None
    pf = round(100 * sum(x[0][i] >= 2 for x in pm) / len(pm)) if pm else None
    gm = [x[1][i] for x in pm if x[1][i] is not None]; cm = [x[2][i] for x in pm if x[2][i] is not None]
    pt = round(100 * sum(1 for x in pm if x[0][i] is not None and x[0][i] >= 0.5 and (
        (x[2][i] is not None and x[2][i] >= 1500) or (x[1][i] is not None and x[1][i] >= 55))) / len(pm)) if pm else None
    horas.append({"hora": t, "chance": pc, "chance_forte": pf, "chance_tempestade": pt, "mm": round(st.median(r), 1) if r else None,
                  "mm_max": round(max(r), 1) if r else None, "rajada": round(st.median(g)) if g else None,
                  "cape_max": round(max(c)) if c else None, "cape_ens_med": round(st.median(cm)) if cm else None})
json.dump({"gerado": dt.datetime.now(dt.timezone.utc).isoformat(), "cenarios_hora": len(mem), "horas": horas},
          open("lab/sondagem_janelas.json", "w"), ensure_ascii=False, indent=1)
for x in horas: print(x)
