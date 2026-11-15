// Revisão de layout: página inteira em celular pequeno (escuro) e grande (claro), e teste do botão de localização
const { chromium, devices } = require('playwright'); const fs = require('fs');
const BASE = process.env.SITE || 'http://localhost:8000/';
(async () => {
  const b = await chromium.launch(); const out = {};
  const cenarios = [['se_escuro', { ...devices['iPhone SE'], colorScheme: 'dark' }], ['max_claro', { ...devices['iPhone 14 Pro Max'], colorScheme: 'light' }]];
  for (const [nome, dev] of cenarios) {
    const ctx = await b.newContext({ ...dev, timezoneId: 'America/Sao_Paulo', locale: 'pt-BR', geolocation: { latitude: -23.4050, longitude: -51.9180, accuracy: 25 }, permissions: ['geolocation'] });
    const p = await ctx.newPage(); const er = []; p.on('pageerror', e => er.push(String(e).slice(0, 200)));
    await p.goto(BASE + '?t=' + Date.now()); await p.waitForSelector('.hero .box', { timeout: 90000 }).catch(e => er.push('hero ' + e));
    await p.waitForSelector('#nc .nc-h', { timeout: 60000 }).catch(() => {}); await p.waitForTimeout(5000);
    out[nome] = { erros: er, larguraPagina: await p.evaluate(() => [document.documentElement.scrollWidth, innerWidth]),
      transbordando: await p.evaluate(() => [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && (r.right > innerWidth + 1 || r.left < -1) && !e.closest('.hours,.leaflet-container,.recentes,.vt-hrs,.qres'); }).slice(0, 12).map(e => e.tagName + '.' + e.className + ' ' + Math.round(e.getBoundingClientRect().right))) };
    await p.screenshot({ path: `lab/fotos/l_${nome}.png`, fullPage: true });
    if (nome === 'se_escuro') {
      await Promise.all([p.waitForNavigation({ timeout: 40000 }).catch(() => {}), p.click('#gpsbtn')]);
      await p.waitForSelector('.hero .box', { timeout: 90000 }).catch(() => {}); await p.waitForTimeout(4000);
      out.gps = await p.evaluate(() => ({ url: location.href, h1: document.getElementById('cidade').textContent, sub: document.getElementById('cidade-uf').textContent, stamp: document.getElementById('stamp').innerText, audit: !document.getElementById('audit').hidden, vento: document.getElementById('vt').innerText.slice(0, 80), nc: document.getElementById('nc').innerText.slice(0, 120) }));
      await p.screenshot({ path: 'lab/fotos/l_gps.png' });
    }
    await ctx.close(); }
  fs.writeFileSync('lab/fotos/layout.json', JSON.stringify(out, null, 1)); console.log(JSON.stringify(out, null, 1)); await b.close();
})();
