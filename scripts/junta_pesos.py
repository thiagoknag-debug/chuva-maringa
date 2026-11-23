"""Grava no lab/pesos.json (versão mais nova do repositório) só as chaves que este robô calculou, sem apagar as dos outros."""
import json, sys
novo = json.load(open(sys.argv[1])); dest = sys.argv[2]
try: base = json.load(open(dest))
except Exception: base = {}
for k in sys.argv[3:]:
    if k in novo: base[k] = novo[k]
    elif k in ("risco", "risco_cape"): base.pop(k, None)   # a auditoria decide se esses entram
json.dump(base, open(dest, "w"), ensure_ascii=False, indent=1)
print("pesos.json:", sorted(base))
