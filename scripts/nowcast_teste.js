// Testa o nowcast com os quadros reais do radar das últimas 2 h: compara previsão x o que o radar mostrou depois, em ~150 pontos em volta de Maringá.
const NC = require('./nowcast.core.js'); const { PNG } = require('pngjs'); const fs = require('fs');
const UA = { 'User-Agent': 'chuva-maringa' };
const png = async u => { for (let t = 0; t < 3; t++) { try { const r = await fetch(u, { headers: UA }); if (r.ok) return PNG.sync.read(Buffer.from(await r.arrayBuffer())); } catch (e) {} } return null; };
(async () => {
  const j = await (await fetch('https://api.rainviewer.com/public/weather-maps.json', { headers: UA })).json();
  const fr = j.radar.past; const Q = [];
  for (const f of fr) { const G = NC.novaGrade(); let ok = 0;
    await Promise.all(NC.tiles().map(async t => { const p = await png(`${j.host}${f.path}/256/${NC.Z}/${t.x}/${t.y}/2/0_0.png`); if (p) { NC.poeTile(G, p.data, t.ox, t.oy); ok++; } }));
    Q.push({ t: f.time, G, ok }); }
  const cov = []; const cg = NC.novaGrade();
  const covInfo = {}; for (const t of NC.tiles()) { const p = await png(`${j.host}/v2/coverage/0/256/${NC.Z}/${t.x}/${t.y}/0/0_0.png`); if (!p) continue;
    if (t.ox === 256 && t.oy === 256) { const x = Math.floor(NC.PX - 256), y = Math.floor(NC.PY - 256), o = (y * 256 + x) * 4; covInfo.maringa = [...p.data.slice(o, o + 4)]; }
    let a0 = 0, a1 = 0; for (let i = 3; i < p.data.length; i += 4) p.data[i] ? a1++ : a0++; covInfo[t.x + '/' + t.y] = { transp: a0, opaco: a1 }; }
  const res = { gerado: new Date().toISOString(), quadros: Q.map(q => ({ hora: new Date(q.t * 1000).toISOString().slice(11, 16), tiles: q.ok, ecos20: q.G.reduce((s, z) => s + (z >= 20), 0) })), cobertura: covInfo };
  // avaliação em 9 regiões do mosaico (onde houver chuva), cada uma com seu próprio movimento
  const est = {}; const add = (k, f, o) => { est[k] = est[k] || { H: 0, M: 0, F: 0, C: 0 }; const e = est[k]; if (f && o) e.H++; else if (!f && o) e.M++; else if (f && !o) e.F++; else e.C++; };
  const vel = []; const regs = []; for (const cy of [200, 384, 568]) for (const cx of [200, 384, 568]) regs.push([cx, cy]);
  for (const [cx, cy] of regs) {
    const alvos = []; for (let dy = -100; dy <= 100; dy += 12) for (let dx = -100; dx <= 100; dx += 12) if (Math.hypot(dx, dy) <= 100) alvos.push([cx + dx / NC.KM, cy + dy / NC.KM]);
    for (let k = 3; k < Q.length - 1; k++) {
      const hist = Q.slice(Math.max(0, k - 3), k + 1), V = NC.velocidade(hist, null, [cx, cy]);
      vel.push({ reg: cx + ',' + cy, hora: new Date(Q[k].t * 1000).toISOString().slice(11, 16), fonte: V.fonte, kmh: Math.round(V.kmh), disp: V.disp && Math.round(V.disp), dir_para: Math.round((Math.atan2(V.v.vx, -V.v.vy) * 180 / Math.PI + 360) % 360) });
      for (let s = 1; k + s < Q.length && s <= 6; s++) { const lead = Math.round((Q[k + s].t - Q[k].t) / 60);
        for (const a of alvos) { const obs = NC.disco(Q[k + s].G, a[0], a[1], 2.5 / NC.KM).p >= 0.5;
          const pv = NC.prever(hist, V.v, Q[k].t, a)[lead]; add('nowcast_' + lead, pv.p >= 0.5, obs); add('nowcast35_' + lead, pv.p >= 0.35, obs);
          add('persist_' + lead, NC.disco(Q[k].G, a[0], a[1], 2.5 / NC.KM).p >= 0.5, obs); } } } }
  for (const k in est) { const e = est[k]; e.CSI = +(e.H / Math.max(1, e.H + e.M + e.F)).toFixed(2); e.POD = +(e.H / Math.max(1, e.H + e.M)).toFixed(2); e.FAR = +(e.F / Math.max(1, e.H + e.F)).toFixed(2); }
  res.velocidades = vel; res.placar = est;
  // previsão de agora para Maringá
  const V = NC.velocidade(Q, null), P = NC.prever(Q, V.v, Date.now() / 1000);
  res.agora = { vel: { fonte: V.fonte, kmh: Math.round(V.kmh), disp: V.disp }, proximo: NC.maisProximo(Q[Q.length - 1].G, V.v), tipo: NC.tipo(Q[Q.length - 1].G, 60), minutos: P.filter(x => x.m % 5 === 0).map(x => [x.m, +x.p.toFixed(2), x.z]) };
  fs.writeFileSync('lab/sondagem_nowcast.json', JSON.stringify(res, null, 1)); console.log(JSON.stringify(res).slice(0, 5000));
})();
