"""Procura uma fonte de CHUVA MEDIDA (mm por dia) em Maringá que funcione, já que o pluviômetro automático do INMET (A835) tem falhas longas."""
import json, gzip, io, re, time, requests, datetime as dt
UA = {"User-Agent": "chuva-maringa-auditoria"}; R = {}
fim = dt.date.today(); ini = fim - dt.timedelta(days=45)
def tenta(nome, f):
    try: R[nome] = f()
    except Exception as e: R[nome] = {"erro": str(e)[:200]}
    print(nome, json.dumps(R[nome], ensure_ascii=False)[:600], flush=True)
def ogimet():
    u = f"https://www.ogimet.com/cgi-bin/getsynop?block=83767&begin={ini:%Y%m%d}0000&end={fim:%Y%m%d}2359"
    r = requests.get(u, headers=UA, timeout=60); linhas = [l for l in r.text.splitlines() if l.startswith("83767")]
    chuva = [l for l in linhas if re.search(r" 6\d{3}[0-9/]", l)]
    return {"status": r.status_code, "boletins": len(linhas), "com_grupo_chuva": len(chuva), "exemplo": (chuva or linhas or [r.text[:200]])[-1][:160]}
def meteostat():
    out = {}
    for est in ("83767", "SBMG0", "83766"):
        r = requests.get(f"https://bulk.meteostat.net/v2/daily/{est}.csv.gz", headers=UA, timeout=60)
        if r.status_code != 200: out[est] = r.status_code; continue
        txt = gzip.decompress(r.content).decode(); ls = [l.split(",") for l in txt.splitlines()]
        rec = [l for l in ls if l[0] >= str(ini)]; com = [l for l in rec if len(l) > 4 and l[4] not in ("", None)]
        out[est] = {"dias_recentes": len(rec), "com_chuva_medida": len(com), "ultimos": [(l[0], l[4]) for l in com[-5:]], "ultimo_dia": ls[-1][0] if ls else None}
    return out
def ghcn():
    u = f"https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&stations=BR000083767&startDate={ini}&endDate={fim}&dataTypes=PRCP&format=json&units=metric"
    r = requests.get(u, headers=UA, timeout=90); j = r.json() if r.status_code == 200 else []
    return {"status": r.status_code, "dias": len(j), "ultimos": [(x.get("DATE"), x.get("PRCP")) for x in j[-5:]]}
def inmet_api():
    out = {}
    for u in (f"https://apitempo.inmet.gov.br/estacao/{ini}/{fim}/A835", f"https://apitempo.inmet.gov.br/estacao/diaria/{ini}/{fim}/A835"):
        r = requests.get(u, headers=UA, timeout=60); out[u.split("estacao/")[1][:18]] = {"status": r.status_code, "inicio": r.text[:160]}
    return out
def inmet_zip():
    r = requests.get(f"https://portal.inmet.gov.br/uploads/dadoshistoricos/{fim.year}.zip", headers=UA, timeout=600)
    import zipfile; z = zipfile.ZipFile(io.BytesIO(r.content)); nm = [x for x in z.namelist() if "A835" in x.upper()]
    if not nm: return {"status": r.status_code, "arquivo": "sem A835"}
    t = z.read(nm[0]).decode("latin-1").splitlines(); dados = [l.split(";") for l in t[9:]]
    meses = {}
    for l in dados:
        if len(l) > 2: m = l[0][:7]; v = l[2].replace(",", "."); meses.setdefault(m, [0, 0]); meses[m][0] += 1; meses[m][1] += (v not in ("", "-9999"))
    return {"arquivo": nm[0][-60:], "horas_por_mes_[total,com_chuva_valida]": meses}
tenta("ogimet_synop_83767", ogimet); time.sleep(2)
tenta("meteostat", meteostat); tenta("ghcn_noaa", ghcn); tenta("inmet_api", inmet_api); tenta("inmet_zip_ano", inmet_zip)
json.dump(R, open("lab/fontes6.json", "w"), ensure_ascii=False, indent=1)
