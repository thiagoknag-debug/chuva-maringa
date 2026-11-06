// Testa a busca e outras cidades (como iPhone, dados reais)
const { chromium, devices } = require('playwright'); const fs = require('fs');
const BASE = process.env.SITE || 'http://localhost:8000/';
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ ...devices['iPhone 13'], colorScheme: 'dark', timezoneId: 'America/Sao_Paulo', locale: 'pt-BR' });
  const out = {};
  const ver = async (hash, nome) => { const p = await ctx.newPage(); const er = []; p.on('pageerror', e => er.push(String(e).slice(0, 200)));
    await p.goto(BASE + '?t=' + Date.now() + hash); await p.waitForSelector('.hero .box', { timeout: 90000 }).catch(e => er.push('hero ' + e));
    await p.waitForSelector('#nc .nc-h', { timeout: 60000 }).catch(e => er.push('nc ' + e)); await p.waitForTimeout(1500);
    const r = await p.evaluate(() => ({ h1: document.getElementById('cidade').textContent, uf: document.getElementById('cidade-uf').textContent, title: document.title,
      stamp: document.getElementById('stamp').innerText, alertas: [...document.querySelectorAll('.chip summary')].map(x => x.textContent.trim()),
      hero: document.getElementById('hero').innerText.slice(0, 400), nc: document.getElementById('nc').innerText.slice(0, 300), audit_oculto: document.getElementById('audit').hidden,
      dias: document.querySelectorAll('.day').length, recentes: document.getElementById('recentes').innerText, calib: !document.getElementById('calibNota').hidden, ncErr: window.__ncErr || null }));
    r.erros = er; await p.screenshot({ path: `lab/fotos/c_${nome}.png` }); out[nome] = r; return p; };
  const p1 = await ver('', 'maringa');
  await p1.fill('#q', 'Londr'); await p1.waitForSelector('#qres li[data-i]', { timeout: 15000 }).catch(() => {});
  out.busca_lista = await p1.$$eval('#qres li', x => x.map(e => e.innerText.replace(/\s+/g, ' ')).slice(0, 6));
  await p1.screenshot({ path: 'lab/fotos/c_busca.png' });
  await Promise.all([p1.waitForNavigation({ timeout: 30000 }).catch(() => {}), p1.click('#qres li[data-i="0"]').catch(() => {})]);
  await p1.waitForSelector('.hero .box', { timeout: 90000 }).catch(() => {});
  out.apos_busca = { url: p1.url(), h1: await p1.textContent('#cidade'), recentes: await p1.innerText('#recentes') };
  await ver('#cianorte-pr', 'cianorte'); await ver('#manaus-am', 'manaus'); await ver('#xyzinexistente-pr', 'inexistente');
  fs.writeFileSync('lab/fotos/cidades.json', JSON.stringify(out, null, 1)); console.log(JSON.stringify(out, null, 1).slice(0, 6000)); await b.close();
})();
