// Situação na rota: radar (agora + próximos 90 min) e modelos (próximas 6 h) em pontos da viagem
const NC = require('./nowcast.core.js'); const { PNG } = require('pngjs'); const fs = require('fs');
const UA = { 'User-Agent': 'chuva-maringa' };
const png = async u => { for (let t = 0; t < 3; t++) { try { const r = await fetch(u, { headers: UA }); if (r.ok) return PNG.sync.read(Buffer.from(await r.arrayBuffer())); } catch (e) {} } return null; };
const geo = async q => { try { const j = await (await fetch('https://geocoding-api.open-meteo.com/v1/search?count=5&language=pt&name=' + encodeURIComponent(q))).json(); return (j.results || []).filter(x => x.country_code === 'BR'); } catch (e) { return []; } };
const nomi = async q => { try { const j = await (await fetch('https://nominatim.openstreetmap.org/search?format=json&limit=5&countrycodes=br&q=' + encodeURIComponent(q), { headers: UA })).json(); return j.map(x => ({ name: x.display_name, latitude: +x.lat, longitude: +x.lon })); } catch (e) { return []; } };
(async () => {
  const out = { gerado: new Date().toISOString(), busca: {} };
  for (const q of ['Floresta', 'Porto Maringá', 'Porto Maringa Paraná']) { out.busca[q] = { om: (await geo(q)).map(x => [x.name, x.admin1, x.latitude, x.longitude]), osm: (await nomi(q)).slice(0, 5).map(x => [x.name, x.latitude, x.longitude]) }; }
  fs.mkdirSync('lab', { recursive: true }); fs.writeFileSync('lab/sondagem_rota.json', JSON.stringify(out, null, 1));
  const fl = (await geo('Floresta')).find(x => x.admin1 === 'Paraná') || { latitude: -23.60, longitude: -52.08 };
  let pm = (await nomi('Porto Maringá, Paraná'))[0] || (await nomi('Porto Maringá'))[0];
  const pts = [['Maringá (centro)', -23.425, -51.938], ['Floresta', fl.latitude, fl.longitude]];
  if (pm) { pts.push(['Meio do caminho', (fl.latitude + pm.latitude) / 2, (fl.longitude + pm.longitude) / 2]); pts.push(['Porto Maringá', pm.latitude, pm.longitude]); }
  out.pontos = pts;
  // radar
  const j = await (await fetch('https://api.rainviewer.com/public/weather-maps.json', { headers: UA })).json();
  const fr = j.radar.past.slice(-4), Q = [];
  for (const f of fr) { const G = NC.novaGrade(); await Promise.all(NC.tiles().map(async t => { const p = await png(`${j.host}${f.path}/256/${NC.Z}/${t.x}/${t.y}/2/0_0.png`); if (p) NC.poeTile(G, p.data, t.ox, t.oy); })); Q.push({ t: f.time, G }); }
  const C = new Uint8Array(NC.N * NC.N); for (const t of NC.tiles()) { const p = await png(`${j.host}/v2/coverage/0/256/${NC.Z}/${t.x}/${t.y}/0/0_0.png`); if (p) NC.poeCobertura(C, p.data, t.ox, t.oy); }
  const n = 256 * 2 ** NC.Z, px = (lat, lon) => { const x = (lon + 180) / 360 * n, s = Math.sin(lat * Math.PI / 180), y = (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * n; return [x - (NC.tiles()[0].x) * 256, y - (NC.tiles()[0].y) * 256]; };
  out.radar_hora = new Date(Q[Q.length - 1].t * 1000).toISOString();
  out.radar = pts.map(([nome, la, lo]) => { const a = px(la, lo), V = NC.velocidade(Q, null, a), P = NC.prever(Q, V.v, Date.now() / 1000, a, C);
    const raio = r => { const d = NC.disco(Q[Q.length - 1].G, a[0], a[1], r / NC.KM); return { p: +d.p.toFixed(2), z: d.z }; };
    let zmax = -128; const R = 25 / NC.KM; for (let y = Math.floor(a[1] - R); y <= a[1] + R; y++) for (let x = Math.floor(a[0] - R); x <= a[0] + R; x++) if ((x - a[0]) ** 2 + (y - a[1]) ** 2 <= R * R) zmax = Math.max(zmax, Q[Q.length - 1].G[y * NC.N + x]);
    return { nome, agora_5km: raio(5), agora_15km: raio(15), dbz_max_25km: zmax, mov_kmh: Math.round(V.kmh), dir_para: Math.round((Math.atan2(V.v.vx, -V.v.vy) * 180 / Math.PI + 360) % 360), prox: NC.maisProximo(Q[Q.length - 1].G, V.v, a), prox_min: P.filter(x => x.m % 10 === 0).map(x => [x.m, +x.p.toFixed(2), x.z, +x.u.toFixed(1)]) }; });
  // modelos (6 h) nos pontos
  const la = pts.map(p => p[1].toFixed(3)).join(','), lo = pts.map(p => p[2].toFixed(3)).join(',');
  const M = ['ecmwf_ifs', 'icon_seamless', 'gfs_seamless', 'ukmo_seamless', 'gem_seamless', 'meteofrance_seamless', 'best_match'];
  try { let f = await (await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${la}&longitude=${lo}&hourly=precipitation,wind_gusts_10m,cape&models=${M.join(',')}&forecast_days=1&timezone=America%2FSao_Paulo`)).json(); if (!Array.isArray(f)) f = [f];
    const h0 = new Date(Date.now() - 3 * 3600e3).getUTCHours();
    out.modelos = f.map((x, k) => ({ nome: pts[k][0], horas: x.hourly.time.map((t, i) => [t.slice(11, 13), i]).filter(([hh]) => +hh >= h0 && +hh <= h0 + 6).map(([hh, i]) => { const pr = M.map(m => x.hourly['precipitation_' + m][i]).filter(v => v != null), g = M.map(m => x.hourly['wind_gusts_10m_' + m][i]).filter(v => v != null), c = M.map(m => x.hourly['cape_' + m][i]).filter(v => v != null);
      return [hh + 'h', 'chovem ' + pr.filter(v => v >= 0.3).length + '/' + pr.length, 'mm máx ' + Math.max(...pr).toFixed(1), 'raj máx ' + Math.round(Math.max(...g)), 'cape máx ' + Math.round(Math.max(...c))]; }) })); } catch (e) { out.modelos_erro = String(e); }
  try { const r = await fetch('https://apiprevmet3.inmet.gov.br/avisos/ativos'); const av = await r.json();
    out.avisos = [...(av.hoje || []), ...(av.futuro || [])].filter(a => /Maring[aá] - PR|Floresta - PR|S[aã]o Pedro do Paran[aá]|Porto Rico - PR|Marilena|Paranava/i.test(a.municipios || '')).map(a => [a.severidade, a.descricao, a.data_inicio, a.hora_inicio, a.data_fim, a.hora_fim]); } catch (e) { out.avisos_erro = String(e); }
  try { out.metar = (await (await fetch('https://aviationweather.gov/api/data/metar?ids=SBMG&hours=3&format=raw')).text()).trim().split('\n'); } catch (e) {}
  fs.writeFileSync('lab/sondagem_rota.json', JSON.stringify(out, null, 1)); console.log(JSON.stringify(out).slice(0, 6000));
})();
