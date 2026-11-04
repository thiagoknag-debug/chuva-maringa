// Abre o site com dados reais (no GitHub Actions) e grava o que apareceu na tela em lab/verificacao.json
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');
const BASE = 'https://thiagoknag-debug.github.io/chuva-maringa/';
const erros = [];
const vc = new VirtualConsole();
vc.on('jsdomError', e => erros.push(String(e && e.message || e).slice(0, 300)));
vc.on('error', e => erros.push(String(e).slice(0, 300)));
const html = fs.readFileSync('index.html', 'utf8');
const dom = new JSDOM(html, { url: BASE, runScripts: 'dangerously', resources: 'usable', pretendToBeVisual: true, virtualConsole: vc,
  beforeParse(w) {
    w.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {} });
    w.fetch = (u, o) => fetch(new URL(String(u), BASE).href, o && o.signal ? { signal: o.signal } : undefined);
  } });
const w = dom.window;
setTimeout(() => {
  const d = w.document, t = s => (d.querySelector(s)?.textContent || '').replace(/\s+/g, ' ').trim();
  const out = {
    gerado: new Date().toISOString(), erros,
    resumo: t('#hero'), classe_resumo: d.getElementById('hero')?.className,
    avisos: [...d.querySelectorAll('.chip summary')].map(x => x.textContent.trim()),
    horas: d.querySelectorAll('.h').length,
    horas_amostra: [...d.querySelectorAll('.h')].slice(0, 12).map(x => x.textContent.replace(/\s+/g, ' ').trim()),
    dias: [...d.querySelectorAll('.day')].map(x => x.textContent.replace(/\s+/g, ' ').trim()),
    radar_msg: t('#rmsg'), radar_hora: t('#rtime'), leaflet: !!w.L, radar_erro: w.__radarErr || null, camadas: d.querySelectorAll('.leaflet-tile-container,.leaflet-layer').length,
    rodape: t('.foot'), carimbo: t('#stamp'),
    auditoria_ranking: d.querySelectorAll('.rk').length
  };
  fs.mkdirSync('lab', { recursive: true });
  fs.writeFileSync('lab/verificacao.json', JSON.stringify(out, null, 1));
  console.log(JSON.stringify(out, null, 1).slice(0, 4000));
  process.exit(0);
}, 70000);
