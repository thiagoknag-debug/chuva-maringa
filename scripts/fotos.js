// Tira fotos do site (como iPhone) com dados reais: topo, painel de amanhã e previsão do radar às 18h
const { chromium, devices } = require('playwright');
const fs = require('fs');
(async () => {
  fs.mkdirSync('lab/fotos', { recursive: true });
  const b = await chromium.launch();
  const ctx = await b.newContext({ ...devices['iPhone 13'], colorScheme: 'dark', timezoneId: 'America/Sao_Paulo', locale: 'pt-BR' });
  const p = await ctx.newPage(); const erros = []; const out = { erros };
  p.on('pageerror', e => erros.push(String(e).slice(0, 300)));
  p.on('console', m => { if (m.type() === 'error') erros.push(m.text().slice(0, 300)); });
  await p.goto((process.env.SITE || 'http://localhost:8000/') + '?t=' + Date.now(), { waitUntil: 'load' });
  await p.waitForSelector('.hero .box', { timeout: 90000 }).catch(() => {});
  await p.waitForTimeout(4000);
  await p.screenshot({ path: 'lab/fotos/1_topo.png' });
  await p.waitForSelector('#nc .nc-h', { timeout: 60000 }).catch(e => erros.push('nc ' + e));
  await p.locator('#nc').screenshot({ path: 'lab/fotos/0_nowcast.png' }).catch(() => {});
  out.nc = await p.evaluate(() => ({ txt: (document.getElementById('nc').innerText || '').slice(0, 1500), err: window.__ncErr || null,
    est: window.__NCUI && window.__NCUI.estado() ? (e => ({ fonte: e.V.fonte, kmh: Math.round(e.V.kmh), disp: e.V.disp, prox: e.prox, tipo: e.tipo, p: e.P.filter(x => x.m % 5 === 0).map(x => [x.m, +x.p.toFixed(2), x.z, +x.u.toFixed(2)]) }))(window.__NCUI.estado()) : null }));
  out.chips = await p.$$eval('.rk-chip', x => x.map(e => e.textContent));
  await p.click('.hero .box >> nth=1').catch(e => erros.push('box ' + e));
  await p.waitForTimeout(800); await p.screenshot({ path: 'lab/fotos/2_amanha.png' });
  out.sheet_head = await p.textContent('.sh-head').catch(() => null);
  await p.click('.sheet-x').catch(() => {});
  await p.locator('#radar').scrollIntoViewIfNeeded();
  await p.click('#tab-prev'); await p.waitForFunction(() => !/Carregando/.test(document.getElementById('pinfo').textContent), null, { timeout: 60000 }).catch(e => erros.push('prev ' + e));
  const amanha = await p.$eval('#pdia', s => s.options[1] ? s.options[1].value : s.value);
  await p.selectOption('#pdia', amanha); await p.fill('#phora', '18:00'); await p.dispatchEvent('#phora', 'change');
  await p.waitForTimeout(1500);
  await p.locator('#radar').screenshot({ path: 'lab/fotos/3_radar_18h.png' });
  out.pinfo = await p.textContent('#pinfo'); out.overlay = await p.$$eval('#rmap img.leaflet-image-layer', x => x.length);
  await p.selectOption('#pcam', 'p'); await p.waitForTimeout(800);
  await p.locator('#radar').screenshot({ path: 'lab/fotos/4_radar_chance.png' });
  await p.click('#tab-agora'); await p.waitForTimeout(1500); out.volta = await p.textContent('#rtime');
  fs.writeFileSync('lab/fotos/resultado.json', JSON.stringify(out, null, 1)); console.log(JSON.stringify(out, null, 1));
  await b.close();
})();
