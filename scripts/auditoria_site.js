// Varredura do site com dados reais: erros, textos quebrados, coerência entre cartões, horários-limite e desempenho.
const { chromium, devices } = require('playwright'); const fs = require('fs');
const BASE = process.env.SITE || 'http://localhost:8000/';
const RUIM = /\bundefined\b|\bNaN\b|\bnull\b|Infinity|\[object|—°|NaN%|-?Infinity/;
async function cenario(b, nome, { hash = '', dev = devices['iPhone 13'], hora = null, geo = null } = {}) {
  const ctx = await b.newContext({ ...dev, timezoneId: 'America/Sao_Paulo', locale: 'pt-BR', ...(geo ? { geolocation: geo, permissions: ['geolocation'] } : {}) });
  const p = await ctx.newPage(); const r = { nome, erros: [], console: [], falhas: [], ruins: [] };
  if (hora) await p.clock.setFixedTime(new Date(hora));
  p.on('pageerror', e => r.erros.push(String(e).slice(0, 300)));
  p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') r.console.push(m.text().slice(0, 200)); });
  p.on('response', x => { if (x.status() >= 400) r.falhas.push(x.status() + ' ' + x.url().slice(0, 120)); });
  p.on('requestfailed', x => r.falhas.push('FALHOU ' + x.url().slice(0, 120) + ' ' + (x.failure() || {}).errorText));
  const t0 = Date.now();
  await p.goto(BASE + '?t=' + Date.now() + hash);
  await p.waitForSelector('.hero .box', { timeout: 90000 }).catch(e => r.erros.push('hero não carregou'));
  r.ms_resumo = Date.now() - t0;
  await p.waitForFunction(() => document.querySelector('#nc .nc-h') || /sem imagem nova|relógio|indisponível/.test((document.querySelector('#nc .hint') || {}).textContent || ''), null, { timeout: 60000 }).catch(() => r.erros.push('60min não carregou'));
  await p.waitForSelector('#ra .ra-h', { timeout: 60000 }).catch(() => r.erros.push('raios não carregou'));
  await p.waitForTimeout(11000); r.ms_total = Date.now() - t0;
  const txt = await p.evaluate(() => document.body.innerText);
  txt.split('\n').forEach(l => { if (/\bundefined\b|\bNaN\b|\bnull\b|Infinity|\[object/.test(l)) r.ruins.push(l.slice(0, 160)); });
  r.fatos = await p.evaluate(() => {
    const t = s => (document.querySelector(s)?.innerText || '').replace(/\s+/g, ' ').trim();
    const E = window.__NCUI && window.__NCUI.estado ? window.__NCUI.estado() : null;
    return { cidade: t('#cidade'), stamp: t('#stamp'), now: t('#hero .now'), proxima: t('#nxlab') + ' | ' + t('#nxhead') + ' | ' + t('#nxsub'),
      hoje: t('.hero .box'), dia0: t('.day'), horas: document.querySelectorAll('#hours .h, .hours .h').length, nc: t('#nc .nc-h') || t('#nc .hint'), conf: t('#nc .nc-conf'),
      p0: E ? +E.P[0].p.toFixed(2) : null, vento: t('#vt .vt-main') + ' | ' + t('#vt .vt-av'), raios: t('#ra .ra-h'), blend: t('#nc .nc-blend'), satlinha: t('#nc .nc-sat'), sat: window.__SAT ? JSON.stringify(window.__SAT) : null, cal: !!(window.__L && window.__L.H && window.__L.H.cal), hrsnota: t('#hrsnota'), r_marcas: document.querySelectorAll('#hours .p sup').length, avisos: [...document.querySelectorAll('.chip summary')].map(x => x.textContent.trim()),
      dias: document.querySelectorAll('.day').length };
  });
  // abre o painel de cada dia
  r.paineis = [];
  const n = await p.$$eval('.day', x => x.length);
  for (let i = 0; i < n; i++) { const ok = await p.evaluate(i => { try { document.querySelectorAll('.day')[i].click(); const s = document.getElementById('sheet'); const ok = s && !s.hidden; const tx = document.getElementById('sheet-body').innerText; document.querySelector('.sheet-x').click(); return ok ? (/\bundefined\b|\bNaN\b|\bnull\b|Infinity/.test(tx) ? 'ruim: ' + tx.match(/.{0,40}(undefined|NaN|null|Infinity).{0,40}/)[0] : 'ok') : 'não abriu'; } catch (e) { return 'erro ' + e; } }, i); r.paineis.push(ok); }
  // radar: previsão por horário
  try { await p.click('#tab-prev'); await p.waitForFunction(() => !/Carregando/.test(document.getElementById('pinfo').textContent), null, { timeout: 60000 }); r.radar_prev = (await p.textContent('#pinfo')).slice(0, 200); await p.click('#tab-agora'); } catch (e) { r.radar_prev = 'ERRO ' + String(e).slice(0, 100); }
  await p.screenshot({ path: `lab/fotos/a_${nome}.png`, fullPage: true });
  await ctx.close(); return r;
}
(async () => {
  const b = await chromium.launch(); const out = { gerado: new Date().toISOString(), cenarios: [] };
  const hoje = new Date(); const d = hoje.toISOString().slice(0, 10);
  const lista = [['maringa', {}], ['maringa_23h40', { hora: `${d}T23:40:00-03:00` }], ['maringa_00h20', { hora: `${d}T00:20:00-03:00` }], ['maringa_06h', { hora: `${d}T06:05:00-03:00` }],
    ['curitiba', { hash: '#curitiba-pr' }], ['gps_centro', { hash: '#gps', geo: { latitude: -23.421, longitude: -51.933, accuracy: 20 } }], ['iphone_se', { dev: devices['iPhone SE'] }]];
  for (const [nome, o] of lista) { try { out.cenarios.push(await cenario(b, nome, o)); } catch (e) { out.cenarios.push({ nome, fatal: String(e).slice(0, 300) }); } }
  fs.writeFileSync('lab/auditoria_site.json', JSON.stringify(out, null, 1)); console.log(JSON.stringify(out, null, 1).slice(0, 12000)); await b.close();
})();
