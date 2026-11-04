"""Envia a previsão para o celular pelo app ntfy. Uso: python scripts/avisar.py manha|tarde"""
import json, os, sys, requests
sys.path.insert(0, os.path.dirname(__file__))
from previsao import calcular

TOPICO = os.environ.get("NTFY_TOPIC", "").strip()
SITE = "https://thiagoknag-debug.github.io/chuva-maringa/"
modo = sys.argv[1] if len(sys.argv) > 1 else "manha"
P = calcular()
os.makedirs("lab", exist_ok=True)
json.dump(P, open("lab/ultima_previsao.json", "w"), ensure_ascii=False, indent=1)

def linha(nome, d):
    r = d["risco"]
    s = f"{nome}: {d['tmin']}°–{d['tmax']}° · chuva {d['chance'] if d['chance'] is not None else '—'}% (~{d['chuva_mm']:g} mm)"
    if d["rajada"]: s += f" · rajadas {d['rajada']} km/h"
    hs = []
    if d.get("pico_chuva") is not None: hs.append(f"chuva mais forte ~{d['pico_chuva']:02d}h")
    tw = d.get("trovoada")
    if tw: hs.append(f"trovoada {tw['de']:02d}h–{tw['ate']:02d}h (pico ~{tw['pico']:02d}h)")
    if d["rajada"] and d["rajada"] >= 40 and d.get("pico_rajada") is not None: hs.append(f"rajada mais forte ~{d['pico_rajada']:02d}h")
    if hs: s += " · " + ", ".join(hs)
    s += f" · temporal: {r['nivel'].lower()} ({r['pct']}%)"
    if d["aviso"]: s += f" · aviso {d['aviso']} INMET"
    return s

hoje, amanha = P["dias"]
alto = [d for d in P["dias"] if d["risco"]["pct"] >= 25 or d["aviso"] in ("laranja", "vermelho")]
if modo == "tarde" and not alto:
    print("tarde sem risco alto: nada enviado"); sys.exit(0)

corpo = linha("Hoje", hoje) + "\n" + linha("Amanhã", amanha)
if any(d["risco"]["parecido_2_11"] for d in P["dias"]):
    corpo += "\n⚠️ Cenário parecido com o temporal de 2/11. Evite deixar carro sob árvores e acompanhe o radar."
if alto:
    pior = max(P["dias"], key=lambda d: d["risco"]["pct"])
    titulo = f"⛈️ Risco {pior['risco']['nivel'].lower()} de temporal {'hoje' if pior is hoje else 'amanhã'} ({pior['risco']['pct']}%)"
    prio, tags = ("urgent" if pior["risco"]["pct"] >= 50 else "high"), "warning,cloud_with_lightning_and_rain"
else:
    titulo, prio, tags = "Previsão de Maringá", "default", "partly_sunny"

print(titulo); print(corpo)
if not TOPICO:
    print("NTFY_TOPIC não configurado: nada enviado"); sys.exit(0)
r = requests.post("https://ntfy.sh/", json={"topic": TOPICO, "title": titulo, "message": corpo,
                  "priority": {"default": 3, "high": 4, "urgent": 5}[prio], "tags": tags.split(","), "click": SITE}, timeout=30)
print("ntfy:", r.status_code)
