async function coletar(){
const W={ecmwf_ifs025:.122,ecmwf_aifs025_single:.14,gfs_seamless:.072,icon_seamless:.1,meteofrance_seamless:.081,ukmo_seamless:.062,jma_seamless:.076,gem_seamless:.087,cma_grapes_global:.163,best_match:.097};
const B="latitude=-23.42&longitude=-51.94&timezone=America/Sao_Paulo";
const get=async u=>{for(let k=0;k<3;k++){try{const ac=new AbortController();setTimeout(()=>ac.abort(),30000);const r=await fetch(u,{signal:ac.signal});if(r.ok)return r.json();}catch(e){} await new Promise(r=>setTimeout(r,2000));} throw new Error("falhou: "+u.slice(8,40));};
const f=await get(`https://api.open-meteo.com/v1/forecast?${B}&hourly=precipitation,temperature_2m&models=${Object.keys(W)}&forecast_days=10`);
const e=await get(`https://ensemble-api.open-meteo.com/v1/ensemble?${B}&hourly=precipitation&models=ecmwf_ifs025,gfs025,icon_seamless&forecast_days=10`);
const T=f.hourly.time, r1=x=>Math.round(x*10)/10;
const mk=Object.keys(e.hourly).filter(k=>k.startsWith("precipitation"));
const ei=Object.fromEntries(e.hourly.time.map((t,i)=>[t,i]));
const pad=n=>String(n).padStart(2,"0"), d0=new Date();
const nowKey=`${d0.getFullYear()}-${pad(d0.getMonth()+1)}-${pad(d0.getDate())}T${pad(d0.getHours())}:00`;
const s=Math.max(0,T.indexOf(nowKey));
const H={start:T[s],mm:[],mx:[],p:[],t:[]};
for(let i=s;i<s+48&&i<T.length;i++){let n=0,d=0,mx=0,tt=0,td=0;
 for(const m in W){const x=f.hourly["precipitation_"+m]?.[i]; if(x!=null){n+=W[m]*x;d+=W[m];mx=Math.max(mx,x);} const y=f.hourly["temperature_2m_"+m]?.[i]; if(y!=null){tt+=W[m]*y;td+=W[m];}}
 let c=0,k=0; const j=ei[T[i]]; for(const q of mk){const x=e.hourly[q][j]; if(x==null)continue;k++; if(x>=0.2)c++;}
 H.mm.push(d?r1(n/d):null); H.mx.push(r1(mx)); H.p.push(k?Math.round(100*c/k):null); H.t.push(td?Math.round(tt/td):null);}
const dates=[...new Set(T.map(t=>t.slice(0,10)))].slice(0,10), D=[];
for(const day of dates){const idx=T.map((t,i)=>t.startsWith(day)?i:-1).filter(i=>i>=0);
 let n=0,d=0,v=[],tx=-99,tn=99;
 for(const m in W){const a=idx.map(i=>f.hourly["precipitation_"+m]?.[i]); if(a.some(x=>x==null))continue; const sm=a.reduce((x,y)=>x+y,0); n+=W[m]*sm; d+=W[m]; v.push(sm);}
 idx.forEach(i=>{let tt=0,td=0; for(const m in W){const y=f.hourly["temperature_2m_"+m]?.[i]; if(y!=null){tt+=W[m]*y;td+=W[m];}} if(td){tx=Math.max(tx,tt/td);tn=Math.min(tn,tt/td);}});
 const sums=[]; for(const q of mk){const a=idx.map(i=>e.hourly[q][ei[T[i]]]); if(a.some(x=>x==null))continue; sums.push(a.reduce((x,y)=>x+y,0));}
 const pr=t=>sums.length?Math.round(100*sums.filter(x=>x>=t).length/sums.length):null;
 D.push([day,d?r1(n/d):null,v.length?r1(Math.min(...v)):null,v.length?r1(Math.max(...v)):null,pr(1),pr(10),pr(25),pr(50),sums.length,Math.round(tx),Math.round(tn)]);}
let A=[];try{const ac=new AbortController();setTimeout(()=>ac.abort(),20000);const j=await fetch("https://apiprevmet3.inmet.gov.br/avisos/ativos",{signal:ac.signal}).then(r=>r.json());
 const lv={"Perigo Potencial":"amarelo","Perigo":"laranja","Grande Perigo":"vermelho"};
 const L=[...(j.hoje||[]),...(j.futuro||[])].filter(a=>/(^|,\s*)Maring[aá]\s*-\s*PR/i.test(a.municipios||"")).map(a=>({lvl:lv[a.severidade]||"amarelo",tit:String(a.descricao).toLowerCase(),ini:a.data_inicio.slice(0,10),fim:a.data_fim.slice(0,10),txt:String(Array.isArray(a.riscos)?a.riscos[0]:a.riscos).split(/\.\s+(Baixo r|R)isco/)[0].replace(/\.$/,"")+"."})).sort((a,b)=>a.ini<b.ini?-1:1);
 for(const a of L){const p=A.find(x=>x.lvl===a.lvl&&x.tit===a.tit&&x.txt===a.txt&&(new Date(a.ini)-new Date(x.fim))<=864e5);if(p){if(a.fim>p.fim)p.fim=a.fim;}else A.push({...a});}}catch(e){A=null}
return {gen:new Date().toISOString(),H,D,alerts:A||[]};

}
(async function(){
const ld=async u=>{const r=await fetch(u+'?v='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error(u);return r.json();};
document.getElementById('stamp').textContent='Buscando a previsão mais recente…';
let DATA,LIVE_;try{[DATA,LIVE_]=await Promise.all([ld('oct.json'),coletar()]);}catch(e){document.getElementById('stamp').textContent='Não foi possível buscar a previsão agora. Verifique a internet e recarregue.';return;}
const O=DATA.oct, F=DATA.fc;
const names=O.names;
const order=['CM','AI','EC','IC','BM','GE','MF','JM','GF','UK'];
const fmt=(v,d=1)=>v==null?'—':v.toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d});
const pct=v=>v==null?'—':Math.round(v*100)+'%';
const LIVE=LIVE_;
const wd=['dom','seg','ter','qua','qui','sex','sáb'];
const pad=n=>String(n).padStart(2,'0');
const todayKey=(()=>{const d=new Date(Date.now()-3*3600e3);return d.toISOString().slice(0,10);})(); /* data em Brasília */
/* carimbo */
(function(){const g=new Date(LIVE.gen);const h=(Date.now()-g)/3600e3;const b=new Date(g.getTime()-3*3600e3);
 const el=document.getElementById('stamp');if(h>12)el.classList.add('old');
 const rel=h<1?'há menos de 1 hora':(h<48?'há '+Math.round(h)+' h':'há '+Math.round(h/24)+' dias');
 el.innerHTML=`<i class="dot"></i><span>Atualizado em ${pad(b.getUTCDate())}/${pad(b.getUTCMonth()+1)} às ${pad(b.getUTCHours())}h${pad(b.getUTCMinutes())} (${rel})${h>12?' · os dados podem estar desatualizados':''}</span>`;})();
/* alertas */
(function(){const box=document.getElementById('alerts');(LIVE.alerts||[]).filter(a=>a.fim>=todayKey).forEach(a=>{const d=document.createElement('div');d.className='alert '+(a.lvl==='amarelo'?'amarelo':'');d.setAttribute('role','note');
 const dl=s=>{const x=new Date(s+'T12:00:00');return wd[x.getDay()]+' '+x.getDate()+'/'+(x.getMonth()+1);};
 d.innerHTML=`<b>Aviso INMET (${a.lvl}): ${a.tit} · ${a.ini===a.fim?dl(a.ini):dl(a.ini)+' a '+dl(a.fim)}</b><span>${a.txt}</span>`;box.appendChild(d);});
 if(box.children.length){const s=document.createElement('small');s.className='note';s.textContent='Defesa Civil 199 · Bombeiros 193';box.appendChild(s);}})();
/* hora a hora */
(function(){const H=LIVE.H;const st=new Date(H.start+':00');const n=H.mm.length;
 const hrs=[...Array(n)].map((_,i)=>new Date(st.getTime()+i*3600e3));
 /* janelas: horas com chance >=50% agrupadas */
 const wins=[];let cur=null;for(let i=0;i<n;i++){if(H.p[i]>=50){if(!cur)cur={a:i,b:i};else cur.b=i;}else if(cur){wins.push(cur);cur=null;}}if(cur)wins.push(cur);
 const lab=d=>{const k=d.toISOString().slice(0,10);const dd=new Date(d.getTime());const today=new Date();const sameDay=(x,y)=>x.getFullYear()===y.getFullYear()&&x.getMonth()===y.getMonth()&&x.getDate()===y.getDate();
   const tm=new Date(today.getTime()+864e5);return sameDay(dd,today)?'Hoje':sameDay(dd,tm)?'Amanhã':wd[dd.getDay()]+' '+dd.getDate()+'/'+(dd.getMonth()+1);};
 const ul=document.getElementById('windows');
 if(!wins.length){ul.innerHTML='<li><b>Sem janela de chuva provável</b><span>Nenhuma hora com chance de 50% ou mais nas próximas 48 h.</span></li>';}
 wins.forEach(w=>{const a=hrs[w.a],b=new Date(hrs[w.b].getTime()+3600e3);let mm=0,pmax=0;for(let i=w.a;i<=w.b;i++){mm+=H.mm[i]||0;pmax=Math.max(pmax,H.p[i]);}
   const li=document.createElement('li');li.innerHTML=`<b>${lab(a)}, ${pad(a.getHours())}h às ${pad(b.getHours())}h</b><span>chance até ${pmax}% · ~${fmt(mm)} mm no período</span>`;ul.appendChild(li);});
 /* gráfico */
 const W=Math.max(640,n*16+50),Hh=230,ml=34,mr=8,mt=26,mb=40,iw=W-ml-mr,ih=Hh-mt-mb;const top=Math.max(4,Math.ceil(Math.max(...H.mx,...H.mm)/2)*2);
 const y=v=>mt+ih-(v/top)*ih,bw=iw/n;
 let s=`<svg viewBox="0 0 ${W} ${Hh}" style="min-width:${W}px" role="img" aria-label="Chuva prevista hora a hora nas próximas 48 horas">`;
 const step=top>12?4:2;for(let t=0;t<=top;t+=step)s+=`<line x1="${ml}" x2="${W-mr}" y1="${y(t)}" y2="${y(t)}" stroke="var(--line)"/><text x="${ml-6}" y="${y(t)+4}" text-anchor="end" font-size="10.5" fill="var(--muted)" font-family="IBM Plex Mono,monospace">${t}</text>`;
 for(let i=0;i<n;i++){const x=ml+i*bw;const p=H.p[i]??0;
   s+=`<rect x="${x+1}" y="4" width="${bw-2}" height="12" rx="2" fill="var(--rain)" fill-opacity="${(0.06+0.94*p/100).toFixed(2)}"><title>${pad(hrs[i].getHours())}h: chance ${p}%</title></rect>`;
   const v=H.mm[i]||0;s+=`<rect x="${x+bw*.18}" y="${y(v)}" width="${bw*.64}" height="${Math.max(0,mt+ih-y(v))}" rx="1.5" fill="var(--rain)"><title>${lab(hrs[i])} ${pad(hrs[i].getHours())}h: ${fmt(v)} mm (máx. entre modelos ${fmt(H.mx[i])} mm), chance ${p}%, ${H.t[i]}°C</title></rect>`;
   if(H.mx[i]>v)s+=`<line x1="${x+bw*.2}" x2="${x+bw*.8}" y1="${y(H.mx[i])}" y2="${y(H.mx[i])}" stroke="var(--ink)" stroke-width="1.4"/>`;
   const hh=hrs[i].getHours();if(hh%3===0)s+=`<text x="${x+bw/2}" y="${Hh-mb+14}" text-anchor="middle" font-size="10.5" fill="var(--muted)" font-family="IBM Plex Mono,monospace">${pad(hh)}h</text>`;
   if(hh===0&&i>0)s+=`<line x1="${x}" x2="${x}" y1="${mt}" y2="${Hh-mb+20}" stroke="var(--muted)" stroke-dasharray="3 3"/><text x="${x+4}" y="${Hh-6}" font-size="11" font-weight="600" fill="var(--ink)">${lab(hrs[i])}</text>`;}
 s+=`<text x="${ml}" y="${Hh-6}" font-size="11" font-weight="600" fill="var(--ink)">${lab(hrs[0])}</text><text x="${ml}" y="${mt-4}" font-size="0">.</text></svg>`;
 document.getElementById('hchart').innerHTML=s;})();
/* 10 dias */
const daysEl=document.getElementById('days');
LIVE.D.forEach(([d,mm,mn,mx,P,P10,P25,P50,n,tx,tn],i)=>{
  const dt=new Date(d+'T12:00:00');
  const row=document.createElement('div');
  row.className='day'+(mm>=20?' hot':'');
  const label=d===todayKey?'Hoje':(i===1&&LIVE.D[0][0]===todayKey?'Amanhã':wd[dt.getDay()]);
  row.innerHTML=`<div class="dname">${label}<small>${dt.getDate()}/${dt.getMonth()+1} · ${tn}–${tx}°</small></div>
   <div class="prob">
     <div class="pbar" aria-hidden="true"><i style="width:${P==null?0:P}%"></i></div>
     <div class="pmeta"><span><b>${P==null?'—':P+'%'}</b> chance de chuva</span>${P10>=10?`<span>≥10 mm: <b>${P10}%</b></span>`:''}${P25>=10?`<span>≥25 mm: <b>${P25}%</b></span>`:''}${P50>=5?`<span>≥50 mm: <b>${P50}%</b></span>`:''}</div>
   </div>
   <div class="mm">${fmt(mm)}<small>${fmt(mn,0)}–${fmt(mx,0)} mm</small></div>`;
  daysEl.appendChild(row);
});

/* ---------- october ---------- */
let model='CM', lead='d1';
const sel=document.getElementById('selModel');
order.forEach(ab=>{const o=document.createElement('option');o.value=ab;o.textContent=names[ab];sel.appendChild(o);});
sel.value=model;
sel.addEventListener('change',()=>{model=sel.value;renderOct();});
document.querySelectorAll('.seg button').forEach(b=>b.addEventListener('click',()=>{
  lead=b.dataset.lead;document.querySelectorAll('.seg button').forEach(x=>x.setAttribute('aria-pressed',x===b?'true':'false'));renderOct();renderRank();}));

const cssv=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function renderOct(){
  const r=O.res[model][lead].all, g=O.res[model][lead].gauge;
  const st=document.getElementById('stats');
  st.innerHTML=[
    [pct(r.acc),'acerto chove/não chove (31 dias)'],
    [r.miss+' / '+r.fa,'chuvas perdidas / alarmes falsos'],
    [fmt(r.mae)+' mm','erro médio por dia'],
    [fmt(r.sumf,0)+' / '+fmt(r.sumo,0),'mm no mês: previsto / real'],
    [fmt(g.mae)+' mm','erro médio, só pluviômetro (22–31)'],
  ].map(([v,k])=>`<div class="stat"><span class="v">${v}</span><span class="k">${k}</span></div>`).join('');
  drawChart();
}
function drawChart(){
  const truth=O.truth, src=O.src, fc=O.models[model][lead];
  const W=760,H=300,ml=36,mr=10,mt=14,mb=34, iw=W-ml-mr, ih=H-mt-mb;
  const maxV=Math.max(10,...truth.map(v=>v||0),...fc.map(v=>v||0));
  const top=Math.ceil(maxV/10)*10;
  const y=v=>mt+ih-(v/top)*ih, bw=iw/31;
  let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Chuva diária em outubro: medida e prevista por ${names[model]}">`;
  for(let t=0;t<=top;t+=top>60?20:10){s+=`<line x1="${ml}" x2="${W-mr}" y1="${y(t)}" y2="${y(t)}" stroke="var(--line)" stroke-width="1"/><text x="${ml-6}" y="${y(t)+4}" text-anchor="end" font-size="11" fill="var(--muted)" font-family="IBM Plex Mono,monospace">${t}</text>`;}
  truth.forEach((v,i)=>{ if(v==null)return; const x=ml+i*bw+bw*.14, h=ih-(y(v)-mt);
    s+=`<rect x="${x}" y="${y(v)}" width="${bw*.72}" height="${Math.max(0,h)}" rx="2" fill="${src[i]==='INMET'?'var(--rain)':'var(--era)'}"><title>${i+1}/10: ${fmt(v)} mm medidos (${src[i]==='INMET'?'pluviômetro INMET':'ERA5'}) · previsto ${fmt(fc[i])} mm</title></rect>`;});
  let path='';fc.forEach((v,i)=>{if(v==null)return;const x=ml+i*bw+bw/2;path+=(path?'L':'M')+x.toFixed(1)+','+y(v).toFixed(1);});
  s+=`<path d="${path}" fill="none" stroke="var(--ink)" stroke-width="1.6" stroke-linejoin="round"/>`;
  fc.forEach((v,i)=>{if(v==null)return;const x=ml+i*bw+bw/2;s+=`<circle cx="${x}" cy="${y(v)}" r="3.2" fill="var(--surface)" stroke="var(--ink)" stroke-width="1.6"/>`;});
  for(let i=0;i<31;i++){ if(i%2)continue; s+=`<text x="${ml+i*bw+bw/2}" y="${H-mb+16}" text-anchor="middle" font-size="11" fill="var(--muted)" font-family="IBM Plex Mono,monospace">${i+1}</text>`;}
  const xg=ml+21*bw; s+=`<line x1="${xg}" x2="${xg}" y1="${mt}" y2="${mt+ih}" stroke="var(--muted)" stroke-dasharray="3 3"/><text x="${xg+4}" y="${mt+10}" font-size="10.5" fill="var(--muted)" font-family="IBM Plex Mono,monospace">pluviômetro →</text>`;
  s+=`<text x="${ml}" y="${H-4}" font-size="11" fill="var(--muted)">mm por dia · dia de outubro</text></svg>`;
  s+=`<div class="legend"><span><i class="sw" style="background:var(--rain)"></i>Medido no pluviômetro INMET</span><span><i class="sw" style="background:var(--era)"></i>Estimado (ERA5), 1–21/10</span><span><i class="sw" style="background:var(--ink);height:2px;vertical-align:3px"></i>${names[model]}, ${lead.slice(1)} dia${lead==='d1'?'':'s'} antes</span></div>`;
  document.getElementById('chart').innerHTML=s;
}

/* ---------- ranking ---------- */
let sortKey='mae', sortDir=1;
const cols=[
  ['name','Modelo'],['acc','Acerto'],['miss','Perdidas'],['fa','Falsos'],['mae','Erro médio (mm/dia)'],['tot','Total previsto (real '+fmt(O.res.EC.d1.all.sumo,0)+')'],['gacc','Acerto · só pluv.'],['gmae','Erro · só pluv.'],['hcsi','Chuva forte ≥10 mm (acerto)'],['w','Peso na previsão']
];
function cls(k,v,all){ if(v==null)return''; const vals=all.map(r=>r[k]).filter(x=>x!=null).sort((a,b)=>a-b); const lowBetter=['miss','fa','mae','gmae'].includes(k);
  const best=lowBetter?vals[0]:vals[vals.length-1], worst=lowBetter?vals[vals.length-1]:vals[0]; if(v===best)return'g'; if(v===worst)return'b'; return'';}
function renderRank(){
  const rows=order.map(ab=>{const r=O.res[ab][lead];return{ab,name:names[ab],acc:r.all.acc,miss:r.all.miss,fa:r.all.fa,mae:r.all.mae,tot:r.all.sumf,gacc:r.gauge.acc,gmae:r.gauge.mae,hcsi:r.heavy.csi,w:F.weights[ab]};});
  rows.sort((a,b)=>{const x=a[sortKey],z=b[sortKey]; if(typeof x==='string')return x.localeCompare(z)*sortDir; return ((x??1e9)-(z??1e9))*sortDir;});
  const t=document.getElementById('rank');
  t.innerHTML='<thead><tr>'+cols.map(([k,l])=>`<th scope="col"><button type="button" data-k="${k}" style="all:unset;cursor:pointer">${l}${sortKey===k?(sortDir>0?' ↑':' ↓'):''}</button></th>`).join('')+'</tr></thead><tbody>'+
   rows.map((r,i)=>`<tr${i===0&&sortKey!=='name'?' class="top"':''}><td>${r.name}</td><td class="${cls('acc',r.acc,rows)}">${pct(r.acc)}</td><td class="${cls('miss',r.miss,rows)}">${r.miss}</td><td class="${cls('fa',r.fa,rows)}">${r.fa}</td><td class="${cls('mae',r.mae,rows)}">${fmt(r.mae)}</td><td>${fmt(r.tot,0)} <span class="sub">(${r.tot>=O.res.EC.d1.all.sumo?'+':''}${Math.round((r.tot/O.res.EC.d1.all.sumo-1)*100)}%)</span></td><td class="${cls('gacc',r.gacc,rows)}">${pct(r.gacc)}</td><td class="${cls('gmae',r.gmae,rows)}">${fmt(r.gmae)}</td><td class="${cls('hcsi',r.hcsi,rows)}">${pct(r.hcsi)}</td><td>${Math.round(r.w*100)}%</td></tr>`).join('')+'</tbody>';
  t.querySelectorAll('th button').forEach(b=>b.addEventListener('click',()=>{const k=b.dataset.k; if(sortKey===k)sortDir*=-1; else{sortKey=k;sortDir=['acc','gacc','hcsi','w'].includes(k)?-1:1;} renderRank();}));
}

/* ---------- findings ---------- */
const F1=O.res;
const totReal=F1.EC.d1.all.sumo;
document.getElementById('findings').innerHTML=[
 `Em outubro choveu cerca de <b>${fmt(totReal,0)} mm</b> em Maringá, somando a estimativa de 1 a 21 com o medido no pluviômetro de 22 a 31.`,
 `Com 1 dia de antecedência, quase todos os modelos acertam <b>se</b> vai chover (74% a 84% dos dias). O que erra é <b>quanto</b>: todos os 10 modelos previram mais chuva do que caiu no mês (o CMA por apenas 1%), e alguns previram quase o dobro (UK Met Office +98%, Météo-France +58%).`,
 `No período com pluviômetro (22 a 31/10) caíram só <b>32 mm</b>, e todos os modelos menos o CMA previram bem mais: de 56 a 129 mm. O caso mais claro é o dia 25: o pluviômetro marcou 2,8 mm, a estimativa ERA5 indicou 36,7 mm e o ECMWF previa 21,6 mm. Foi chuva em parte da região que não passou pela estação.`,
 `<b>ECMWF AIFS</b> e <b>ECMWF IFS</b> lideram no mês inteiro, mas parte dessa vantagem vem de a referência de 1 a 21 ser do próprio ECMWF. No pluviômetro, que é independente, o <b>CMA</b> teve o menor erro (3,2 mm/dia) e <b>ICON, CMA e Météo-France</b> acertaram chove/não chove em 9 de 10 dias.`,
 `Previsão de 3 dias atrás piora pouco no "vai chover ou não", mas o volume fica bem menos confiável. Para decidir algo pelo volume de chuva, confie na previsão da véspera.`
].map(t=>`<li>${t}</li>`).join('');

renderOct();renderRank();
})();
