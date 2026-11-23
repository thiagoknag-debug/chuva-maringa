import json, re, requests
UA = {"User-Agent": "Mozilla/5.0 (chuva-maringa-auditoria)"}; P = "G19-ABI-FD-BAND13"; R = {}
t = requests.get(f"https://realearth.ssec.wisc.edu/api/times?products={P}", headers=UA, timeout=60).json()[P]; t1, t0 = t[-1], t[-30]
base = "https://realearth.ssec.wisc.edu/api/probe?lat=-23.42&lon=-51.94&products="
for nome, u in (("ultimo", base + P), ("sufixo_t1", base + f"{P}_{t1.replace('.', '_')}"), ("sufixo_t0", base + f"{P}_{t0.replace('.', '_')}"),
                ("time_t0", base + P + f"&time={t0}"), ("time_t0_", base + P + f"&time={t0.replace('.', '_')}"), ("timestamp", base + f"{P}&timestamp={t0}")):
    x = requests.get(u, headers=UA, timeout=30).text
    corpo = re.sub(r"<[^>]+>", " ", x); corpo = re.sub(r"\s+", " ", corpo)
    R[nome] = {"url": u, "texto": corpo[-300:]}; print(nome, R[nome], flush=True)
json.dump(R, open("lab/sat4.json", "w"), ensure_ascii=False, indent=1)
