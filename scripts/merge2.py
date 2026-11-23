"""MERGE (CPTEC/INPE) em Maringá: baixa a série diária (com cache), descobre a janela de acumulação e compara com
pluviômetro do INMET (A835), aeroporto (METAR SBMG) e ERA5 (a "chuva real" usada na auditoria de outubro)."""
import sys, subprocess, io, os, json, time, zipfile, datetime as dt, requests, numpy as np, pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pygrib"], check=False)
import pygrib
UA = {"User-Agent": "Mozilla/5.0 (chuva-maringa-auditoria)"}; LAT, LON = -23.42, -51.94
INI, FIM = dt.date(2024, 9, 1), dt.date.today() - dt.timedelta(days=1)
CACHE = "lab/cache/merge_maringa.csv"; os.makedirs("lab/cache", exist_ok=True); OUT = {}
def salva(): json.dump(OUT, open("lab/merge2.json", "w"), ensure_ascii=False, indent=1, default=str)
# ---------- MERGE ----------
IJ = {}
def baixa(d):
    u = f"http://ftp.cptec.inpe.br/modelos/tempo/MERGE/GPM/DAILY/{d:%Y/%m}/MERGE_CPTEC_{d:%Y%m%d}.grib2"
    for k in range(4):
        try:
            r = requests.get(u, headers=UA, timeout=(15, 60))
            if r.status_code == 404: return d, None
            if r.status_code == 200 and len(r.content) > 10000: return d, r.content
        except Exception: pass
        time.sleep(3 * (k + 1))
    return d, None
def extrai(b):
    fn = f"/tmp/m_{os.getpid()}.grib2"; open(fn, "wb").write(b); m = pygrib.open(fn).message(1); v = np.asarray(m.values, dtype=float)
    if not IJ:
        la, lo = m.latlons(); lo = np.where(lo > 180, lo - 360, lo); i, j = np.unravel_index(np.argmin((la - LAT) ** 2 + (lo - LON) ** 2), la.shape)
        IJ.update(i=i, j=j, ponto=(float(la[i, j]), float(lo[i, j])))
    i, j = IJ["i"], IJ["j"]; v3 = v[i - 1:i + 2, j - 1:j + 2]; v5 = v[i - 2:i + 3, j - 2:j + 3]
    return {"mm": v[i, j], "mm3": np.nanmean(v3), "max3": np.nanmax(v3), "mm5": np.nanmean(v5)}
old = pd.read_csv(CACHE, index_col=0, parse_dates=True) if os.path.exists(CACHE) else pd.DataFrame()
dias = [INI + dt.timedelta(days=k) for k in range((FIM - INI).days + 1)]
falta = [d for d in dias if old.empty or pd.Timestamp(d) not in old.index or d > FIM - dt.timedelta(days=10)]
print("MERGE: baixando", len(falta), "dias", flush=True); t0 = time.time(); novos = {}; sem = []
with ThreadPoolExecutor(8) as ex:
    for f in as_completed([ex.submit(baixa, d) for d in falta]):
        d, b = f.result()
        if b is None: sem.append(str(d)); continue
        try: novos[pd.Timestamp(d)] = extrai(b)
        except Exception as e: sem.append(f"{d} {e}")
        if len(novos) % 100 == 0: print(" ", len(novos), "dias", round(time.time() - t0), "s", flush=True)
mg = pd.concat([old[~old.index.isin(list(novos))], pd.DataFrame(novos).T]).sort_index().astype(float) if novos else old
mg.to_csv(CACHE, float_format="%.2f"); OUT["merge"] = {"dias": len(mg), "de": mg.index.min(), "ate": mg.index.max(), "sem_arquivo": sem[:20], "n_sem": len(sem),
                                                      "ponto_da_grade": IJ.get("ponto"), "seg": round(time.time() - t0)}
print(OUT["merge"], flush=True); salva()
# ---------- INMET A835 (horário, UTC) ----------
def inmet(ano):
    try:
        r = requests.get(f"https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip", headers=UA, timeout=600)
        z = zipfile.ZipFile(io.BytesIO(r.content)); nm = [x for x in z.namelist() if "A835" in x.upper()]
        L = z.read(nm[0]).decode("latin-1").splitlines(); h = next(i for i, l in enumerate(L) if l.upper().startswith("DATA") and "HORA" in l.upper())
        df = pd.read_csv(io.StringIO("\n".join(L[h:])), sep=";", decimal=",", dtype=str); cp = [c for c in df.columns if "PRECIPITA" in c.upper()][0]
        v = pd.to_numeric(df[cp].astype(str).str.replace(",", ".").str.strip(), errors="coerce"); v = v.where(v > -9000)
        t = pd.to_datetime(df[df.columns[0]].str.replace("/", "-").str.strip() + " " + df[df.columns[1]].str.extract(r"(\d{2})")[0] + ":00", errors="coerce")
        return pd.Series(v.values, index=t).dropna()
    except Exception as e: print("inmet", ano, e, flush=True); return None
iv = pd.concat([s for s in (inmet(a) for a in (2024, 2025, 2026)) if s is not None]).sort_index(); iv = iv[~iv.index.duplicated()]
print("INMET horas válidas", len(iv), flush=True)
# ---------- METAR SBMG (UTC) ----------
sb = []
a = pd.Timestamp(INI) - pd.Timedelta(days=1)
while a <= pd.Timestamp(FIM) + pd.Timedelta(days=1):
    b = min(a + pd.offsets.MonthEnd(0), pd.Timestamp(FIM) + pd.Timedelta(days=1))
    for k in range(5):
        try:
            r = requests.get("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py", timeout=180, headers=UA,
                params={"station": "SBMG", "data": ["wxcodes"], "year1": a.year, "month1": a.month, "day1": a.day, "year2": b.year, "month2": b.month, "day2": b.day,
                        "tz": "Etc/UTC", "format": "onlycomma", "missing": "empty", "report_type": [3, 4]})
            if r.status_code == 200: sb.append(pd.read_csv(io.StringIO(r.text), dtype=str)); break
        except Exception as e: print("sbmg", e, flush=True)
        time.sleep(15 * (k + 1))
    a = b + pd.Timedelta(days=1); time.sleep(4)
sb = pd.concat(sb, ignore_index=True); sb["t"] = pd.to_datetime(sb["valid"], errors="coerce"); sb = sb.dropna(subset=["t"]).drop_duplicates("t").set_index("t").sort_index()
wx = sb["wxcodes"].fillna("").astype(str); sb["chuva"] = wx.str.contains(r"(^|\s)[-+]?(TS|SH)?(RA|DZ)", regex=True); sb["forte"] = wx.str.contains(r"(^|\s)\+(TS|SH)?RA|TSRA", regex=True)
print("METAR boletins", len(sb), flush=True)
# ---------- ERA5 (Open-Meteo, horário UTC) ----------
try:
    r = requests.get("https://archive-api.open-meteo.com/v1/archive", timeout=300, params={"latitude": LAT, "longitude": LON, "start_date": str(INI - dt.timedelta(days=1)),
        "end_date": str(FIM), "hourly": "precipitation", "timezone": "UTC", "models": "era5"}).json()
    era = pd.Series(r["hourly"]["precipitation"], index=pd.to_datetime(r["hourly"]["time"]), dtype=float)
except Exception as e: print("era5", e, flush=True); era = pd.Series(dtype=float)
# ---------- janelas ----------
def janela(s, d, tipo, how):
    # valores horários rotulados pelo FIM da hora: a janela 12Z->12Z vai do rótulo 13Z ao 12Z (inclusive)
    ini = {"A": d - pd.Timedelta(hours=11), "B": d + pd.Timedelta(hours=13), "C": d + pd.Timedelta(hours=1)}[tipo]; q = s.loc[ini:ini + pd.Timedelta(hours=23)]
    return how(q)
def serie(s, tipo, how): return pd.Series({d: janela(s, d, tipo, how) for d in mg.index})
res_j = {}
for tipo in "ABC":
    im = serie(iv, tipo, lambda q: q.sum() if q.count() >= 23 else np.nan); ok = im.notna() & mg.mm.notna()
    res_j[tipo] = {"n": int(ok.sum()), "r_pearson": round(float(np.corrcoef(mg.mm[ok], im[ok])[0, 1]), 3) if ok.sum() > 10 else None}
OUT["janela"] = {"A=12Z dia anterior->12Z dia": res_j["A"], "B=12Z dia->12Z dia seguinte": res_j["B"], "C=00Z->24Z do dia": res_j["C"]}
best = max("ABC", key=lambda t: res_j[t]["r_pearson"] or -1); OUT["janela_escolhida"] = best; print(OUT["janela"], "->", best, flush=True); salva()
im = serie(iv, best, lambda q: q.sum() if q.count() >= 23 else np.nan)
mt = serie(sb["chuva"], best, lambda q: (q.any() if len(q) >= 20 else np.nan)); mtn = serie(sb["chuva"], best, lambda q: q.sum() if len(q) >= 20 else np.nan)
e5 = serie(era, best, lambda q: q.sum() if q.count() >= 23 else np.nan)
T = pd.DataFrame({"merge": mg.mm, "merge3": mg.mm3, "max3": mg.max3, "inmet": im, "metar": mt, "metar_horas": mtn, "era5": e5}); T.to_csv("lab/merge_comparacao.csv", float_format="%.2f")
# ---------- notas ----------
def ge(s, x): return (s >= x).where(s.notna())
def cont(prev, obs):
    ok = prev.notna() & obs.notna(); p, o = prev[ok].astype(bool), obs[ok].astype(bool); a, b, c, d = (p & o).sum(), (p & ~o).sum(), (~p & o).sum(), (~p & ~o).sum()
    n = a + b + c + d; e = ((a + b) * (a + c) + (c + d) * (b + d)) / n if n else 0
    return {"n": int(n), "acerto": round((a + d) / n, 3) if n else None, "detecta_chuva(POD)": round(a / (a + c), 3) if a + c else None,
            "alarme_falso(FAR)": round(b / (a + b), 3) if a + b else None, "CSI": round(a / (a + b + c), 3) if a + b + c else None, "HSS": round((a + d - e) / (n - e), 3) if n - e else None}
def quant(x, y):
    ok = x.notna() & y.notna(); x, y = x[ok], y[ok]
    return {"n": int(ok.sum()), "total_prev": round(float(x.sum()), 1), "total_obs": round(float(y.sum()), 1), "vies_%": round(100 * (x.sum() / y.sum() - 1), 1) if y.sum() else None,
            "r": round(float(np.corrcoef(x, y)[0, 1]), 3), "erro_medio_mm": round(float((x - y).abs().mean()), 2)}
OUT["vs_inmet"] = {k: {"quantidade": quant(T[k], T.inmet), ">=1mm": cont(ge(T[k], 1), ge(T.inmet, 1)), ">=10mm": cont(ge(T[k], 10), ge(T.inmet, 10)), ">=25mm": cont(ge(T[k], 25), ge(T.inmet, 25))}
                  for k in ("merge", "merge3", "era5")}
sem_inmet = T.inmet.isna()
OUT["vs_aeroporto"] = {k: {"todos_dias": {"limiar_0.2": cont(ge(T[k], 0.2), T.metar), "limiar_1": cont(ge(T[k], 1), T.metar)},
                           "dias_sem_pluviometro_INMET": {"limiar_1": cont(ge(T[k], 1)[sem_inmet], T.metar[sem_inmet])},
                           "dias_com_pluviometro_INMET": {"limiar_1": cont(ge(T[k], 1)[~sem_inmet], T.metar[~sem_inmet])},
                           "chuva_longa(>=3_boletins)": cont(ge(T[k], 1), ge(T.metar_horas, 3))} for k in ("merge", "merge3", "era5")}
OUT["vs_aeroporto"]["inmet"] = {"todos_dias": {"limiar_1": cont(ge(T.inmet, 1), T.metar)}}
OUT["dias_conhecidos"] = {str(d.date()): {k: (None if pd.isna(T.loc[d, k]) else round(float(T.loc[d, k]), 1)) for k in T.columns} for d in pd.to_datetime(["2026-11-02", "2026-11-03", "2026-11-16", "2026-11-17", "2026-11-19", "2026-11-20", "2026-11-21", "2026-11-22"]) if d in T.index}
salva(); print(json.dumps(OUT, ensure_ascii=False, default=str)[:6000])
