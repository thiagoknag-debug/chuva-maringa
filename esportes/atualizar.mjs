// Monta a agenda da semana (ontem → +8 dias) e grava esportes/saida/semana.json
import { createRequire } from "module";
import fs from "fs";
const N = createRequire(import.meta.url)("./nucleo.js");

const agora = new Date();
const dias = [];
for (let i = -1; i <= 8; i++) dias.push(N.diaET(new Date(agora.getTime() + i * 864e5)));
const diasIso = []; for (let i = -1; i <= 7; i++) diasIso.push(N.diaBR(new Date(agora.getTime() + i * 864e5)));

async function pega(u, tent = 3) {
  for (let i = 0; i < tent; i++) {
    try {
      const r = await fetch(u, { headers: { "User-Agent": "Mozilla/5.0 agenda-esportiva" } });
      if (r.ok) return await r.json();
      if (r.status === 400 || r.status === 404) return null;
    } catch (e) {}
    await new Promise((r) => setTimeout(r, 1500 * (i + 1)));
  }
  return null;
}
async function emLotes(tarefas, n) {
  const res = []; let i = 0;
  await Promise.all(Array.from({ length: n }, async () => { while (i < tarefas.length) { const k = i++; res[k] = await tarefas[k](); } }));
  return res;
}

const log = {}; const todos = new Map();
const add = (lista, fonte) => lista.forEach((e) => { if (!todos.has(e.id) || e.st.e !== "pre") todos.set(e.id, e); log[fonte] = (log[fonte] || 0) + 1; });

const tarefas = [];
for (const L of N.LIGAS) {
  const porDia = !/^(racing|golf)\//.test(L.k);
  const ds = porDia ? dias : [null, ...dias.filter((_, i) => i % 3 === 1)];
  for (const d of ds) tarefas.push(async () => { const j = await pega(N.urlEspn(L.k, d)); if (j) add(N.lerEspn(L.k, j), L.k); });
}
await emLotes(tarefas, 8);

// TheSportsDB: limite gratuito ~30/min → devagar
for (const cfg of N.TSDB_ESPORTES) for (const d of diasIso) {
  const j = await pega(N.urlTsdb(cfg.s, d), 2);
  if (j) add(N.lerTsdb(cfg, j), "tsdb:" + cfg.s);
  await new Promise((r) => setTimeout(r, 2500));
}

const ini = new Date(agora.getTime() - 30 * 3600e3), fim = new Date(agora.getTime() + 8.5 * 864e5);
const eventos = [...todos.values()].filter((e) => {
  const t = new Date(e.t); const tf = e.fimT ? new Date(e.fimT) : t;
  return tf >= ini && t <= fim;
}).sort((a, b) => a.t.localeCompare(b.t));

fs.mkdirSync("esportes/saida", { recursive: true });
fs.writeFileSync("esportes/saida/semana.json", JSON.stringify({ gerado: agora.toISOString(), n: eventos.length, eventos }));
console.log(JSON.stringify({ n: eventos.length, por_fonte: log, finais: eventos.filter((e) => e.fase === "final").map((e) => e.liga + ": " + e.tit + " " + e.t) }, null, 1));
