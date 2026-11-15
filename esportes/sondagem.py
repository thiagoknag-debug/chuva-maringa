"""Sondagem das fontes de agenda esportiva (ESPN + TheSportsDB). Grava esportes/lab/sondagem.json"""
import json, requests, datetime as dt
H = {"User-Agent": "Mozilla/5.0", "Origin": "https://thiagoknag-debug.github.io"}
hoje = dt.date.today(); fim = hoje + dt.timedelta(days=7)
R = f"{hoje:%Y%m%d}-{fim:%Y%m%d}"
B = "https://site.api.espn.com/apis/site/v2/sports/"
L = ["soccer/bra.1","soccer/bra.2","soccer/bra.copa_do_brasil","soccer/conmebol.libertadores","soccer/conmebol.sudamericana",
     "soccer/uefa.champions","soccer/uefa.europa","soccer/uefa.nations","soccer/fifa.friendly","soccer/fifa.worldq.conmebol",
     "soccer/eng.1","soccer/esp.1","soccer/ita.1","soccer/ger.1","soccer/fra.1","soccer/usa.1","soccer/arg.1","soccer/por.1",
     "racing/f1","racing/irl","racing/nascar-premier","basketball/nba","football/nfl","football/college-football",
     "tennis/atp","tennis/wta","mma/ufc","hockey/nhl","golf/pga","baseball/mlb","volleyball/womens-college-volleyball","rugby/scoreboard"]
out = {"range": R}
def trim(o, d=0):
    if d > 5: return "…"
    if isinstance(o, dict): return {k: trim(v, d+1) for k, v in list(o.items())[:25]}
    if isinstance(o, list): return [trim(v, d+1) for v in o[:2]]
    if isinstance(o, str): return o[:120]
    return o
for l in L:
    u = B + l + "/scoreboard?limit=300&dates=" + R
    try:
        r = requests.get(u, headers=H, timeout=40); j = r.json() if r.ok else {}
        ev = j.get("events", [])
        out[l] = {"status": r.status_code, "acao": r.headers.get("Access-Control-Allow-Origin"), "n": len(ev),
                  "nomes": [(e.get("date"), e.get("name"), e.get("status",{}).get("type",{}).get("name")) for e in ev[:6]]}
        if l in ("soccer/bra.1","racing/f1","tennis/atp","mma/ufc","basketball/nba","soccer/conmebol.libertadores"):
            out[l]["amostra"] = trim(ev[0]) if ev else trim(j)
            if l == "soccer/bra.1" and ev:
                s = requests.get(B + l + "/summary?event=" + ev[0]["id"], headers=H, timeout=40)
                out["summary_bra1"] = {"status": s.status_code, "acao": s.headers.get("Access-Control-Allow-Origin"), "keys": list(s.json().keys()) if s.ok else None, "amostra": trim(s.json()) if s.ok else s.text[:300]}
    except Exception as e: out[l] = repr(e)
# TheSportsDB (chave pública de teste "3")
for s in ["Volleyball","Motorsport","Fighting","Basketball"]:
    u = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={hoje:%Y-%m-%d}&s={s}"
    try:
        r = requests.get(u, headers=H, timeout=40); j = r.json() if r.ok else {}
        ev = j.get("events") or []
        out["tsdb_"+s] = {"status": r.status_code, "acao": r.headers.get("Access-Control-Allow-Origin"), "n": len(ev), "nomes": [(e.get("strTimestamp"), e.get("strEvent"), e.get("strLeague")) for e in ev[:8]]}
    except Exception as e: out["tsdb_"+s] = repr(e)
json.dump(out, open("esportes/lab/sondagem.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k:(v if not isinstance(v,dict) else {kk:vv for kk,vv in v.items() if kk!="amostra"}) for k,v in out.items()}, indent=1, ensure_ascii=False)[:6000])
