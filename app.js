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
const $=id=>document.getElementById(id);
const wd=['dom','seg','ter','qua','qui','sex','sáb'];
const WD=['Domingo','Segunda','Terça','Quarta','Quinta','Sexta','Sábado'];
const pad=n=>String(n).padStart(2,'0');
const fmt=(v,d=1)=>v==null?'—':Number(v).toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d});
const mmTxt=v=>v<0.5?'0':(v<10?fmt(v):fmt(v,0));
const sameDay=(a,b)=>a.getFullYear()===b.getFullYear()&&a.getMonth()===b.getMonth()&&a.getDate()===b.getDate();
const now=new Date(), tmw=new Date(now.getTime()+864e5);
const dayName=d=>sameDay(d,now)?'Hoje':sameDay(d,tmw)?'Amanhã':wd[d.getDay()];
$('reload').addEventListener('click',()=>location.reload());

let L,O;
try{[L,O]=await Promise.all([coletar(),fetch('oct.json?v='+Date.now(),{cache:'no-store'}).then(r=>r.json())]);}
catch(e){$('stamp').textContent='Sem conexão com os serviços de tempo';$('hero').outerHTML='<div class="err">Não foi possível buscar a previsão agora. Verifique a internet e toque em ↻.</div>';return;}

/* carimbo */
const g=new Date(L.gen);$('stamp').textContent='Atualizado às '+pad(g.getHours())+'h'+pad(g.getMinutes())+' · '+WD[g.getDay()]+', '+g.getDate()+'/'+(g.getMonth()+1);

/* avisos */
const todayKey=now.getFullYear()+'-'+pad(now.getMonth()+1)+'-'+pad(now.getDate());
const col={amarelo:'var(--amarelo)',laranja:'var(--laranja)',vermelho:'var(--vermelho)'};
const dl=s=>{const x=new Date(s+'T12:00:00');return dayName(x).toLowerCase()==='hoje'?'hoje':(dayName(x)==='Amanhã'?'amanhã':wd[x.getDay()]+' '+x.getDate());};
$('alerts').innerHTML=(L.alerts||[]).filter(a=>a.fim>=todayKey).map(a=>`<details class="chip"><summary><i class="dot" style="background:${col[a.lvl]||col.amarelo}"></i>${a.tit[0].toUpperCase()+a.tit.slice(1)} · ${a.ini===a.fim?dl(a.ini):dl(a.ini)+'–'+dl(a.fim)}</summary><p>Aviso ${a.lvl} do INMET. ${a.txt}</p></details>`).join('');

/* horas */
const H=L.H, n=H.mm.length, st=new Date(H.start+':00');
const hrs=[...Array(n)].map((_,i)=>new Date(st.getTime()+i*3600e3));
const wins=[];let cur=null;
for(let i=0;i<n;i++){if(H.p[i]>=50){if(!cur)cur={a:i,b:i};else cur.b=i;}else if(cur){wins.push(cur);cur=null;}}if(cur)wins.push(cur);
const winMm=w=>{let s=0,p=0;for(let i=w.a;i<=w.b;i++){s+=H.mm[i]||0;p=Math.max(p,H.p[i]);}return{s,p};};

/* resumo */
const dIdx=k=>L.D.findIndex(d=>d[0]===k);
const key=d=>d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());
const box=(lab,d)=>{if(!d)return'';return `<div class="box"><span>${lab}</span><b>${mmTxt(d[1])} mm</b><span>${d[4]??'—'}% de chance</span></div>`;};
let head,sub,lab;
const sig=wins.filter(w=>winMm(w).s>=1);
if(wins.length){const w=sig[0]||wins[0],a=hrs[w.a],b=new Date(hrs[w.b].getTime()+3600e3),m=winMm(w);
  const light=!sig.length;
  lab=w.a===0?(light?'Garoa agora':'Chuva agora'):(light?'Próxima garoa':'Próxima chuva');
  head=w.a===0?`Até as ${pad(b.getHours())}h`:`${dayName(a)}, das ${pad(a.getHours())}h às ${pad(b.getHours())}h`;
  sub=`Cerca de ${mmTxt(m.s)} mm · chance de até ${m.p}%`;
  const prev=wins.filter(x=>x.a<w.a);
  if(prev.length)sub+=` · antes disso, garoa fraca ${prev[0].a===0?'agora':'às '+pad(hrs[prev[0].a].getHours())+'h'}`;}
else{const pm=Math.max(...H.p);lab='Próximas 48 horas';head='Sem chuva provável';sub=`Chance máxima de ${pm}% em alguma hora`;}
$('hero').innerHTML=`<div><div class="lab">${lab}</div><p class="head">${head}</p><p class="sub">${sub}</p></div><div class="pair">${box('Hoje',L.D[dIdx(key(now))])}${box('Amanhã',L.D[dIdx(key(tmw))])}</div>`;

const drop=p=>`<svg viewBox="0 0 20 24" aria-hidden="true"><path d="M10 1.5C10 1.5 2.5 10.2 2.5 15a7.5 7.5 0 0 0 15 0C17.5 10.2 10 1.5 10 1.5z" fill="var(--rain)" fill-opacity="${(0.08+0.92*p/100).toFixed(2)}" stroke="var(--rain)" stroke-width="1.2"/></svg>`;
const hmax=Math.max(4,...H.mm.map(v=>v||0));
$('hours').innerHTML=hrs.map((d,i)=>{const p=H.p[i]??0,v=H.mm[i]||0,nd=d.getHours()===0&&i>0;
  const t=i===0?'Agora':pad(d.getHours())+'h';
  return `<div class="h${nd?' newday':''}" role="listitem" aria-label="${dayName(d)} ${pad(d.getHours())}h: ${p}% de chance, ${fmt(v)} mm"><div class="t">${nd?`<b>${dayName(d)}</b>`:''}${t}</div>${drop(p)}<div class="p" style="color:${p>=50?'var(--rain)':'var(--muted)'}">${p}%</div><div class="bar"><i style="height:${Math.round(100*Math.min(v,hmax)/hmax)}%"></i></div><div class="mm">${v>=0.2?mmTxt(v):''}</div><div class="deg">${H.t[i]??''}°</div></div>`;}).join('');

/* dias */
const S=Math.min(60,Math.max(20,...L.D.map(d=>d[3]||0)));
const pos=v=>Math.min(100,100*(v||0)/S);
$('days').innerHTML=L.D.map(d=>{const dt=new Date(d[0]+'T12:00:00'),P=d[4];
  return `<div class="day"><div class="n">${dayName(dt)}<small>${dt.getDate()}/${dt.getMonth()+1}</small></div><div class="c${P<40?' lo':''}">${P??'—'}%</div><div class="track" title="Entre ${fmt(d[2],0)} e ${fmt(d[3],0)} mm conforme o modelo"><span class="rng" style="left:${pos(d[2])}%;width:${Math.max(2,pos(d[3])-pos(d[2]))}%"></span><span class="val" style="left:${pos(d[1])}%"></span></div><div class="v">${mmTxt(d[1])}<small> mm</small></div><div class="tmp">${d[10]}° a ${d[9]}°${d[6]>=20?` · ${d[6]}% de chance de passar de 25 mm`:''}</div></div>`;}).join('')+
 `<div class="legend"><span><i class="sw" style="width:10px;height:10px;border-radius:50%;background:var(--rain)"></i>estimativa (mm)</span><span><i class="sw" style="width:16px;height:6px;border-radius:3px;background:var(--rain-2);opacity:.6"></i>variação entre os modelos</span><span>% = chance de chover</span></div>`;

/* outubro */
const oc=O.oct, W=O.fc.weights, names=oc.names;
const short={EC:'ECMWF',AI:'ECMWF IA',GF:'GFS (EUA)',IC:'ICON (Alemanha)',MF:'Météo-France',UK:'UK Met Office',JM:'JMA (Japão)',GE:'GEM (Canadá)',CM:'CMA (China)',BM:'Best Match'};
const real=oc.res.EC.d1.all.sumo;
let base='gauge', model='CM';
const ab=Object.keys(names);
function rankHTML(){const rows=ab.map(k=>({k,v:oc.res[k].d1[base].mae,acc:oc.res[k].d1[base].acc})).sort((a,b)=>a.v-b.v);const mx=rows[rows.length-1].v;
  return rows.map((r,i)=>`<div class="rk${i===0?' best':''}"><span class="nm">${short[r.k]}</span><span class="bt"><i style="width:${Math.max(4,100*r.v/mx)}%"></i></span><span class="vl">${fmt(r.v)} mm</span></div>`).join('');}
function chartHTML(){const fc=oc.models[model].d1, tr=oc.truth;
  const Wd=620,Hd=220,ml=30,mr=6,mt=22,mb=28,iw=Wd-ml-mr,ih=Hd-mt-mb,bw=iw/31;
  const top=Math.max(10,Math.ceil(Math.max(...tr,...fc)/10)*10), y=v=>mt+ih-ih*v/top;
  let s=`<svg viewBox="0 0 ${Wd} ${Hd}" role="img" aria-label="Chuva real e prevista por ${names[model]} em outubro">`;
  const x0=ml+21*bw;s+=`<rect x="${x0}" y="${mt-18}" width="${iw-21*bw}" height="${ih+18}" fill="var(--rain-3)" opacity=".45" rx="6"/><text x="${x0+6}" y="${mt-6}" font-size="11" fill="var(--muted)">medido no pluviômetro</text>`;
  const step=top>40?20:10;for(let t=0;t<=top;t+=step)s+=`<line x1="${ml}" x2="${Wd-mr}" y1="${y(t)}" y2="${y(t)}" stroke="var(--line)"/><text x="${ml-5}" y="${y(t)+4}" font-size="10.5" text-anchor="end" fill="var(--muted)">${t}</text>`;
  for(let i=0;i<31;i++){const x=ml+i*bw;
    s+=`<rect x="${x+bw*.1}" y="${y(tr[i])}" width="${bw*.38}" height="${mt+ih-y(tr[i])}" rx="1.5" fill="var(--rain)"><title>${i+1}/10 · real ${fmt(tr[i])} mm</title></rect>`;
    s+=`<rect x="${x+bw*.52}" y="${y(fc[i])}" width="${bw*.38}" height="${mt+ih-y(fc[i])}" rx="1.5" fill="var(--bad)" fill-opacity=".75"><title>${i+1}/10 · previsto ${fmt(fc[i])} mm</title></rect>`;
    if(i%5===0||i===30)s+=`<text x="${x+bw/2}" y="${Hd-10}" font-size="10.5" text-anchor="middle" fill="var(--muted)">${i+1}</text>`;}
  return s+'</svg>';}
function verdict(){const r=oc.res[model].d1.all,g=oc.res[model].d1.gauge,d=Math.round((r.sumf/r.sumo-1)*100);
  return `No mês choveu <b>${fmt(r.sumo,0)} mm</b> e o ${short[model]} previu <b>${fmt(r.sumf,0)} mm</b> (${d>=0?'+':''}${d}%). Acertou se ia chover ou não em <b>${Math.round(r.acc*100)}%</b> dos dias. No período do pluviômetro, errou em média <b>${fmt(g.mae)} mm</b> por dia.`;}
$('auditBody').innerHTML=`<ul class="takeaways">
<li>Os modelos acertam bem <b>se</b> vai chover: 74% a 84% dos dias, com a previsão da véspera.</li>
<li>Eles <b>exageram o volume</b>: todos previram mais chuva que o real (${fmt(real,0)} mm no mês). Alguns quase o dobro.</li>
<li>No pluviômetro (22 a 31/10), o <b>CMA</b> foi o mais preciso. Por isso ele tem o maior peso na previsão.</li></ul>
<p class="sub-h">Erro médio por dia (quanto menor, melhor)</p><p class="sub-p">Previsão feita na véspera.</p>
<div class="seg" role="group" aria-label="Base de comparação"><button type="button" data-b="gauge" aria-pressed="true">Pluviômetro (22–31)</button><button type="button" data-b="all" aria-pressed="false">Mês todo</button></div>
<div class="rank" id="rank"></div>
<p class="sub-h">Dia a dia: real × previsto</p>
<select id="selModel" aria-label="Modelo">${ab.map(k=>`<option value="${k}">${names[k]}</option>`).join('')}</select>
<div class="legend"><span><i class="sw" style="width:10px;height:10px;border-radius:2px;background:var(--rain)"></i>choveu (real)</span><span><i class="sw" style="width:10px;height:10px;border-radius:2px;background:var(--bad);opacity:.75"></i>previsto na véspera</span></div>
<div class="chartbox" id="ochart"></div><p class="verdict" id="verdict"></p>`;
const sel=$('selModel');sel.value=model;
const draw=()=>{$('rank').innerHTML=rankHTML();$('ochart').innerHTML=chartHTML();$('verdict').innerHTML=verdict();};
sel.addEventListener('change',()=>{model=sel.value;draw();});
document.querySelectorAll('.seg button').forEach(b=>b.addEventListener('click',()=>{base=b.dataset.b;document.querySelectorAll('.seg button').forEach(x=>x.setAttribute('aria-pressed',x===b?'true':'false'));draw();}));
draw();
})();
