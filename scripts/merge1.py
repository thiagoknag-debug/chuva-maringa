"""Sonda o MERGE (CPTEC/INPE) com prazos curtos e salvando cada etapa."""
import sys, subprocess, re, json, time, socket, ftplib, datetime as dt, requests
UA = {"User-Agent": "Mozilla/5.0 (chuva-maringa-auditoria)"}; R = {}; LAT, LON = -23.42, -51.94; H = "ftp.cptec.inpe.br"
def salva(): json.dump(R, open("lab/merge1.json", "w"), ensure_ascii=False, indent=1)
def passo(nome, f):
    t = time.time()
    try: R[nome] = f()
    except Exception as e: R[nome] = {"erro": f"{type(e).__name__}: {str(e)[:200]}"}
    if isinstance(R[nome], dict): R[nome]["seg"] = round(time.time() - t, 1)
    print(nome, json.dumps(R[nome], ensure_ascii=False)[:900], flush=True); salva()
def get(u, maxs=60):
    t0 = time.time(); r = requests.get(u, headers=UA, timeout=(15, 30), stream=True); buf = b""
    for ch in r.iter_content(65536):
        buf += ch
        if time.time() - t0 > maxs: raise TimeoutError(f"lento: {len(buf)} bytes em {maxs}s")
    return r.status_code, buf
def hrefs(b): return [h for h in re.findall(r'href="([^"?#][^"]*)"', b.decode("latin-1")) if not h.startswith(("/", "http", "..")) and h != "./"]
passo("dns", lambda: {"ips": sorted({a[4][0] for a in socket.getaddrinfo(H, None)})})
def tcp(p):
    t = time.time(); s = socket.create_connection((H, p), timeout=10); s.close(); return {"ok": True, "ms": int((time.time() - t) * 1000)}
for p in (80, 443, 21): passo(f"tcp_{p}", lambda p=p: tcp(p))
for u in (f"http://{H}/", f"https://{H}/", f"http://{H}/modelos/tempo/MERGE/GPM/DAILY/"):
    passo("http " + u, lambda u=u: (lambda s, b: {"status": s, "bytes": len(b), "itens": hrefs(b)[-15:]})(*get(u, 45)))
def ftp():
    f = ftplib.FTP(H, timeout=25); f.login(); out = {"boas_vindas": f.getwelcome()[:120]}
    for d in ("/modelos/tempo/MERGE/GPM/DAILY", "/modelos/tempo/MERGE/GPM/DAILY/2026/11"):
        try: out[d] = sorted(f.nlst(d))[-8:]
        except Exception as e: out[d] = str(e)[:120]
    f.quit(); return out
passo("ftp", ftp)
# arquivos diretos (sem listar): últimos dias e dias conhecidos
hoje = dt.date.today(); dias = [hoje - dt.timedelta(days=k) for k in range(1, 5)] + [dt.date(2026, 11, 19), dt.date(2026, 11, 2)]
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pygrib", "numpy"], check=False)
def le(d):
    u = f"http://{H}/modelos/tempo/MERGE/GPM/DAILY/{d:%Y/%m}/MERGE_CPTEC_{d:%Y%m%d}.grib2"
    s, b = get(u, 90)
    if s != 200: return {"status": s}
    import pygrib, numpy as np
    open("/tmp/m.grib2", "wb").write(b); m = pygrib.open("/tmp/m.grib2").message(1); la, lo = m.latlons(); v = m.values
    lo = np.where(lo > 180, lo - 360, lo); i, j = np.unravel_index(np.argmin((la - LAT) ** 2 + (lo - LON) ** 2), la.shape)
    viz = np.asarray(v[i - 1:i + 2, j - 1:j + 2], dtype=float)
    return {"bytes": len(b), "nome": m.name, "un": m.units, "dataDate": m.dataDate, "dataTime": m.dataTime, "stepRange": getattr(m, "stepRange", None),
            "grade": [float(la.min()), float(la.max()), float(lo.min()), float(lo.max()), list(la.shape)], "ponto": [round(float(la[i, j]), 3), round(float(lo[i, j]), 3)],
            "mm": round(float(v[i, j]), 2), "mm_3x3": round(float(np.nanmean(viz)), 2), "max_3x3": round(float(np.nanmax(viz)), 2)}
for d in dias: passo(f"arquivo {d}", lambda d=d: le(d))
