// Guarda o que o site mostrou (previsão por dia e por hora) para conferir depois com o que aconteceu.
const { chromium, devices } = require('playwright'); const fs = require('fs');
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ ...devices['iPhone 13'], timezoneId: 'America/Sao_Paulo', locale: 'pt-BR' });
  const p = await ctx.newPage(); await p.goto('http://localhost:8000/?t=' + Date.now());
  await p.waitForFunction(() => window.__L && window.__L.D, null, { timeout: 120000 });
  await p.waitForTimeout(8000);
  const r = await p.evaluate(() => { const L = window.__L, E = window.__NCUI && window.__NCUI.estado && window.__NCUI.estado();
    return { gerado: L.gen, dias: L.D.map(d => ({ dia: d[0], mm: d[1], mm_min: d[2], mm_max: d[3], chance: d[4], chance_cenarios: d[17] ?? null, p10: d[5], tmax: d[9], tmin: d[10], rajada: d[11],
      temporal: d[15] ? d[15].pct : null, trovoada: d[16] ? d[16].ts : null, chuva_cal: d[16] ? d[16].chuva : null, forte: d[16] ? d[16].forte : null })),
      horas: { inicio: L.H.start, chance: L.H.p, mm: L.H.mm, rajada: L.H.wg, vento: L.H.ws },
      nowcast: E ? { radar: E.t0, p: E.P.filter(x => x.m % 10 === 0).map(x => [x.m, +x.p.toFixed(2), x.z]) } : null, raios: window.__RAIOS || null, obs: window.__OBS ? { ...window.__OBS, t: String(window.__OBS.t) } : null }; });
  const t = new Date(); const nome = `lab/historico/${t.toISOString().slice(0, 13).replace('T', '_')}.json`;
  fs.mkdirSync('lab/historico', { recursive: true }); fs.writeFileSync(nome, JSON.stringify(r)); console.log(nome, JSON.stringify(r.dias.slice(0, 3)));
  await b.close();
})();
