"""Sonda fontes novas: pluviômetros Cemaden e raios (GLM/GIBS). Grava lab/sondagem_fontes.json"""
import json, re, requests
H = {"User-Agent": "Mozilla/5.0 (chuva-maringa)", "Origin": "https://thiagoknag-debug.github.io"}
out = {}
def tenta(k, u, n=1500, **kw):
    try:
        r = requests.get(u, headers=H, timeout=40, **kw)
        out[k] = {"status": r.status_code, "acao": r.headers.get("Access-Control-Allow-Origin"), "ctype": r.headers.get("Content-Type"), "len": len(r.content), "amostra": r.text[:n]}
        return r
    except Exception as e: out[k] = repr(e)
tenta("cemaden_getjson2_pr", "http://sjc.salvar.cemaden.gov.br/resources/graficos/interativo/getJson2.php?uf=PR", 3000)
tenta("cemaden_getjson2_pr_https", "https://sjc.salvar.cemaden.gov.br/resources/graficos/interativo/getJson2.php?uf=PR", 1500)
tenta("cemaden_resources", "https://resources.cemaden.gov.br/graficos/interativo/getJson2.php?uf=PR", 1500)
tenta("cemaden_mapainterativo", "https://mapainterativo.cemaden.gov.br/MapaInterativoWS/resources/horario/3/24", 1500)
tenta("cemaden_ws_estacoes", "https://mapservices.cemaden.gov.br/MapaInterativoWS/resources/horario/3/24", 1500)
r = tenta("sgb_cemaden_layers", "https://geoportal.sgb.gov.br/server/rest/services/Cemaden/MapServer/layers?f=json", 4000)
tenta("sgb_cemaden_q", "https://geoportal.sgb.gov.br/server/rest/services/Cemaden/MapServer/0/query?where=1%3D1&geometry=-52.1,-23.6,-51.8,-23.3&geometryType=esriGeometryEnvelope&inSR=4326&outFields=*&f=json&resultRecordCount=5", 4000)
g = tenta("gibs_caps", "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml", 100)
try:
    txt = requests.get("https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/1.0.0/WMTSCapabilities.xml", timeout=60).text
    out["gibs_glm"] = sorted(set(re.findall(r"<ows:Identifier>([^<]*(?:GLM|Lightning|lightning|Flash)[^<]*)</ows:Identifier>", txt)))[:40]
except Exception as e: out["gibs_glm"] = repr(e)
tenta("aws_goes19_glm", "https://noaa-goes19.s3.amazonaws.com/?list-type=2&prefix=GLM-L2-LCFA/2026/318/&max-keys=3", 1200)
json.dump(out, open("lab/sondagem_fontes.json", "w"), ensure_ascii=False, indent=1)
for k, v in out.items(): print(k, v if isinstance(v, (str, list)) else (v["status"], v["acao"], v["ctype"], v["len"], v["amostra"][:300].replace("\n", " ")))
