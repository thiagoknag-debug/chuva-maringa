"""Chance de chuva HORA A HORA calibrada para Maringá.
Alvo: em cada hora, o aeroporto (METAR SBMG) registrou chuva (RA/DZ/SH/TS, presente ou 'recente' RE..)?  e trovoada?
Previsores: o que 11 modelos previam hora a hora (Open-Meteo Previous Runs; d0 = rodada mais nova, d1 = da véspera),
energia (CAPE), chuva do dia e o ciclo do dia (pancada costuma vir à tarde). Teste fora da amostra (treino até 2025, teste 2026).
Grava lab/hora.json e pesos.json['hora'] (coeficientes que o site aplica)."""
import io, os, sys, json, time, datetime as dt
import numpy as np, pandas as pd, requests
LAT, LON, TZ = -23.4053, -51.9328, "America/Sao_Paulo"
MODELS = ["ecmwf_ifs", "ecmwf_ifs025", "ecmwf_aifs025_single", "gfs_seamless", "icon_seamless", "meteofrance_seamless",
          "ukmo_seamless", "jma_seamless", "gem_seamless", "cma_grapes_global", "best_match"]
UA = {"User-Agent": "chuva-maringa-auditoria"}; CACHE = "lab/cache"; os.makedirs(CACHE, exist_ok=True)
HOJE = pd.Timestamp.now(tz=TZ).tz_localize(None).normalize(); INI = pd.Timestamp("2024-09-01"); FIM = HOJE - pd.Timedelta(days=1)
def meses():
    d = INI
    while d <= FIM:
        e = min(d + pd.offsets.MonthEnd(0), FIM); yield d, e; d = e + pd.Timedelta(days=1)
def prev(a, b, l):
    suf = "" if l == 0 else f"_previous_day{l}"
    for k in range(7):
        try:
            r = requests.get("https://previous-runs-api.open-meteo.com/v1/forecast", timeout=150, headers=UA, params={
                "latitude": LAT, "longitude": LON, "timezone": TZ, "start_date": str(a.date()), "end_date": str(b.date()),
                "hourly": f"precipitation{suf},cape{suf}", "models": ",".join(MODELS)})
            if r.status_code == 200 and "hourly" in r.text:
                df = pd.DataFrame(r.json()["hourly"]); df["time"] = pd.to_datetime(df["time"]); df = df.set_index("time")
                ren = {}
                for m in MODELS:
                    ren[f"precipitation{suf}_{m}"] = "p_" + m; ren[f"cape{suf}_{m}"] = "c_" + m
                return df.rename(columns=ren)[[c for c in ren.values() if c in df.rename(columns=ren).columns]].astype(float)
            print("HTTP", r.status_code, r.text[:120], flush=True)
        except Exception as e: print("erro", a.date(), l, str(e)[:100], flush=True)
        time.sleep(5 * (k + 1))
    return None
def carrega(l):
    fn = f"{CACHE}/hora_d{l}.csv.gz"
    old = pd.read_csv(fn, index_col=0, parse_dates=True) if os.path.exists(fn) else pd.DataFrame()
    for a, b in meses():
        if not old.empty and b < FIM - pd.Timedelta(days=40) and len(old.loc[a:b + pd.Timedelta(hours=23)]) >= 24 * ((b - a).days + 1) - 24: continue
        df = prev(a, b, l)
        if df is None: print("sem previsão", l, a.date(), flush=True); continue
        old = pd.concat([old[~old.index.isin(df.index)], df]).sort_index(); old.to_csv(fn, float_format="%.2f", compression="gzip")
        print("previsões", l, a.date(), len(df), flush=True); time.sleep(1)
    return old
def metar():
    fn = f"{CACHE}/metar_sbmg_hora.csv.gz"
    old = pd.read_csv(fn, index_col=0, parse_dates=True) if os.path.exists(fn) else pd.DataFrame()
    partes = []
    for a, b in meses():
        if not old.empty and b < FIM - pd.Timedelta(days=40) and len(old.loc[a:b + pd.Timedelta(hours=23)]) > 0: continue
        for k in range(5):
            try:
                a2, b2 = a - pd.Timedelta(days=1), b + pd.Timedelta(days=1)
                r = requests.get("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py", timeout=180, headers=UA,
                    params={"station": "SBMG", "data": ["wxcodes", "metar"], "year1": a2.year, "month1": a2.month, "day1": a2.day,
                            "year2": b2.year, "month2": b2.month, "day2": b2.day, "tz": "Etc/UTC", "format": "onlycomma", "missing": "empty", "report_type": [3, 4]})
                if r.status_code == 200: partes.append(pd.read_csv(io.StringIO(r.text), dtype=str)); break
            except Exception as e: print("sbmg", e, flush=True)
            time.sleep(15 * (k + 1))
        time.sleep(4); print("metar", a.date(), flush=True)
    if partes:
        sb = pd.concat(partes, ignore_index=True); sb["t"] = pd.to_datetime(sb["valid"], errors="coerce") - pd.Timedelta(hours=3)
        sb = sb.dropna(subset=["t"]).drop_duplicates("t").sort_values("t")
        wx = sb["wxcodes"].fillna("").astype(str); raw = sb["metar"].fillna("").astype(str)
        chuva = wx.str.contains(r"(^|\s)[-+]?(VC)?(TS|SH)?(RA|DZ)", regex=True) | raw.str.contains(r"\sRE(TS|SH)?(RA|DZ)", regex=True)
        trov = wx.str.contains(r"(^|\s)[-+]?(VC)?TS", regex=True) | raw.str.contains(r"\sRETS", regex=True)
        forte = wx.str.contains(r"(^|\s)\+(TS|SH)?RA|TSRA", regex=True)
        h = sb["t"].dt.ceil("h")   # relatório entre h-1 e h vai para a hora que termina em h
        H = pd.DataFrame({"n": 1, "chuva": chuva.values, "trov": trov.values, "forte": forte.values}, index=h.values).groupby(level=0).agg({"n": "sum", "chuva": "any", "trov": "any", "forte": "any"})
        old = pd.concat([old[~old.index.isin(H.index)], H]).sort_index(); old.to_csv(fn, compression="gzip")
    return old
if len(sys.argv) > 2 and sys.argv[1] == "--so-cache":
    for l in map(int, sys.argv[2:]): carrega(l)
    sys.exit(0)
OBS = metar(); OBS = OBS[OBS.n >= 1]
print("horas com boletim:", len(OBS), "· por hora do dia:", OBS.groupby(OBS.index.hour).size().to_dict(), flush=True)
# ---------------- previsores ----------------
def feats(D):
    P = D[[c for c in D.columns if c.startswith("p_")]]; C = D[[c for c in D.columns if c.startswith("c_")]]
    n = P.notna().sum(axis=1).replace(0, np.nan)
    P3 = P.rolling(3, center=True, min_periods=1).max(); P7 = P.rolling(7, center=True, min_periods=1).max()
    dia = P.index.normalize(); Pd = P.groupby(dia).sum(min_count=20); fr1d = ((Pd >= 1).sum(axis=1) / Pd.notna().sum(axis=1).replace(0, np.nan))
    cmaxd = C.max(axis=1).groupby(dia).max()
    hh = (P.index.hour - 0.5) % 24; w = 2 * np.pi * hh / 24
    F = pd.DataFrame({"f01": (P3 >= 0.1).sum(axis=1) / n, "f05": (P3 >= 0.5).sum(axis=1) / n, "f01w": (P7 >= 0.1).sum(axis=1) / n,
                      "pmed": np.log1p(P3.median(axis=1)), "pmax": np.log1p(P3.max(axis=1)),
                      "fr1d": fr1d.reindex(dia).values, "cape": C.median(axis=1).clip(upper=3700) / 1000, "capemax": cmaxd.reindex(dia).clip(upper=4000).values / 1000,
                      "s1": np.sin(w), "c1": np.cos(w), "s2": np.sin(2 * w), "c2": np.cos(2 * w), "bruto": (P >= 0.1).sum(axis=1) / n}, index=P.index)
    F["cs1"], F["cc1"], F["fs1"], F["fc1"] = F.cape * F.s1, F.cape * F.c1, F.fr1d * F.s1, F.fr1d * F.c1
    return F
CONJ = {"A": ["f01", "f05", "f01w", "pmed"], "B": ["f01", "f05", "f01w", "pmed", "fr1d", "cape", "capemax"],
        "C": ["f01", "f05", "f01w", "pmed", "fr1d", "cape", "capemax", "s1", "c1", "s2", "c2"],
        "D": ["f01", "f05", "f01w", "pmed", "fr1d", "cape", "capemax", "s1", "c1", "s2", "c2", "cs1", "cc1", "fs1", "fc1"]}
def fit(X, y, it=40, lam=1e-1):
    A = np.c_[np.ones(len(X)), X]; b = np.zeros(A.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-np.clip(A @ b, -30, 30))); W = p * (1 - p) + 1e-9
        b = b + np.linalg.solve(A.T @ (A * W[:, None]) + lam * np.eye(len(b)), A.T @ (y - p) - lam * b)
    return b
pred = lambda b, X: 1 / (1 + np.exp(-np.clip(np.c_[np.ones(len(X)), X] @ b, -30, 30)))
def auc(p, y):
    o = np.argsort(p, kind="mergesort"); y = y[o]; n1 = y.sum(); n0 = len(y) - n1
    return float(np.cumsum(1 - y)[y == 1].sum() / (n1 * n0)) if n1 and n0 else None
bs = lambda p, y: float(np.mean((p - y) ** 2))
def confiab(p, y):
    out = []
    for a_, b_ in ((0, .05), (.05, .1), (.1, .2), (.2, .3), (.3, .45), (.45, .6), (.6, .8), (.8, 1.01)):
        k = (p >= a_) & (p < b_)
        if k.sum() >= 20: out.append([round(float(p[k].mean()), 3), round(float(y[k].mean()), 3), int(k.sum())])
    return out
def janela(p, horas_obs):
    """horas 'mais prováveis' = ≥60% do pico do dia; quantas das horas com chuva caíram dentro"""
    if p.max() <= 0: return None
    jan = p >= 0.6 * p.max(); return float((jan & horas_obs).sum() / max(1, horas_obs.sum())), float(jan.mean())
RES = {"gerado": str(HOJE.date()), "leads": {}}; PES = {}
for l in (0, 1):
    D = carrega(l); F = feats(D)
    T = F.join(OBS[["chuva", "trov", "forte"]], how="inner").dropna(subset=["f01", "fr1d", "cape", "capemax"])
    tr, te = T[T.index < "2026-01-01"], T[T.index >= "2026-01-01"]
    out = {"horas_treino": len(tr), "horas_teste": len(te), "alvos": {}}
    for alvo in ("chuva", "trov"):
        ytr, yte = tr[alvo].astype(float).values, te[alvo].astype(float).values
        clim_h = tr.groupby(tr.index.hour)[alvo].mean(); pc = te.index.hour.map(clim_h).values.astype(float)
        ref = bs(pc, yte); m = {"climatologia_por_hora": {"bs": round(ref, 4)},
                               "bruto(fração de modelos)": {"bss": round(1 - bs(te.bruto.values, yte) / ref, 3), "auc": round(auc(te.bruto.values, yte), 3)}}
        for k, cols in CONJ.items():
            b = fit(tr[cols].values, ytr); p = pred(b, te[cols].values)
            m[k] = {"bss": round(1 - bs(p, yte) / ref, 3), "auc": round(auc(p, yte), 3), "confiab": confiab(p, yte)}
        best = max(CONJ, key=lambda k: m[k]["bss"])
        # janela "mais prováveis": bruto × calibrado, nos dias de teste em que choveu no aeroporto
        pb = pred(fit(tr[CONJ[best]].values, ytr), te[CONJ[best]].values); jj = {"bruto": [], "calibrado": []}
        for d, g in te.assign(pcal=pb).groupby(te.index.normalize()):
            if len(g) < 18 or g[alvo].sum() == 0: continue
            for nome, col in (("bruto", "bruto"), ("calibrado", "pcal")):
                r = janela(g[col].values, g[alvo].values.astype(bool))
                if r: jj[nome].append(r)
        m["janela"] = {k: {"dias": len(v), "horas_com_chuva_dentro": round(float(np.mean([x[0] for x in v])), 3), "tamanho_medio_h": round(24 * float(np.mean([x[1] for x in v])), 1)} for k, v in jj.items() if v}
        # limiares para o site: por hora (ícone/chance) e por dia (existe janela de chuva × choveu ≥2 h no aeroporto)
        def hss(pr_, ob_):
            a1, b1, c1 = int((pr_ & ob_).sum()), int((pr_ & ~ob_).sum()), int((~pr_ & ob_).sum()); d1 = len(pr_) - a1 - b1 - c1; n_ = len(pr_)
            e_ = ((a1 + b1) * (a1 + c1) + (c1 + d1) * (b1 + d1)) / n_ if n_ else 0
            return {"hss": round((a1 + d1 - e_) / (n_ - e_), 3) if n_ - e_ else None, "pod": round(a1 / max(1, a1 + c1), 3), "far": round(b1 / max(1, a1 + b1), 3)}
        g_ = te.assign(pcal=pb).groupby(te.index.normalize()).agg(mx=("pcal", "max"), nh=(alvo, "sum"), n=(alvo, "size")); g_ = g_[g_.n >= 18]
        m["limiares"] = {"hora": {str(x): hss(pb >= x, yte.astype(bool)) for x in (0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5)},
                         "dia": {str(x): hss((g_.mx >= x).values, (g_.nh >= 2).values) for x in (0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5)},
                         "max_por_dia_quantis": {"choveu": [round(float(q), 3) for q in g_[g_.nh >= 2].mx.quantile([.1, .25, .5, .75, .9])],
                                                 "seco": [round(float(q), 3) for q in g_[g_.nh == 0].mx.quantile([.1, .25, .5, .75, .9])]}}
        bf = fit(T[CONJ[best]].values, T[alvo].astype(float).values)
        out["alvos"][alvo] = {"taxa_teste": round(float(yte.mean()), 3), "modelos": m, "escolhido": best}
        if m[best]["bss"] > 0.02: PES.setdefault(f"d{l}", {})[alvo] = {"feats": best, "cols": CONJ[best], "coef": [round(float(x), 4) for x in bf],
                                                                    "bss_teste": m[best]["bss"], "auc_teste": m[best]["auc"]}
        print("lead", l, alvo, json.dumps({k: (v.get("bss"), v.get("auc")) for k, v in m.items() if isinstance(v, dict) and "bss" in v}), "janela", m["janela"], "limiares", json.dumps(m["limiares"]), flush=True)
    RES["leads"][str(l)] = out
json.dump(RES, open("lab/hora.json", "w"), ensure_ascii=False, indent=1)
if PES:
    pj = json.load(open("lab/pesos.json")); pj["hora"] = {"gerado": str(HOJE.date()), **PES}; json.dump(pj, open("lab/pesos.json", "w"), ensure_ascii=False, indent=1)
print("ok", list(PES))
