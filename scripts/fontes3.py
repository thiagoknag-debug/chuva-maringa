"""Sonda 3: cidades com pluviômetro Cemaden no PR e produtos de raios no RealEarth. Grava lab/sondagem_fontes3.json"""
import json, requests
H = {"User-Agent": "Mozilla/5.0 (chuva-maringa)", "Origin": "https://thiagoknag-debug.github.io"}
out = {}
j = requests.get("https://resources.cemaden.gov.br/graficos/interativo/getJson2.php?uf=PR", headers=H, timeout=60).json()
cid = {}
for x in j: cid.setdefault(x["cidade"], []).append((x["nomeestacao"], x["tipoestacao"], x["status"], x["datahoraUltimovalor"], x["acc24hr"]))
out["cidades"] = {k: len(v) for k, v in sorted(cid.items())}
viz = ["MARINGA", "MARINGÁ", "SARANDI", "PAICANDU", "PAIÇANDU", "MARIALVA", "MANDAGUARI", "ASTORGA", "FLORESTA", "IGUARACU", "IGUARAÇU", "MANDAGUACU", "MANDAGUAÇU", "APUCARANA", "ARAPONGAS", "CIANORTE", "LONDRINA", "PARANAVAI", "PARANAVAÍ", "CAMPO MOURAO", "CAMPO MOURÃO"]
out["vizinhas"] = {k: v for k, v in cid.items() if k.upper() in viz}
p = requests.get("https://realearth.ssec.wisc.edu/api/products", headers=H, timeout=90).json()
out["realearth_glm"] = [{k: x.get(k) for k in ("id", "name", "categories", "maxzoom", "projection", "displaytype", "times")} for x in p if any(s in (x.get("id", "") + x.get("name", "")).upper() for s in ("GLM", "LIGHTN", "FLASH"))][:30]
r = requests.get("https://realearth.ssec.wisc.edu/api/times?products=G19-GLM-FED", headers=H, timeout=40)
out["re_times_g19fed"] = [r.status_code, r.headers.get("Access-Control-Allow-Origin"), r.text[:400]]
json.dump(out, open("lab/sondagem_fontes3.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False)[:4000])
