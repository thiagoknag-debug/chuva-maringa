"""Baixa a tabela de cores do RainViewer (Universal Blue) -> lab/rv_cores.csv"""
import requests, json
UA = {"User-Agent": "chuva-maringa"}
out = {}
for u in ["https://www.rainviewer.com/files/rainviewer_api_colors_table.csv", "https://rainviewer.com/files/rainviewer_api_colors_table.csv",
          "https://www.rainviewer.com/api/rainviewer_api_colors_table.csv"]:
    try:
        r = requests.get(u, headers=UA, timeout=30); out[u] = [r.status_code, r.headers.get("Content-Type"), r.text[:200]]
        if r.status_code == 200 and "dBZ" in r.text[:300]: open("lab/sondagem_rv_cores.csv", "w").write(r.text); break
    except Exception as e: out[u] = repr(e)
json.dump(out, open("lab/sondagem_rv2.json", "w"), indent=1); print(out)
