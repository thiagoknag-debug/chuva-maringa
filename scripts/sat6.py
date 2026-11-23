"""Satélite (GOES-19, RealEarth G19-ABI-FD-BAND13): 1) tabela cor -> temperatura do topo da nuvem (pela sonda de valores do próprio RealEarth);
2) teste nos dias disponíveis (~7): sinal de 'nuvem crescendo' perto de Maringá × chuva/trovoada no aeroporto na hora seguinte."""
import sys, subprocess, json, re, io, time, math, datetime as dt, requests
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pillow", "numpy", "pandas"], check=False)
import numpy as np, pandas as pd
from PIL import Image
UA = {"User-Agent": "Mozilla/5.0 (chuva-maringa-auditoria)"}; P = "G19-ABI-FD-BAND13"; R = {}; LAT, LON = -23.42, -51.94
def salva(): json.dump(R, open("lab/sat3.json", "w"), ensure_ascii=False, indent=1, default=str)
def img(t, b, w, h):
    u = f"https://realearth.ssec.wisc.edu/api/image?products={P}_{t.replace('.', '_')}&bounds={b[0]},{b[1]},{b[2]},{b[3]}&width={w}&height={h}"
    for k in range(3):
        try:
            r = requests.get(u, headers=UA, timeout=60)
            if r.status_code == 200: return np.asarray(Image.open(io.BytesIO(r.content)).convert("RGBA"))
        except Exception: pass
        time.sleep(2)
    return None
def sonda(t, lat, lon):
    u = f"https://realearth.ssec.wisc.edu/api/probe?products={P}_{t.replace('.', '_')}&lat={lat:.4f}&lon={lon:.4f}"
    x = requests.get(u, headers=UA, timeout=30).text
    m = re.findall(r"(-?\d+(?:\.\d+)?)\s*(?:&deg;|°)\s*C", x) or re.findall(r"(-?\d+(?:\.\d+)?)\s*(?:&deg;|°)?\s*K\b", x)
    return (float(m[-1]) if m else None), x
tempos = requests.get(f"https://realearth.ssec.wisc.edu/api/times?products={P}", headers=UA, timeout=60).json()[P]
R["tempos"] = {"n": len(tempos), "primeiro": tempos[0], "ultimo": tempos[-1]}; print(R["tempos"], flush=True)
tab = json.load(open("lab/sat_cores.json"))
C = np.array([x[0] for x in tab], float); V = np.array([x[1] for x in tab], float)
LUT = {tuple(x[0]): x[1] for x in tab}
def decodifica(a):
    rgb = a[..., :3].reshape(-1, 3).astype(np.int64); al = a[..., 3].reshape(-1)
    keys = rgb[:, 0] * 65536 + rgb[:, 1] * 256 + rgb[:, 2]; uk, inv = np.unique(keys, return_inverse=True); vals = np.empty(len(uk))
    for n_, k_ in enumerate(uk):
        c = (int(k_ // 65536), int((k_ // 256) % 256), int(k_ % 256))
        if c in LUT: vals[n_] = LUT[c]
        else:
            d = ((C - np.array(c, float)) ** 2).sum(1); j_ = int(d.argmin()); vals[n_] = V[j_] if d[j_] <= 300 else np.nan
    v = vals[inv.reshape(-1)]; v[al == 0] = np.nan
    return v.reshape(a.shape[:2])
# ---------- 2) teste ----------
BOX = (LAT - 1.0, LON - 1.1, LAT + 1.0, LON + 1.1); NW = NH = 110   # ~2 km por pixel
yy, xx = np.mgrid[0:NH, 0:NW]; plat = BOX[2] - (yy + 0.5) / NH * 2.0; plon = BOX[1] + (xx + 0.5) / NW * 2.2
dist = np.hypot((plat - LAT) * 111.2, (plon - LON) * 111.2 * math.cos(math.radians(LAT)))
from numpy.lib.stride_tricks import sliding_window_view as swv
def minviz(a, r=5):
    p = np.pad(a, r, constant_values=np.nan); return np.nanmin(swv(p, (2 * r + 1, 2 * r + 1)), axis=(-1, -2))
VAR = {"A_atual": dict(t0=-10, dt=-6, nm=-40, px=3), "B": dict(t0=-20, dt=-12, nm=-25, px=2), "C_nascendo": dict(t0=-25, dt=-15, nm=-15, px=2), "D_nascendo_rapido": dict(t0=-25, dt=-15, nm=-15, px=2, d10=-4)}
def sinal(T0, T20, T10=None, raio=40, v=VAR["A_atual"]):
    nm = minviz(T20, 5)
    novo = (T0 <= v["t0"]) & ((T0 - nm) <= v["dt"]) & (nm >= v["nm"])
    if T10 is not None: novo &= (T0 <= T10 + (v.get("d10", 1)))
    k = novo & (dist <= raio)
    if k.sum() < v["px"]: return None
    d = dist[k]; return {"px": int(k.sum()), "km": round(float(d.min()), 1)}
# frames: tardes/noites (13-03 UTC) dos dias disponíveis
fr = [t for t in tempos if int(t[9:11]) >= 13 or int(t[9:11]) <= 2]
print("frames para testar", len(fr), flush=True)
T = {}
for t in fr:
    a = img(t, BOX, NW, NH)
    if a is not None: T[t] = decodifica(a)
print("frames decodificados", len(T), flush=True)
def ts(t): return pd.Timestamp(dt.datetime.strptime(t, "%Y%m%d.%H%M%S"))
lista = sorted(T); np.savez_compressed("lab/cache/sat_quadros.npz", **{t.replace(".", "_"): T[t].astype(np.float16) for t in lista}); sig = {}
GR = {}
for vn, vv in VAR.items():
    for raio in (15, 25, 40):
        GR[(vn, raio)] = {}
        for t in lista:
            t0 = ts(t); a20 = [x for x in lista if abs((t0 - ts(x)).total_seconds() / 60 - 20) <= 3]; a10 = [x for x in lista if abs((t0 - ts(x)).total_seconds() / 60 - 10) <= 3]
            if a20: GR[(vn, raio)][t0] = sinal(T[t], T[a20[0]], T[a10[0]] if a10 else None, raio, vv)
for i, t in enumerate(lista):
    t0 = ts(t); a20 = [x for x in lista if abs((t0 - ts(x)).total_seconds() / 60 - 20) <= 3]; a10 = [x for x in lista if abs((t0 - ts(x)).total_seconds() / 60 - 10) <= 3]
    if not a20: continue
    sig[t0] = sinal(T[t], T[a20[0]], T[a10[0]] if a10 else None)
# METAR
a, b = ts(lista[0]) - pd.Timedelta(days=1), ts(lista[-1]) + pd.Timedelta(days=1)
r = requests.get("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py", timeout=180, headers=UA, params={"station": "SBMG", "data": ["wxcodes", "metar"],
    "year1": a.year, "month1": a.month, "day1": a.day, "year2": b.year, "month2": b.month, "day2": b.day, "tz": "Etc/UTC", "format": "onlycomma", "missing": "empty", "report_type": [3, 4]})
sb = pd.read_csv(io.StringIO(r.text), dtype=str); sb["t"] = pd.to_datetime(sb["valid"]); sb = sb.set_index("t").sort_index()
wx = sb["wxcodes"].fillna("") + " " + sb["metar"].fillna("").str.extract(r"(RE\w+)", expand=False).fillna("")
sb["ev"] = wx.str.contains(r"RA|DZ|TS|SH", regex=True)
lin = []; casos = []
for t0, s in sig.items():
    agora = sb.loc[t0 - pd.Timedelta(minutes=30):t0, "ev"].any(); depois = sb.loc[t0 + pd.Timedelta(minutes=1):t0 + pd.Timedelta(minutes=70), "ev"]
    if len(depois) == 0: continue
    lin.append({"t": t0, "sinal": s is not None, "evento": bool(depois.any()) and not agora, "chovendo": bool(agora)})
    if s is not None: casos.append({"t": str(t0), **s, "metar_agora": " ".join(sb.loc[t0 - pd.Timedelta(minutes=30):t0, "wxcodes"].dropna()), "metar_depois": " ".join(sb.loc[t0:t0 + pd.Timedelta(minutes=70), "wxcodes"].dropna())})
D = pd.DataFrame(lin); D = D[~D.chovendo]
a_, b_, c_ = int((D.sinal & D.evento).sum()), int((D.sinal & ~D.evento).sum()), int((~D.sinal & D.evento).sum())
R["teste"] = {"frames_sem_chuva_no_aeroporto": len(D), "com_sinal": int(D.sinal.sum()), "eventos_na_hora_seguinte": int(D.evento.sum()),
              "acertos": a_, "alarmes": b_, "perdidos": c_, "POD": round(a_ / max(1, a_ + c_), 2), "FAR": round(b_ / max(1, a_ + b_), 2),
              "taxa_evento_com_sinal": round(a_ / max(1, a_ + b_), 2), "taxa_evento_sem_sinal": round(c_ / max(1, len(D) - a_ - b_), 3)}
R["casos"] = casos[:80]
R["variantes"] = {}
for (vn, raio), sg in GR.items():
    L2 = []
    for t0, s_ in sg.items():
        ag = sb.loc[t0 - pd.Timedelta(minutes=30):t0, "ev"].any(); dp = sb.loc[t0 + pd.Timedelta(minutes=1):t0 + pd.Timedelta(minutes=70), "ev"]
        if len(dp) == 0 or ag: continue
        L2.append((s_ is not None, bool(dp.any())))
    X = pd.DataFrame(L2, columns=["s", "e"]); a_, b_, c_ = int((X.s & X.e).sum()), int((X.s & ~X.e).sum()), int((~X.s & X.e).sum()); n_ = len(X)
    cs, ss = (a_ / (a_ + b_)) if a_ + b_ else None, (c_ / max(1, n_ - a_ - b_))
    R["variantes"][f"{vn}_{raio}km"] = {"frames": n_, "com_sinal": a_ + b_, "chuva_depois_com_sinal": round(cs, 3) if cs is not None else None, "chuva_depois_sem_sinal": round(ss, 3),
                                       "lift": round(cs / ss, 2) if cs is not None and ss else None, "POD": round(a_ / max(1, a_ + c_), 2)}
# linha do tempo dos dias que você relatou
for dia, h1, h2 in (("2026-11-16", 13, 19), ("2026-11-19", 13, 19), ("2026-11-20", 18, 23)):
    R[f"linha_{dia}"] = [[str(t0)[11:16], (s or {}).get("km"), (s or {}).get("tmin"), (s or {}).get("esfriou"), " ".join(sb.loc[t0 - pd.Timedelta(minutes=9):t0, "wxcodes"].dropna())]
                        for t0, s in sorted(sig.items()) if str(t0.date()) == dia and h1 <= t0.hour <= h2]
salva(); print(json.dumps(R["teste"]), flush=True)
