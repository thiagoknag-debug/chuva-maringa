/* Núcleo da Agenda Esportiva — usado pela página (navegador) e pela Action (Node).
   Lê o placar público da ESPN e o TheSportsDB e devolve eventos num formato único. */
(function (root) {
  const ESPN = "https://site.api.espn.com/apis/site/v2/sports/";
  const TSDB = "https://www.thesportsdb.com/api/v1/json/123/eventsday.php";

  const CATS = [
    { id: "futebol", nome: "Futebol", ico: "⚽" },
    { id: "auto", nome: "Automobilismo", ico: "🏁" },
    { id: "basquete", nome: "Basquete e NFL", ico: "🏀" },
    { id: "tenis", nome: "Tênis", ico: "🎾" },
    { id: "mma", nome: "MMA", ico: "🥊" },
    { id: "volei", nome: "Vôlei", ico: "🏐" },
    { id: "outros", nome: "Outros", ico: "🏆" },
  ];

  // p = peso da competição (0–10). tipo define como o placar é lido.
  const LIGAS = [
    { k: "soccer/bra.1", nome: "Brasileirão Série A", cat: "futebol", p: 10, tipo: "time" },
    { k: "soccer/conmebol.libertadores", nome: "Libertadores", cat: "futebol", p: 10, tipo: "time" },
    { k: "soccer/bra.copa_do_brasil", nome: "Copa do Brasil", cat: "futebol", p: 9, tipo: "time" },
    { k: "soccer/uefa.champions", nome: "Champions League", cat: "futebol", p: 9, tipo: "time" },
    { k: "soccer/conmebol.sudamericana", nome: "Sul-Americana", cat: "futebol", p: 8, tipo: "time" },
    { k: "soccer/eng.1", nome: "Premier League", cat: "futebol", p: 8, tipo: "time" },
    { k: "soccer/fifa.friendly", nome: "Amistosos de seleções", cat: "futebol", p: 6, tipo: "time" },
    { k: "soccer/uefa.nations", nome: "Liga das Nações", cat: "futebol", p: 6, tipo: "time" },
    { k: "soccer/bra.2", nome: "Brasileirão Série B", cat: "futebol", p: 6, tipo: "time" },
    { k: "soccer/esp.1", nome: "La Liga", cat: "futebol", p: 7, tipo: "time" },
    { k: "soccer/uefa.europa", nome: "Europa League", cat: "futebol", p: 6, tipo: "time" },
    { k: "soccer/ita.1", nome: "Serie A (Itália)", cat: "futebol", p: 6, tipo: "time" },
    { k: "soccer/ger.1", nome: "Bundesliga", cat: "futebol", p: 6, tipo: "time" },
    { k: "soccer/fra.1", nome: "Ligue 1", cat: "futebol", p: 5, tipo: "time" },
    { k: "soccer/uefa.europa.conf", nome: "Conference League", cat: "futebol", p: 4, tipo: "time" },
    { k: "soccer/por.1", nome: "Liga Portugal", cat: "futebol", p: 4, tipo: "time" },
    { k: "soccer/arg.1", nome: "Argentino", cat: "futebol", p: 4, tipo: "time" },
    { k: "soccer/usa.1", nome: "MLS", cat: "futebol", p: 4, tipo: "time" },
    { k: "soccer/fifa.cwc", nome: "Mundial de Clubes", cat: "futebol", p: 9, tipo: "time" },
    { k: "soccer/fifa.intercontinental_cup", nome: "Copa Intercontinental", cat: "futebol", p: 8, tipo: "time" },
    { k: "racing/f1", nome: "Fórmula 1", cat: "auto", p: 9, tipo: "corrida" },
    { k: "racing/irl", nome: "IndyCar", cat: "auto", p: 4, tipo: "corrida" },
    { k: "racing/nascar-premier", nome: "NASCAR Cup", cat: "auto", p: 3, tipo: "corrida" },
    { k: "basketball/nba", nome: "NBA", cat: "basquete", p: 8, tipo: "time" },
    { k: "football/nfl", nome: "NFL", cat: "basquete", p: 8, tipo: "time" },
    { k: "basketball/wnba", nome: "WNBA", cat: "basquete", p: 3, tipo: "time" },
    { k: "tennis/atp", nome: "ATP", cat: "tenis", p: 7, tipo: "tenis" },
    { k: "tennis/wta", nome: "WTA", cat: "tenis", p: 6, tipo: "tenis" },
    { k: "mma/ufc", nome: "UFC", cat: "mma", p: 7, tipo: "mma" },
    { k: "hockey/nhl", nome: "NHL (hóquei)", cat: "outros", p: 3, tipo: "time" },
    { k: "baseball/mlb", nome: "MLB (beisebol)", cat: "outros", p: 3, tipo: "time" },
    { k: "golf/pga", nome: "Golfe PGA Tour", cat: "outros", p: 3, tipo: "golfe" },
  ];

  // TheSportsDB: vôlei e motor (o que a ESPN não cobre)
  const TSDB_ESPORTES = [
    { s: "Volleyball", cat: "volei", p: 5, filtro: (l) => !/NCAA|College|Universit/i.test(l) },
    { s: "Motorsport", cat: "auto", p: 5, filtro: (l) => /MotoGP|Moto2|Stock Car|Formula E|WEC|World Endurance|WRC|Rally|Formula 2|Porsche|DTM|Super ?GT|Turismo/i.test(l) },
  ];

  const LIGA_POR_K = Object.fromEntries(LIGAS.map((l) => [l.k, l]));

  // ---------- utilidades ----------
  function diaET(d) {
    return new Intl.DateTimeFormat("en-CA", { timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit" }).format(d).replace(/-/g, "");
  }
  function diaBR(d) {
    return new Intl.DateTimeFormat("en-CA", { timeZone: "America/Sao_Paulo", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(d));
  }
  function urlEspn(k, dia) {
    return ESPN + k + "/scoreboard?limit=400&lang=pt&region=br" + (dia ? "&dates=" + dia : "");
  }
  function urlTsdb(s, diaIso) { return TSDB + "?d=" + diaIso + "&s=" + s; }
  const PT = { Brazil: "Brasil", Argentina: "Argentina", Germany: "Alemanha", France: "França", Spain: "Espanha", England: "Inglaterra", Italy: "Itália", Netherlands: "Holanda", Portugal: "Portugal", Uruguay: "Uruguai", Colombia: "Colômbia", Chile: "Chile", Paraguay: "Paraguai", Peru: "Peru", Ecuador: "Equador", Bolivia: "Bolívia", Venezuela: "Venezuela", Mexico: "México", "United States": "Estados Unidos", Japan: "Japão", Belgium: "Bélgica", Croatia: "Croácia", Switzerland: "Suíça", Morocco: "Marrocos", Senegal: "Senegal", Scotland: "Escócia", Wales: "País de Gales", Poland: "Polônia", Denmark: "Dinamarca", Sweden: "Suécia", Norway: "Noruega", Austria: "Áustria", Ireland: "Irlanda", Turkey: "Turquia", Türkiye: "Turquia", Greece: "Grécia", Czechia: "Tchéquia", Serbia: "Sérvia", Ukraine: "Ucrânia", Hungary: "Hungria", Romania: "Romênia", "South Korea": "Coreia do Sul", Australia: "Austrália", Canada: "Canadá", Egypt: "Egito", Nigeria: "Nigéria", Cameroon: "Camarões", Ghana: "Gana", "Saudi Arabia": "Arábia Saudita", Qatar: "Catar", Iran: "Irã", Tunisia: "Tunísia", Algeria: "Argélia", "Ivory Coast": "Costa do Marfim", "Costa Rica": "Costa Rica", Panama: "Panamá", Jamaica: "Jamaica", "New Zealand": "Nova Zelândia", Finland: "Finlândia", Iceland: "Islândia", Slovakia: "Eslováquia", Slovenia: "Eslovênia", Albania: "Albânia", Bulgaria: "Bulgária", Russia: "Rússia", "North Macedonia": "Macedônia do Norte", Montenegro: "Montenegro", Cyprus: "Chipre", Latvia: "Letônia", Lithuania: "Lituânia", Estonia: "Estônia", Belarus: "Bielorrússia", Armenia: "Armênia", Georgia: "Geórgia", Israel: "Israel", Luxembourg: "Luxemburgo", "Northern Ireland": "Irlanda do Norte", "Bosnia and Herzegovina": "Bósnia", Kosovo: "Kosovo", Moldova: "Moldávia", Azerbaijan: "Azerbaijão", Kazakhstan: "Cazaquistão", "South Africa": "África do Sul" };
  const tr = (s) => (s && PT[s]) || s || "";

  const TXT_FINAL = /(^|[^a-zà-ú])(final|finais|finals|grande final|decis[aã]o|super bowl|mls cup|world series|stanley cup final|nba finals|copa do brasil - final)([^a-zà-ú]|$)/i;
  const TXT_SEMI = /semi|semifinal|semi-final/i;
  const TXT_QUARTAS = /quarter|quartas|oitavas|round of 16|playoff|mata-mata|eliminat/i;
  function fase(textos) {
    const t = textos.filter(Boolean).join(" | ");
    if (!t) return "";
    if (TXT_SEMI.test(t)) return "semi";
    const limpo = t.replace(/(quarter|round of \d+)[- ]?finals?|quartas de final|oitavas de final|semi-?finals?/gi, "");
    if (TXT_FINAL.test(limpo)) return "final";
    if (TXT_QUARTAS.test(t) || /post-?season/i.test(t)) return "mata";
    return "";
  }
  function peso(base, f, extra) {
    let s = base * 10;
    if (f === "final") s += 120; else if (f === "semi") s += 45; else if (f === "mata") s += 15;
    return s + (extra || 0);
  }
  const ehBrasil = (n) => /^(Brasil|Brazil)$/i.test(n || "");

  function status(st) {
    st = st || {}; const t = st.type || {};
    return { e: t.state || "pre", txt: t.shortDetail || t.detail || t.description || "", rel: st.displayClock || "", per: st.period || 0, fim: !!t.completed };
  }
  function tvs(c) {
    const out = [];
    (c.broadcasts || []).forEach((b) => (b.names || []).forEach((n) => out.includes(n) || out.push(n)));
    (c.geoBroadcasts || []).forEach((g) => { const n = g.media && g.media.shortName; if (n && !out.includes(n)) out.push(n); });
    return out.slice(0, 4);
  }
  function linkEv(e) {
    const l = (e.links || []).find((x) => (x.rel || []).includes("summary")) || (e.links || [])[0];
    return l ? l.href : "";
  }
  function notas(c, e) {
    const n = [];
    (c.notes || []).forEach((x) => n.push(x.headline || x.text));
    (e.notes || []).forEach((x) => n.push(x.headline || x.text));
    return n.filter(Boolean);
  }

  // ---------- normalizadores ----------
  function lerTime(L, j) {
    const out = [];
    const ligaNome = L.nome;
    (j.events || []).forEach((e) => {
      const c = (e.competitions || [])[0]; if (!c) return;
      const cs = c.competitors || [];
      const casa = cs.find((x) => x.homeAway === "home") || cs[0] || {};
      const fora = cs.find((x) => x.homeAway === "away") || cs[1] || {};
      const lado = (x) => {
        const t = x.team || {};
        const nome = tr(t.shortDisplayName || t.displayName || t.name);
        return { n: nome, nl: tr(t.displayName) || nome, a: t.abbreviation || "", logo: t.logo || "", pl: x.score != null && x.score !== "" ? String(x.score) : "", rec: ((x.records || [])[0] || {}).summary || "", v: !!x.winner, id: t.id || "" };
      };
      const h = lado(casa), a = lado(fora);
      const ns = notas(c, e);
      const f = fase([...ns, e.season && e.season.slug, c.type && c.type.text]);
      const extra = ehBrasil(h.n) || ehBrasil(a.n) ? 60 : 0;
      const venue = c.venue || {};
      out.push({
        id: L.k + ":" + e.id, ev: e.id, k: L.k, cat: L.cat, liga: ligaNome, tipo: "time",
        t: e.date, st: status(c.status || e.status), casa: h, fora: a,
        tit: (a.n && h.n) ? h.n + " x " + a.n : (e.name || ""),
        local: venue.fullName || "", cid: [venue.address && venue.address.city, venue.address && venue.address.country].filter(Boolean).join(", "),
        tv: tvs(c), obs: ns.slice(0, 2), fase: f, sem: (e.week && e.week.number) ? "Semana " + e.week.number : "",
        temp: e.season && e.season.slug ? e.season.slug : "", link: linkEv(e), w: peso(L.p, f, extra),
      });
    });
    return out;
  }

  const SESSAO = { FP1: "Treino Livre 1", FP2: "Treino Livre 2", FP3: "Treino Livre 3", Qual: "Classificação", Q: "Classificação", SS: "Classificação Sprint", SQ: "Classificação Sprint", Sprint: "Corrida Sprint", Race: "Corrida", R: "Corrida" };
  function lerCorrida(L, j) {
    const out = [];
    (j.events || []).forEach((e) => {
      const circ = e.circuit || {};
      (e.competitions || []).forEach((c) => {
        const ab = (c.type && c.type.abbreviation) || "";
        const nomeS = SESSAO[ab] || ab || "Sessão";
        const corrida = /^(Race|R)$/i.test(ab);
        const top = (c.competitors || []).slice().sort((x, y) => (x.order || 99) - (y.order || 99)).slice(0, 5)
          .map((x) => ({ n: (x.athlete && (x.athlete.displayName || x.athlete.fullName)) || "", eq: (x.team && x.team.displayName) || "" })).filter((x) => x.n);
        const ns = notas(c, e);
        out.push({
          id: L.k + ":" + c.id, ev: e.id, k: L.k, cat: L.cat, liga: L.nome, tipo: "corrida",
          t: c.date || c.startDate || e.date, st: status(c.status), tit: (e.shortName || e.name) + " — " + nomeS,
          gp: e.name, sessao: nomeS, local: circ.fullName || "", cid: [circ.address && circ.address.city, circ.address && circ.address.country].filter(Boolean).join(", "),
          tv: tvs(c), obs: ns, fase: "", top, link: linkEv(e), w: peso(L.p, "", corrida ? 40 : -25),
        });
      });
    });
    return out;
  }

  function nomeAtleta(x) {
    const a = x.athlete || {};
    const pais = a.flag && a.flag.alt ? a.flag.alt : "";
    return { n: a.displayName || a.fullName || (x.roster && x.roster.shortDisplayName) || "", pais: tr(pais), v: !!x.winner,
      sets: (x.linescores || []).map((s) => (s.value != null ? String(Math.round(s.value)) : "") + (s.tiebreak != null ? "(" + s.tiebreak + ")" : "")).filter(Boolean) };
  }
  function lerTenis(L, j) {
    const out = [];
    (j.events || []).forEach((e) => {
      (e.groupings || []).forEach((g) => {
        const slug = (g.grouping && g.grouping.slug) || "";
        (g.competitions || []).forEach((c) => {
          const rodada = (c.round && c.round.displayName) || "";
          if (/qualif/i.test(rodada)) return;
          const dupla = /doubles/.test(slug);
          const f = fase([rodada]);
          if (dupla && f !== "final") return;
          const cs = (c.competitors || []).slice().sort((x, y) => (x.order || 0) - (y.order || 0));
          const p1 = nomeAtleta(cs[0] || {}), p2 = nomeAtleta(cs[1] || {});
          if (!p1.n && !p2.n) return;
          const extra = (/finals/i.test(e.name) ? 25 : 0) + (e.major ? 25 : 0) + (/Brazil|Brasil/i.test(p1.pais + p2.pais) ? 30 : 0);
          out.push({
            id: L.k + ":" + c.id, ev: e.id, k: L.k, cat: L.cat, liga: L.nome + " · " + (e.shortName || e.name), tipo: "tenis",
            t: c.date || c.startDate, st: status(c.status), p1, p2, tit: (p1.n || "A definir") + " x " + (p2.n || "A definir"),
            rodada: rodada + (dupla ? " (duplas)" : ""), local: (c.venue && c.venue.fullName) || "", quadra: (c.venue && c.venue.court) || "",
            tv: tvs(c), obs: notas(c, {}), fase: f, link: linkEv(e), w: peso(L.p, f, extra),
          });
        });
      });
    });
    return out;
  }

  function lerMMA(L, j) {
    const out = [];
    (j.events || []).forEach((e) => {
      const lutas = (e.competitions || []).map((c) => {
        const cs = c.competitors || [];
        const a = cs[0] || {}, b = cs[1] || {};
        const nm = (x) => ({ n: (x.athlete && (x.athlete.displayName || x.athlete.fullName)) || "", pais: tr(x.athlete && x.athlete.flag && x.athlete.flag.alt), rec: ((x.records || [])[0] || {}).summary || "", v: !!x.winner });
        return { cat: (c.type && c.type.abbreviation) || "", a: nm(a), b: nm(b), st: status(c.status), t: c.date };
      });
      const principal = lutas[lutas.length - 1];
      const c0 = (e.competitions || [])[0] || {};
      const venue = c0.venue || {};
      const br = lutas.some((l) => /Brazil|Brasil/.test(l.a.pais + l.b.pais)) ? 15 : 0;
      out.push({
        id: L.k + ":" + e.id, ev: e.id, k: L.k, cat: L.cat, liga: L.nome, tipo: "mma",
        t: e.date, st: status(e.status), tit: e.name, principal, lutas: lutas.slice().reverse(),
        local: venue.fullName || "", cid: [venue.address && venue.address.city, venue.address && venue.address.country].filter(Boolean).join(", "),
        tv: tvs(c0), obs: [], fase: /^UFC \d+/.test(e.name || "") ? "" : "", link: linkEv(e), w: peso(L.p, "", (/^UFC \d+/.test(e.name || "") ? 20 : 0) + br),
      });
    });
    return out;
  }

  function lerGolfe(L, j) {
    const out = [];
    (j.events || []).forEach((e) => {
      const c = (e.competitions || [])[0] || {};
      const top = (c.competitors || []).slice().sort((x, y) => (x.order || 999) - (y.order || 999)).slice(0, 5)
        .map((x) => ({ n: (x.athlete && x.athlete.displayName) || "", pl: x.score && typeof x.score === "object" ? x.score.displayValue : x.score })).filter((x) => x.n);
      out.push({
        id: L.k + ":" + e.id, ev: e.id, k: L.k, cat: L.cat, liga: L.nome, tipo: "golfe",
        t: e.date, fimT: e.endDate || "", st: status(e.status || c.status), tit: e.name, top,
        local: (c.venue && c.venue.fullName) || "", tv: tvs(c), obs: [], fase: "", link: linkEv(e), w: peso(L.p, "", (e.major ? 40 : 0)),
      });
    });
    return out;
  }

  function lerEspn(k, j) {
    const L = LIGA_POR_K[k]; if (!L || !j) return [];
    try {
      if (L.tipo === "corrida") return lerCorrida(L, j);
      if (L.tipo === "tenis") return lerTenis(L, j);
      if (L.tipo === "mma") return lerMMA(L, j);
      if (L.tipo === "golfe") return lerGolfe(L, j);
      return lerTime(L, j);
    } catch (err) { return []; }
  }

  function lerTsdb(cfg, j) {
    const out = [];
    ((j && j.events) || []).forEach((e) => {
      const liga = e.strLeague || "";
      if (!cfg.filtro(liga)) return;
      let t = e.strTimestamp ? e.strTimestamp.replace(" ", "T") : (e.dateEvent + "T" + (e.strTime || "00:00:00"));
      if (!/Z|[+-]\d\d:?\d\d$/.test(t)) t += "Z";
      const fim = /FT|Match Finished|Finished|AET|Final/i.test(e.strStatus || "") || (e.intHomeScore != null && e.intHomeScore !== "" && new Date(t) < Date.now() - 3 * 3600e3);
      const aoVivo = /live|in progress|set \d|1st|2nd|3rd|4th|5th/i.test(e.strStatus || "") && !fim;
      const f = fase([e.strEvent, e.intRound === "500" ? "final" : "", e.strRound]);
      const temTimes = e.strHomeTeam && e.strAwayTeam;
      const casa = { n: tr(e.strHomeTeam || ""), logo: e.strHomeTeamBadge || "", pl: e.intHomeScore != null ? String(e.intHomeScore) : "" };
      const fora = { n: tr(e.strAwayTeam || ""), logo: e.strAwayTeamBadge || "", pl: e.intAwayScore != null ? String(e.intAwayScore) : "" };
      const extra = /Brazil|Brasil|Superliga|Brasileir/i.test(liga + e.strHomeTeam + e.strAwayTeam) ? 30 : 0;
      out.push({
        id: "tsdb:" + e.idEvent, ev: e.idEvent, k: "tsdb:" + cfg.s, cat: cfg.cat, liga: liga, tipo: temTimes ? "time" : "corrida",
        t, st: { e: fim ? "post" : aoVivo ? "in" : "pre", txt: e.strStatus && e.strStatus !== "NS" && e.strStatus !== "Not Started" ? e.strStatus : "", fim },
        casa: temTimes ? casa : null, fora: temTimes ? fora : null, tit: temTimes ? casa.n + " x " + fora.n : e.strEvent,
        sessao: temTimes ? "" : e.strEvent, local: e.strVenue || "", cid: [e.strCity, e.strCountry].filter(Boolean).join(", "),
        tv: [], obs: [e.strRound && e.strRound !== "0" ? "Rodada " + e.strRound : ""].filter(Boolean), fase: f, link: "", fonte: "TheSportsDB",
        w: peso(cfg.p, f, extra),
      });
    });
    return out;
  }

  const api = { ESPN, CATS, LIGAS, LIGA_POR_K, TSDB_ESPORTES, diaET, diaBR, urlEspn, urlTsdb, lerEspn, lerTsdb, fase, tr };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.Nucleo = api;
})(typeof self !== "undefined" ? self : this);
