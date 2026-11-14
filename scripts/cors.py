"""Testa se endpoints de METAR aceitam CORS (leitura direta pelo navegador). Grava lab/sondagem_cors.json"""
import json, requests
H = {"User-Agent": "Mozilla/5.0", "Origin": "https://thiagoknag-debug.github.io"}
U = {"awc_json": "https://aviationweather.gov/api/data/metar?ids=SBMG&format=json&hours=3",
     "iem_currents": "https://mesonet.agron.iastate.edu/api/1/currents.json?station=SBMG",
     "iem_currents_net": "https://mesonet.agron.iastate.edu/api/1/currents.json?network=BR__ASOS",
     "iem_asos": "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=SBMG&data=sknt,drct,gust,tmpf,dwpf,metar&tz=UTC&format=onlycomma&hours=3",
     "iem_obhistory": "https://mesonet.agron.iastate.edu/api/1/obhistory.json?station=SBMG&network=BR__ASOS"}
out = {}
for k, u in U.items():
    try:
        r = requests.get(u, headers=H, timeout=40)
        out[k] = {"status": r.status_code, "acao": r.headers.get("Access-Control-Allow-Origin"), "ctype": r.headers.get("Content-Type"), "amostra": r.text[:700]}
    except Exception as e: out[k] = repr(e)
json.dump(out, open("lab/sondagem_cors.json", "w"), indent=1, ensure_ascii=False); print(json.dumps(out, indent=1)[:5000])
