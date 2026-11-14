"""Vento agora em Maringá: METAR do aeroporto (SBMG), estação INMET A835 e modelos (hora atual). Grava lab/sondagem_vento.json"""
import json, datetime as dt, requests
UA = {"User-Agent": "chuva-maringa"}
out = {"gerado": dt.datetime.now(dt.timezone.utc).isoformat()}
for nome, url, p in [("metar_awc", "https://aviationweather.gov/api/data/metar", {"ids": "SBMG", "hours": 3, "format": "raw"}),
                     ("metar_awc_json", "https://aviationweather.gov/api/data/metar", {"ids": "SBMG", "hours": 3, "format": "json"})]:
    try: r = requests.get(url, params=p, headers=UA, timeout=30); out[nome] = r.text[:4000] if "json" not in nome else r.json()
    except Exception as e: out[nome + "_erro"] = repr(e)
hoje = dt.datetime.now(dt.timezone.utc).date()
try:
    r = requests.get("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py", params={"station": "SBMG", "data": "metar", "tz": "UTC", "format": "onlycomma",
        "year1": hoje.year, "month1": hoje.month, "day1": hoje.day, "year2": hoje.year, "month2": hoje.month, "day2": hoje.day + 1}, headers=UA, timeout=40)
    out["metar_iem"] = r.text.strip().splitlines()[-6:]
except Exception as e: out["metar_iem_erro"] = repr(e)
for d in (hoje, hoje - dt.timedelta(days=1)):
    try:
        r = requests.get(f"https://apitempo.inmet.gov.br/estacao/{d}/{hoje}/A835", headers=UA, timeout=40)
        out["inmet_status"] = r.status_code
        if r.status_code == 200:
            j = r.json(); out["inmet"] = [{k: x.get(k) for k in ("DT_MEDICAO", "HR_MEDICAO", "VEN_VEL", "VEN_RAJ", "VEN_DIR", "TEM_INS", "CHUVA")} for x in j][-6:]; break
        else: out["inmet_txt"] = r.text[:300]
    except Exception as e: out["inmet_erro"] = repr(e)
try:
    j = requests.get("https://api.open-meteo.com/v1/forecast", params={"latitude": -23.42, "longitude": -51.94, "timezone": "America/Sao_Paulo",
        "current": "wind_speed_10m,wind_direction_10m,wind_gusts_10m,temperature_2m,precipitation", "models": "best_match,ecmwf_ifs,icon_seamless,gfs_seamless,ukmo_seamless"}, headers=UA, timeout=40).json()
    out["modelos_current"] = j.get("current")
except Exception as e: out["modelos_erro"] = repr(e)
try:
    av = requests.get("https://apiprevmet3.inmet.gov.br/avisos/ativos", headers=UA, timeout=40).json()
    out["avisos"] = [[a.get("severidade"), a.get("descricao"), a.get("data_inicio"), a.get("hora_inicio"), a.get("data_fim"), a.get("hora_fim")] for a in av.get("hoje", []) + av.get("futuro", []) if "Maringá - PR" in (a.get("municipios") or "")]
except Exception as e: out["avisos_erro"] = repr(e)
json.dump(out, open("lab/sondagem_vento.json", "w"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(out, ensure_ascii=False, default=str)[:5000])
