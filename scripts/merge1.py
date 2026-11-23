"""Sonda o MERGE (CPTEC/INPE): onde estão os arquivos, formato, data mais recente e o valor no ponto de Maringá."""
import sys, subprocess, re, json, datetime as dt, requests
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pygrib", "numpy"], check=False)
UA = {"User-Agent": "chuva-maringa-auditoria"}; R = {}; LAT, LON = -23.42, -51.94
def lista(u):
    r = requests.get(u, headers=UA, timeout=90)
    hs = [h for h in re.findall(r'href="([^"?#][^"]*)"', r.text) if not h.startswith(("/", "http", "..")) and h != "./"]
    return r.status_code, hs
def tenta(u):
    try: s, h = lista(u); R[u] = {"status": s, "n": len(h), "itens": h[:6] + ["…"] + h[-12:] if len(h) > 18 else h}
    except Exception as e: R[u] = {"erro": str(e)[:200]}
    print(u, json.dumps(R[u], ensure_ascii=False)[:900], flush=True); return R[u]
B = "http://ftp.cptec.inpe.br/modelos/tempo/MERGE/"
for u in (B, B + "GPM/", B + "GPM/DAILY/", B + "GPM/HOURLY/", "https://ftp.cptec.inpe.br/modelos/tempo/MERGE/GPM/DAILY/"): tenta(u)
# navega até o arquivo diário mais recente
def ultimo(u):
    s, h = lista(u); return sorted(h)[-1] if h else None
D = B + "GPM/DAILY/"; arqs = []
try:
    ano = ultimo(D); mes = ultimo(D + ano); s, fs = lista(D + ano + mes)
    fs = sorted(f for f in fs if "MERGE" in f.upper()); R["diario_mais_recente"] = {"pasta": ano + mes, "ultimos": fs[-6:]}
    print("diário:", R["diario_mais_recente"], flush=True)
    gr = [f for f in fs if f.endswith((".grib2", ".grb2", ".grib"))]; arqs = [(D + ano + mes + gr[-1])] if gr else []
    # dias conhecidos: 19/11 (chuva forte que os modelos não viram) e 02/11 (tornado)
    for d in ("20261119", "20261120", "20261102", "20261103"):
        nm = [f for f in fs if d in f and f.endswith((".grib2", ".grb2", ".grib"))]
        if nm: arqs.append(D + ano + mes + nm[0])
except Exception as e: R["navegacao_erro"] = str(e)[:300]; print("erro navegação", e, flush=True)
try:
    import pygrib, numpy as np
    for u in arqs:
        r = requests.get(u, headers=UA, timeout=180); open("/tmp/m.grib2", "wb").write(r.content)
        g = pygrib.open("/tmp/m.grib2"); info = {"bytes": len(r.content), "msgs": []}
        for m in g:
            la, lo = m.latlons(); v = m.values
            if lo.max() > 180: lo = np.where(lo > 180, lo - 360, lo)
            i, j = np.unravel_index(np.argmin((la - LAT) ** 2 + (lo - LON) ** 2), la.shape)
            viz = np.asarray(v[max(0, i - 1):i + 2, max(0, j - 1):j + 2], dtype=float)
            info["msgs"].append({"nome": m.name, "un": m.units, "dataDate": m.dataDate, "dataTime": m.dataTime,
                                 "validityDate": getattr(m, "validityDate", None), "validityTime": getattr(m, "validityTime", None),
                                 "stepRange": getattr(m, "stepRange", None), "grade": [round(float(la.min()), 2), round(float(la.max()), 2), round(float(lo.min()), 2), round(float(lo.max()), 2), list(la.shape)],
                                 "ponto": [round(float(la[i, j]), 3), round(float(lo[i, j]), 3)], "mm_ponto": round(float(v[i, j]), 2), "mm_3x3": round(float(np.nanmean(viz)), 2), "mm_max_3x3": round(float(np.nanmax(viz)), 2)})
        R[u.split("/")[-1]] = info; print(u.split("/")[-1], json.dumps(info, ensure_ascii=False)[:1000], flush=True)
except Exception as e: R["grib_erro"] = str(e)[:300]; print("erro grib", e, flush=True)
json.dump(R, open("lab/merge1.json", "w"), ensure_ascii=False, indent=1)
