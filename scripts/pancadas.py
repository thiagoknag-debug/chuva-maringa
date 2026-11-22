"""Calibra o índice de pancadas/trovoada de Maringá.
Alvo: o que o aeroporto (SBMG, METAR) registrou em cada dia — trovoada (TS ou VCTS) e chuva (RA/DZ/SH) — e o pluviômetro do INMET quando houver.
Previsores: o que 11 modelos previam na véspera (Open-Meteo Previous Runs): energia (CAPE) e chuva.
Teste fora da amostra (treino no período mais antigo, teste no mais recente). Grava lab/pancadas.json e, se ganhar da climatologia, lab/pesos.json["pancadas"]."""
import io, json, time, zipfile, datetime as dt
import numpy as np, pandas as pd, requests
LAT, LON, TZ = -23.4053, -51.9328, "America/Sao_Paulo"
MODELS = ["ecmwf_ifs", "ecmwf_ifs025", "ecmwf_aifs025_single", "gfs_seamless", "icon_seamless", "meteofrance_seamless",
          "ukmo_seamless", "jma_seamless", "gem_seamless", "cma_grapes_global", "best_match"]
UA = {"User-Agent": "chuva-maringa-auditoria"}
HOJE = pd.Timestamp.now(tz=TZ).tz_localize(None).normalize()
INI = pd.Timestamp("2024-09-01"); FIM = HOJE - pd.Timedelta(days=1)
def get(url, params=None, tries=5, timeout=240):
    for k in range(tries):
        try:
            r = requests.get(url, params=params, timeout=timeout, headers=UA)
            if r.status_code == 200: return r
            print("HTTP", r.status_code, url, r.text[:150], flush=True)
        except Exception as e: print("erro", e, flush=True)
        time.sleep(15 * (k + 1))
    return None
def meses():
    d = INI
    while d <= FIM:
        e = min(d + pd.offsets.MonthEnd(0), FIM); yield d, e; d = e + pd.Timedelta(days=1)
# ---- previsões arquivadas por antecedência (1, 2, 3 e 5 dias antes) ----
LEADS = [1, 2, 3, 5]
def prev_runs(a, b, l):
    for k in range(6):
        try:
            r = requests.get("https://previous-runs-api.open-meteo.com/v1/forecast", timeout=300, headers=UA, params={"latitude": LAT, "longitude": LON, "timezone": TZ,
                "start_date": a.strftime("%Y-%m-%d"), "end_date": b.strftime("%Y-%m-%d"), "hourly": f"precipitation_previous_day{l},cape_previous_day{l}", "models": ",".join(MODELS)})
            if r.status_code == 200:
                j = r.json()
                if "hourly" in j: return pd.DataFrame(j["hourly"])
            print("HTTP", r.status_code, r.text[:120], flush=True)
        except Exception as e: print("erro", a.date(), l, str(e)[:120], flush=True)
        time.sleep(20 * (k + 1))
    return None
FEAT = {}
for l in LEADS:
    partes = []
    for a, b in meses():
        df = prev_runs(a, b, l)
        if df is None: print("sem previsão", l, a.date(), flush=True); continue
        df["time"] = pd.to_datetime(df["time"]); partes.append(df.set_index("time")); time.sleep(1.5)
    fc = pd.concat(partes).sort_index(); fc = fc[~fc.index.duplicated()]; dia = fc.index.normalize(); R, C = {}, {}
    for m in MODELS:
        pr_, cp_ = fc.get(f"precipitation_previous_day{l}_{m}"), fc.get(f"cape_previous_day{l}_{m}")
        if pr_ is not None: g = pr_.groupby(dia); R[m] = g.sum(min_count=1).where(g.count() >= 20)
        if cp_ is not None: g = cp_.groupby(dia); C[m] = g.max().where(g.count() >= 20)
    R, C = pd.DataFrame(R).astype(float), pd.DataFrame(C).astype(float)
    FEAT[l] = pd.DataFrame({"cape_med": C.median(axis=1), "cape_max": C.max(axis=1), "frac1": (R >= 1).sum(axis=1) / R.notna().sum(axis=1),
                            "p_med": R.median(axis=1), "p_max": R.max(axis=1)}).astype(float)
    print("antecedência", l, "dias", len(FEAT[l]), flush=True)
# ---- aeroporto ----
sb = []
for a, b in meses():
    for k in range(5):
        try:
            r = requests.get("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py", timeout=180, headers=UA,
                params={"station": "SBMG", "data": ["wxcodes"], "year1": a.year, "month1": a.month, "day1": a.day, "year2": b.year, "month2": b.month, "day2": b.day,
                        "tz": "Etc/UTC", "format": "onlycomma", "missing": "empty", "report_type": [3, 4]})
            if r.status_code == 200: sb.append(pd.read_csv(io.StringIO(r.text), dtype=str)); break
        except Exception as e: print("sbmg", e)
        time.sleep(20 * (k + 1))
    time.sleep(6); print("sbmg", a.date(), flush=True)
sb = pd.concat(sb, ignore_index=True)
sb["local"] = pd.to_datetime(sb["valid"], errors="coerce") - pd.Timedelta(hours=3); sb = sb.dropna(subset=["local"]).drop_duplicates("local")
wx = sb["wxcodes"].fillna("").astype(str)
sb["ts"] = wx.str.contains(r"(^|\s)(VC)?[-+]?TS", regex=True); sb["chuva"] = wx.str.contains(r"(^|\s)[-+]?(TS|SH)?(RA|DZ)", regex=True)
sb["forte"] = wx.str.contains(r"(^|\s)\+(TS|SH)?RA|TSRA|\+TSRA", regex=True)
g = sb.groupby(sb["local"].dt.normalize()); n = g.size()
obs = pd.DataFrame({"ts": g["ts"].any(), "chuva": g["chuva"].any(), "forte": g["forte"].any(), "n": n})
obs = obs[obs.n >= 18]
# ---- INMET (quando o pluviômetro funciona) ----
def inmet(ano):
    r = get(f"https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip", timeout=600)
    if r is None: return None
    z = zipfile.ZipFile(io.BytesIO(r.content)); nm = [x for x in z.namelist() if "A835" in x.upper()]
    if not nm: return None
    L = z.read(nm[0]).decode("latin-1").splitlines(); h = next(i for i, l in enumerate(L) if l.upper().startswith("DATA") and "HORA" in l.upper())
    df = pd.read_csv(io.StringIO("\n".join(L[h:])), sep=";", decimal=",", dtype=str)
    cp = [c for c in df.columns if "PRECIPITA" in c.upper()][0]
    v = pd.to_numeric(df[cp].astype(str).str.replace(",", ".").str.strip(), errors="coerce"); v = v.where(v > -9000)
    t = pd.to_datetime(df[df.columns[0]].str.replace("/", "-").str.strip() + " " + df[df.columns[1]].str.extract(r"(\d{2})")[0] + ":00", errors="coerce") - pd.Timedelta(hours=3)
    return pd.Series(v.values, index=t).dropna()
iv = pd.concat([s for s in (inmet(a) for a in (2024, 2025, 2026)) if s is not None]).sort_index(); iv = iv[~iv.index.duplicated()]
gi = iv.groupby(iv.index.normalize()); imm = gi.sum().where(gi.count() >= 24); imax = gi.max().where(gi.count() >= 24)
obs["mm"] = imm.reindex(obs.index); obs["mmh_max"] = imax.reindex(obs.index)
# ---- tabela e ajuste por antecedência ----
def feats(df, k):
    base = {"f": [df.frac1], "fc": [df.frac1, df.cape_med / 1000], "fcp": [df.frac1, df.cape_med / 1000, np.log1p(df.p_max)],
            "fcpi": [df.frac1, df.cape_med / 1000, np.log1p(df.p_max), (df.cape_med / 1000) * (df.p_max >= 1)]}[k]
    return np.c_[tuple(base)]
def fit(Xm, y, it=60, lam=1e-2):
    A = np.c_[np.ones(len(Xm)), Xm]; b = np.zeros(A.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-A @ b)); W = p * (1 - p) + 1e-9
        b = b + np.linalg.solve(A.T @ (A * W[:, None]) + lam * np.eye(len(b)), A.T @ (y - p) - lam * b)
    return b
pred = lambda b, Xm: 1 / (1 + np.exp(-(np.c_[np.ones(len(Xm)), Xm] @ b)))
def auc(p, y):
    o = np.argsort(p); y = y[o]; n1 = y.sum(); n0 = len(y) - n1
    return float((np.cumsum(1 - y)[y == 1].sum()) / (n1 * n0)) if n1 and n0 else None
res = {"gerado": str(HOJE.date()), "leads": {}}; fin_all = {}
for l in LEADS:
    D = FEAT[l].join(obs, how="inner").dropna(subset=["cape_med", "frac1", "p_med", "p_max"])
    for c_ in ["ts", "chuva", "forte"]: D[c_] = D[c_].astype(bool)
    if l == 1: D.to_csv("lab/pancadas_dados.csv")
    D["cape_med"] = D["cape_med"].clip(upper=3700)
    corte = D.index[int(len(D) * 0.6)]; tr, te = D[D.index < corte], D[D.index >= corte]
    out_l = {"periodo": [str(D.index.min().date()), str(D.index.max().date())], "corte_teste": str(corte.date()), "n_treino": len(tr), "n_teste": len(te), "alvos": {}}
    fin = {}
    for alvo in ["ts", "chuva", "forte"]:
        ytr, yte = tr[alvo].astype(float).values, te[alvo].astype(float).values
        clim = ytr.mean(); bs_c = float(np.mean((clim - yte) ** 2)); o = {"taxa_treino": round(clim, 3), "taxa_teste": round(float(yte.mean()), 3), "brier_clima": round(bs_c, 4), "modelos": {}}
        for k in ["f", "fc", "fcp", "fcpi"]:
            b = fit(feats(tr, k), ytr); p = pred(b, feats(te, k)); bs = float(np.mean((p - yte) ** 2))
            bins = pd.cut(p, [0, .1, .2, .35, .5, .7, 1.01]); rel = pd.DataFrame({"p": p, "y": yte}).groupby(bins, observed=True).agg(prev=("p", "mean"), obs=("y", "mean"), n=("y", "size"))
            o["modelos"][k] = {"coef": [round(float(x), 4) for x in b], "brier": round(bs, 4), "bss": round(1 - bs / bs_c, 3), "auc": round(auc(p, yte), 3) if auc(p, yte) else None,
                               "confiab": [[round(r.prev, 2), round(r.obs, 2), int(r.n)] for r in rel.itertuples()]}
        kb = max(o["modelos"], key=lambda q: o["modelos"][q]["bss"]); o["melhor"] = kb; out_l["alvos"][alvo] = o
        if o["modelos"][kb]["bss"] > 0.03:
            b = fit(feats(D, kb), D[alvo].astype(float).values)
            fin[alvo] = {"feats": kb, "coef": [round(float(x), 4) for x in b], "bss_teste": o["modelos"][kb]["bss"], "auc_teste": o["modelos"][kb]["auc"], "n": len(D)}
    if l == 1:
        z = D[D.p_med < 0.5]
        out_l["mediana_zero_por_cape"] = [[f"{a}-{b}", int(len(s_)), round(float(s_.ts.mean()), 2) if len(s_) else None, round(float(s_.chuva.mean()), 2) if len(s_) else None]
            for a, b in [(0, 1000), (1000, 2000), (2000, 3000), (3000, 99999)] for s_ in [z[(z.cape_med >= a) & (z.cape_med < b)]]]
    res["leads"][str(l)] = out_l; fin_all[str(l)] = fin
    print("antecedência", l, {a: (v["melhor"], v["modelos"][v["melhor"]]["bss"], v["modelos"][v["melhor"]]["auc"]) for a, v in out_l["alvos"].items()}, flush=True)
pj = json.load(open("lab/pesos.json"))
if fin_all.get("1"):
    pj["pancadas"] = {"gerado": str(HOJE.date()), **fin_all["1"], "leads": fin_all}
    json.dump(pj, open("lab/pesos.json", "w"), ensure_ascii=False, indent=1)
json.dump(res, open("lab/pancadas.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({l: {a: v["modelos"][v["melhor"]]["bss"] for a, v in o["alvos"].items()} for l, o in res["leads"].items()}))
