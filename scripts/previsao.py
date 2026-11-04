"""Previsão de Maringá (mesma lógica do site), usada pelo aviso no celular.
Calcula, para hoje e amanhã: chuva (mediana dos modelos), chance de chuva (conjuntos),
temperatura, rajadas (corrigidas pela auditoria), avisos do INMET e risco de temporal."""
import json, math, os, statistics as st, datetime as dt
import requests

LAT, LON, TZ = -23.42, -51.94, "America/Sao_Paulo"
M = ["ecmwf_ifs", "ecmwf_ifs025", "ecmwf_aifs025_single", "gfs_seamless", "icon_seamless", "meteofrance_seamless",
     "ukmo_seamless", "jma_seamless", "gem_seamless", "cma_grapes_global", "best_match"]
ENS = [["ecmwf_ifs025"], ["ecmwf_aifs025"], ["gfs025"], ["icon_seamless"], ["gem_global"], ["ukmo_global_ensemble_20km"]]
UA = {"User-Agent": "chuva-maringa"}
B = {"latitude": LAT, "longitude": LON, "timezone": TZ}

def _get(url, params, tries=3):
    for _ in range(tries):
        try:
            r = requests.get(url, params=params, timeout=60, headers=UA)
            if r.status_code == 200: return r.json()
        except Exception: pass
    return None

def pesos():
    try: return json.load(open("lab/pesos.json"))
    except Exception: return {}

def risco_dia(mem, det, alerta_lvl, rcape=None):
    """mem: lista de (chuva_mm, rajada_max|None, cape_max|None) por cenário; det: idem por modelo (rajada já corrigida).
    alerta_lvl: None/'amarelo'/'laranja'/'vermelho' (avisos de tempestade/chuva/vento do INMET)."""
    def severo(r, g, c):
        return (g is not None and g >= 70) or (r is not None and r >= 50) or \
               (c is not None and r is not None and c >= 2000 and r >= 20) or \
               (c is not None and g is not None and r is not None and c >= 1000 and g >= 55 and r >= 10)
    pe = sum(severo(*x) for x in mem) / len(mem) if mem else 0
    pd_ = sum(severo(*x) for x in det) / len(det) if det else 0
    raw = 100 * (0.7 * pe + 0.3 * pd_) if mem else 100 * pd_
    if rcape and det:
        cm = max([x[2] or 0 for x in det])
        fx = next((x for x in rcape if x["de"] <= cm < x["ate"]), None)
        if fx and fx.get("taxa") is not None and fx.get("eventos", 0) >= 2: raw = max(raw, 100 * fx["taxa"])
    piso = {"amarelo": 10, "laranja": 35, "vermelho": 65}.get(alerta_lvl, 0)
    p = int(round(min(95, max(raw, piso))))
    gmed = st.median([x[1] for x in det if x[1] is not None]) if any(x[1] is not None for x in det) else 0
    p50 = 100 * sum(1 for x in mem if x[0] is not None and x[0] >= 50) / len(mem) if mem else 0
    parecido = p >= 35 and (gmed >= 55 or p50 >= 15 or (alerta_lvl in ("laranja", "vermelho") and raw >= 15))
    nivel = "Muito alto" if p >= 50 else "Alto" if p >= 25 else "Moderado" if p >= 10 else "Baixo"
    return {"pct": p, "nivel": nivel, "parecido_2_11": bool(parecido), "bruto": round(raw), "piso_inmet": piso}

def calcular():
    PJ = pesos(); FR = (PJ.get("vento") or {}).get("fator_rajada", {})
    f = _get("https://api.open-meteo.com/v1/forecast", {**B, "forecast_days": 3, "models": ",".join(M),
             "hourly": "precipitation,temperature_2m,wind_speed_10m,wind_gusts_10m,cape"})
    if not f: raise RuntimeError("sem previsão dos modelos")
    T = f["hourly"]["time"]; H = f["hourly"]
    E = []
    for ids in ENS:
        for i in ids:
            j = _get("https://ensemble-api.open-meteo.com/v1/ensemble", {**B, "forecast_days": 3, "models": i,
                     "hourly": "precipitation,wind_gusts_10m,cape"}, tries=1)
            if j and any(k.startswith("precipitation") and any(x is not None for x in v) for k, v in j.get("hourly", {}).items()): E.append(j); break
    try:
        av = requests.get("https://apiprevmet3.inmet.gov.br/avisos/ativos", timeout=40, headers=UA).json()
        lv = {"Perigo Potencial": "amarelo", "Perigo": "laranja", "Grande Perigo": "vermelho"}
        avisos = [{"lvl": lv.get(a.get("severidade"), "amarelo"), "tit": str(a.get("descricao", "")).lower(),
                   "ini": a["data_inicio"][:10], "fim": a["data_fim"][:10]}
                  for a in (av.get("hoje", []) + av.get("futuro", []))
                  if "Maringá - PR" in (a.get("municipios") or "") or "Maringa - PR" in (a.get("municipios") or "")]
    except Exception:
        avisos = []
    ordem = {"amarelo": 1, "laranja": 2, "vermelho": 3}
    hoje = dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))).date()
    dias = []
    for k in range(2):
        d = (hoje + dt.timedelta(days=k)).isoformat(); idx = [i for i, t in enumerate(T) if t.startswith(d)]
        def soma(a): v = [a[i] for i in idx]; return None if any(x is None for x in v) else sum(v)
        def mx(a): v = [a[i] for i in idx if a[i] is not None]; return max(v) if v else None
        chuva = [soma(H[f"precipitation_{m}"]) for m in M if f"precipitation_{m}" in H]
        chuva = [x for x in chuva if x is not None]
        det = []
        for m in M:
            r = soma(H.get(f"precipitation_{m}", [None] * len(T)))
            g = mx(H.get(f"wind_gusts_10m_{m}", [None] * len(T))); c = mx(H.get(f"cape_{m}", [None] * len(T)))
            if g is not None: g *= FR.get(m, 1)
            if r is not None: det.append((r, g, c))
        temps = [H[f"temperature_2m_{m}"][i] for m in M for i in idx if H.get(f"temperature_2m_{m}") and H[f"temperature_2m_{m}"][i] is not None]
        tmax = max(st.median([H[f"temperature_2m_{m}"][i] for m in M if H.get(f"temperature_2m_{m}") and H[f"temperature_2m_{m}"][i] is not None]) for i in idx)
        tmin = min(st.median([H[f"temperature_2m_{m}"][i] for m in M if H.get(f"temperature_2m_{m}") and H[f"temperature_2m_{m}"][i] is not None]) for i in idx)
        gust = st.median([x[1] for x in det if x[1] is not None]) if det else None
        mem = []
        for j in E:
            h = j["hourly"]; tix = {t: i for i, t in enumerate(h["time"])}; ii = [tix[t] for t in T if t.startswith(d) and t in tix]
            for key in [x for x in h if x.startswith("precipitation")]:
                v = [h[key][i] for i in ii if h[key][i] is not None]
                if not (len(v) >= 20 or len(v) in (4, 8)): continue
                suf = key[len("precipitation"):]
                g = [h.get("wind_gusts_10m" + suf, [None] * len(h["time"]))[i] for i in ii]; g = [x for x in g if x is not None]
                c = [h.get("cape" + suf, [None] * len(h["time"]))[i] for i in ii]; c = [x for x in c if x is not None]
                mem.append((sum(v), max(g) if g else None, max(c) if c else None))
        chance = round(100 * sum(1 for x in mem if x[0] >= 1) / len(mem)) if mem else None
        lvl = None
        for a in avisos:
            if a["ini"] <= d <= a["fim"] and any(w in a["tit"] for w in ("tempestade", "chuva", "vento", "vendaval", "granizo")):
                if lvl is None or ordem[a["lvl"]] > ordem[lvl]: lvl = a["lvl"]
        # horários: chuva mais forte, rajada mais forte e janela de trovoada (cenários com chuva + CAPE>=1500 ou rajada>=55)
        def medh(var, i, fr=False):
            v = [H[f"{var}_{m}"][i] * (FR.get(m, 1) if fr else 1) for m in M if H.get(f"{var}_{m}") and H[f"{var}_{m}"][i] is not None]
            return st.median(v) if v else None
        agora_h = dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))).hour if k == 0 else 0
        fut = [i for i in idx if int(T[i][11:13]) >= agora_h]
        def chance_h(i):
            n = c = 0
            for j in E:
                h = j["hourly"]; tix = {t: q for q, t in enumerate(h["time"])}
                if T[i] not in tix: continue
                for key in [x for x in h if x.startswith("precipitation")]:
                    v = h[key][tix[T[i]]]
                    if v is not None: n += 1; c += v >= 0.2
            return 100 * c / n if n else 0
        pr = [(medh("precipitation", i) or 0, int(T[i][11:13])) for i in fut if chance_h(i) >= 30]
        pico_chuva = max(pr)[1] if pr and max(pr)[0] >= 0.5 else None
        gr = [(medh("wind_gusts_10m", i, True) or 0, int(T[i][11:13])) for i in fut]
        pico_rajada = max(gr)[1] if gr else None
        tro = []
        for i in fut:
            n = ts = 0
            for j in E:
                h = j["hourly"]; tix = {t: q for q, t in enumerate(h["time"])}
                if T[i] not in tix: continue
                q = tix[T[i]]
                for key in [x for x in h if x.startswith("precipitation")]:
                    suf = key[len("precipitation"):]; pv = h[key][q]
                    gv = (h.get("wind_gusts_10m" + suf) or [None] * len(h["time"]))[q]; cv = (h.get("cape" + suf) or [None] * len(h["time"]))[q]
                    if pv is None or (gv is None and cv is None): continue
                    n += 1; ts += pv >= 0.5 and ((cv is not None and cv >= 1500) or (gv is not None and gv >= 55))
            tro.append((round(100 * ts / n) if n else 0, int(T[i][11:13])))
        janela_tro = None
        if tro and max(tro)[0] >= 25:
            pk = max(tro); lim = max(25, round(pk[0] * 0.75)); hs = [h_ for v_, h_ in tro if v_ >= lim]
            janela_tro = {"de": hs[0], "ate": hs[-1] + 1, "pico": pk[1], "pct": pk[0]}
        dias.append({"dia": d, "chuva_mm": round(st.median(chuva), 1) if chuva else None, "chance": chance,
                     "tmin": round(tmin), "tmax": round(tmax), "rajada": round(gust) if gust else None,
                     "aviso": lvl, "pico_chuva": pico_chuva, "pico_rajada": pico_rajada, "trovoada": janela_tro, "risco": risco_dia(mem, det, lvl, PJ.get("risco_cape")), "cenarios": len(mem)})
    return {"gerado": dt.datetime.now(dt.timezone.utc).isoformat(), "dias": dias, "avisos": avisos}

if __name__ == "__main__":
    print(json.dumps(calcular(), ensure_ascii=False, indent=1))
