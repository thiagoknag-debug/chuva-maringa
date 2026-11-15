"""Sonda 2: detalhes Cemaden (Maringá) e raios no RealEarth. Grava lab/sondagem_fontes2.json"""
import json, requests
H = {"User-Agent": "Mozilla/5.0 (chuva-maringa)", "Origin": "https://thiagoknag-debug.github.io"}
out = {}
def tenta(k, u, n=2500):
    try:
        r = requests.get(u, headers=H, timeout=40)
        out[k] = {"status": r.status_code, "acao": r.headers.get("Access-Control-Allow-Origin"), "ctype": r.headers.get("Content-Type"), "len": len(r.content), "amostra": r.text[:n]}
        return r
    except Exception as e: out[k] = repr(e)
r = tenta("getjson2", "https://resources.cemaden.gov.br/graficos/interativo/getJson2.php?uf=PR", 600)
try:
    j = r.json(); out["getjson2_campos"] = list(j[0].keys()); out["getjson2_maringa"] = [x for x in j if "MARING" in str(x.get("cidade", "")).upper()][:30]
    out["getjson2_total"] = len(j)
except Exception as e: out["getjson2_erro"] = repr(e)
tenta("sgb_maringa", "https://geoportal.sgb.gov.br/server/rest/services/Cemaden/MapServer/0/query?where=1%3D1&geometry=-52.1,-23.6,-51.8,-23.3&geometryType=esriGeometryEnvelope&inSR=4326&outFields=*&f=json&returnGeometry=false", 3000)
for k, u in {"ws_estacoes_pr": "https://mapservices.cemaden.gov.br/MapaInterativoWS/resources/estacoes/PR",
             "ws_municipio": "https://mapservices.cemaden.gov.br/MapaInterativoWS/resources/horario/4115200/24",
             "ws_acumulado": "https://mapservices.cemaden.gov.br/MapaInterativoWS/resources/acumulado/PR",
             "ws_root": "https://mapservices.cemaden.gov.br/MapaInterativoWS/resources/application.wadl"}.items(): tenta(k, u, 1500)
tenta("realearth_glm", "https://realearth.ssec.wisc.edu/api/products?search=glm", 3000)
tenta("realearth_lightning", "https://realearth.ssec.wisc.edu/api/products?search=lightning", 3000)
json.dump(out, open("lab/sondagem_fontes2.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False)[:3000])
