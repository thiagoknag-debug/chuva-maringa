"""MERGE (CPTEC/INPE): chuva diária em grade de 0,1° (satélite + pluviômetros), acumulada das 12Z do dia anterior
às 12Z do dia do arquivo (09h->09h em Maringá). Mantém uma série do ponto de Maringá em lab/cache/merge_maringa.csv."""
import os, time, datetime as dt, requests, numpy as np, pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
UA = {"User-Agent": "Mozilla/5.0 (chuva-maringa-auditoria)"}
CACHE = "lab/cache/merge_maringa.csv"
URL = "http://ftp.cptec.inpe.br/modelos/tempo/MERGE/GPM/DAILY/{d:%Y/%m}/MERGE_CPTEC_{d:%Y%m%d}.grib2"
def _baixa(d):
    for k in range(4):
        try:
            r = requests.get(URL.format(d=d), headers=UA, timeout=(15, 60))
            if r.status_code == 404: return d, None
            if r.status_code == 200 and len(r.content) > 10000: return d, r.content
        except Exception: pass
        time.sleep(3 * (k + 1))
    return d, None
def serie(ini, fim, lat=-23.42, lon=-51.94, cache=CACHE, refaz=10, log=print):
    import pygrib
    old = pd.read_csv(cache, index_col=0, parse_dates=True) if os.path.exists(cache) else pd.DataFrame()
    dias = [ini + dt.timedelta(days=k) for k in range((fim - ini).days + 1)]
    falta = [d for d in dias if old.empty or pd.Timestamp(d) not in old.index or d > fim - dt.timedelta(days=refaz)]
    IJ, novos, fn = {}, {}, f"/tmp/merge_{os.getpid()}.grib2"
    with ThreadPoolExecutor(8) as ex:
        for f in as_completed([ex.submit(_baixa, d) for d in falta]):
            d, b = f.result()
            if b is None: continue
            try:
                open(fn, "wb").write(b); m = pygrib.open(fn).message(1); v = np.asarray(m.values, dtype=float)
                if not IJ:
                    la, lo = m.latlons(); lo = np.where(lo > 180, lo - 360, lo)
                    i, j = np.unravel_index(np.argmin((la - lat) ** 2 + (lo - lon) ** 2), la.shape); IJ.update(i=i, j=j)
                i, j = IJ["i"], IJ["j"]; v3 = v[i - 1:i + 2, j - 1:j + 2]
                novos[pd.Timestamp(d)] = {"mm": v[i, j], "mm3": np.nanmean(v3), "max3": np.nanmax(v3), "mm5": np.nanmean(v[i - 2:i + 3, j - 2:j + 3])}
            except Exception as e: log("MERGE erro", d, str(e)[:100])
    mg = pd.concat([old[~old.index.isin(list(novos))], pd.DataFrame(novos).T]).sort_index().astype(float) if novos else old
    os.makedirs(os.path.dirname(cache), exist_ok=True); mg.to_csv(cache, float_format="%.2f")
    log("MERGE: baixados", len(novos), "de", len(falta), "· série com", len(mg), "dias até", mg.index.max())
    return mg
