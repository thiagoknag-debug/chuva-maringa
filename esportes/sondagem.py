"""Sondagem 2: formatos de data na ESPN, summary, e fontes de vôlei. Grava esportes/lab/sondagem2.json"""
import json, requests, datetime as dt, os, traceback
H = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)", "Origin": "https://thiagoknag-debug.github.io", "Accept": "application/json"}
hoje = dt.date.today()
B = "https://site.api.espn.com/apis/site/v2/sports/"
out = {}
def trim(o, d=0, w=3):
    if d > 7: return "…"
    if isinstance(o, dict): return {k: trim(v, d+1, w) for k, v in list(o.items())[:30]}
    if isinstance(o, list): return [trim(v, d+1, w) for v in o[:w]]
    if isinstance(o, str): return o[:160]
    return o
def get(k, u, keep=False):
    try:
        r = requests.get(u, headers=H, timeout=40)
        d = {"u": u, "status": r.status_code, "acao": r.headers.get("Access-Control-Allow-Origin")}
        try:
            j = r.json(); ev = j.get("events", []) if isinstance(j, dict) else []
            d["n"] = len(ev); d["nomes"] = [(e.get("date"), e.get("shortName") or e.get("name")) for e in ev[:5]]
            if keep: d["amostra"] = trim(ev[0]) if ev else trim(j)
            if not r.ok: d["erro"] = r.text[:300]
        except Exception: d["texto"] = r.text[:300]
        out[k] = d; return r
    except Exception as e: out[k] = repr(e)
d1 = f"{hoje:%Y%m%d}"; d7 = f"{hoje+dt.timedelta(days=6):%Y%m%d}"
get("bra1_sem", B+"soccer/bra.1/scoreboard")
get("bra1_dia", B+"soccer/bra.1/scoreboard?dates="+d1)
get("bra1_rng7", B+"soccer/bra.1/scoreboard?dates="+d1+"-"+d7)
get("bra1_rng7_lim100", B+"soccer/bra.1/scoreboard?limit=100&dates="+d1+"-"+d7, keep=True)
get("bra1_rng30", B+"soccer/bra.1/scoreboard?limit=100&dates="+d1+"-"+f"{hoje+dt.timedelta(days=30):%Y%m%d}")
get("nba_rng7", B+"basketball/nba/scoreboard?limit=100&dates="+d1+"-"+d7, keep=True)
get("nba_dia", B+"basketball/nba/scoreboard?dates="+d1)
get("nfl_sem", B+"football/nfl/scoreboard", keep=True)
get("lib_rng30", B+"soccer/conmebol.libertadores/scoreboard?limit=100&dates="+d1+"-"+f"{hoje+dt.timedelta(days=30):%Y%m%d}", keep=True)
get("sula_rng30", B+"soccer/conmebol.sudamericana/scoreboard?limit=100&dates="+d1+"-"+f"{hoje+dt.timedelta(days=30):%Y%m%d}")
get("cdb_rng30", B+"soccer/bra.copa_do_brasil/scoreboard?limit=100&dates="+d1+"-"+f"{hoje+dt.timedelta(days=30):%Y%m%d}")
get("friendly", B+"soccer/fifa.friendly/scoreboard?limit=100&dates="+d1+"-"+d7)
get("nations", B+"soccer/uefa.nations/scoreboard?limit=100&dates="+d1+"-"+d7)
get("all_soccer", B+"soccer/all/scoreboard?dates="+d1)
get("f1", B+"racing/f1/scoreboard", keep=True)
get("atp", B+"tennis/atp/scoreboard", keep=True)
get("ufc", B+"mma/ufc/scoreboard", keep=True)
r = get("bra1_sum_base", B+"soccer/bra.1/scoreboard?dates="+d1)
try:
    ev = r.json()["events"]
    if ev:
        s = requests.get(B+"soccer/bra.1/summary?event="+ev[0]["id"], headers=H, timeout=40)
        out["summary"] = {"status": s.status_code, "acao": s.headers.get("Access-Control-Allow-Origin"), "keys": list(s.json().keys()), "amostra": trim({k: s.json()[k] for k in ("gameInfo","broadcasts","odds","standings","headToHeadGames","lastFiveGames","news") if k in s.json()}, w=2)}
except Exception: out["summary_err"] = traceback.format_exc()
# vôlei
get("sofa_volei", f"https://api.sofascore.com/api/v1/sport/volleyball/scheduled-events/{hoje:%Y-%m-%d}")
get("sofa_volei_www", f"https://www.sofascore.com/api/v1/sport/volleyball/scheduled-events/{hoje:%Y-%m-%d}")
get("espn_core_volei", "https://sports.core.api.espn.com/v2/sports/volleyball/leagues")
get("tsdb_123", f"https://www.thesportsdb.com/api/v1/json/123/eventsday.php?d={hoje:%Y-%m-%d}&s=Volleyball")
os.makedirs("esportes/lab", exist_ok=True)
json.dump(out, open("esportes/lab/sondagem2.json", "w"), indent=1, ensure_ascii=False, default=str)
