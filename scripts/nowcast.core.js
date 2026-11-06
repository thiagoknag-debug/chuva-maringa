/* ===== Nowcast (próximos 60–90 min) a partir do radar RainViewer: núcleo sem DOM, usado no site e no teste em Node ===== */
const NC=(()=>{
const Z=7,T=256,N=3*T,LAT=typeof LOC!=='undefined'?LOC.lat:-23.42,LON=typeof LOC!=='undefined'?LOC.lon:-51.94,NOME=typeof LOC!=='undefined'?LOC.nome:'Maringá';
const TAB=[[-10,"63615914"],[-9,"66635a19"],[-8,"69665c1e"],[-7,"6c685d24"],[-6,"6f6b5f29"],[-5,"726e612e"],[-4,"75706234"],[-3,"78736439"],[-2,"7c75653e"],[-1,"7f786744"],[0,"827b6949"],[1,"857d6a4e"],[2,"88806c54"],[3,"8b826d59"],[4,"8e856f5e"],[5,"92887164"],[6,"9e93756e"],[7,"aa9e7978"],[8,"b6a97e82"],[9,"c2b4828c"],[10,"cec08796"],[11,"d2c48ba0"],[12,"d6c88faa"],[13,"dacc93b4"],[14,"ded097be"],[15,"88ddeeff"],[16,"6cd1ebff"],[17,"51c5e8ff"],[18,"36bae5ff"],[19,"1baee2ff"],[20,"00a3e0ff"],[21,"009ad5ff"],[22,"0091caff"],[23,"0088bfff"],[24,"007fb4ff"],[25,"0077aaff"],[26,"0070a3ff"],[27,"00699cff"],[28,"006295ff"],[29,"005b8eff"],[30,"005588ff"],[31,"005180ff"],[32,"004e78ff"],[33,"004a70ff"],[34,"004768ff"],[35,"ffee00ff"],[36,"ffe000ff"],[37,"ffd200ff"],[38,"ffc500ff"],[39,"ffb700ff"],[40,"ffaa00ff"],[41,"ff9f00ff"],[42,"ff9500ff"],[43,"ff8b00ff"],[44,"ff8100ff"],[45,"ff4400ff"],[46,"f23600ff"],[47,"e62800ff"],[48,"d91b00ff"],[49,"cd0d00ff"],[50,"c10000ff"],[51,"a80000ff"],[52,"8f0000ff"],[53,"760000ff"],[54,"5d0000ff"],[55,"ffaaffff"],[56,"ff9fffff"],[57,"ff95ffff"],[58,"ff8bffff"],[59,"ff81ffff"],[60,"ff77ffff"],[61,"ff6cffff"],[62,"ff62ffff"],[63,"ff58ffff"],[64,"ff4effff"],[65,"ffffffff"],[66,"ffffffff"],[67,"ffffffff"],[68,"ffffffff"],[69,"ffffffff"],[70,"ffffffff"],[71,"ffffffff"],[72,"ffffffff"],[73,"ffffffff"],[74,"ffffffff"],[75,"00ff00ff"],[76,"00ff00ff"],[77,"00ff00ff"],[78,"00ff00ff"],[79,"00ff00ff"],[80,"00ff00ff"],[81,"00ff00ff"],[82,"00ff00ff"],[83,"00ff00ff"],[84,"00ff00ff"],[85,"00ff00ff"],[86,"00ff00ff"],[87,"00ff00ff"],[88,"00ff00ff"],[89,"00ff00ff"],[90,"00ff00ff"],[91,"00ff00ff"],[92,"00ff00ff"],[93,"00ff00ff"],[94,"00ff00ff"],[95,"00ff00ff"],[-9,"ceffff0c"],[-8,"cdffff19"],[-7,"ccffff26"],[-6,"cbffff33"],[-5,"cbffff3f"],[-4,"caffff4c"],[-3,"c9ffff59"],[-2,"c8ffff66"],[-1,"c7ffff72"],[0,"c7ffff7f"],[1,"c6ffff8c"],[2,"c5ffff99"],[3,"c4ffffa5"],[4,"c3ffffb2"],[5,"c3ffffbf"],[6,"c2ffffcc"],[7,"c1ffffd8"],[8,"c0ffffe5"],[9,"bffffff2"],[10,"bfffffff"],[11,"b8f8ffff"],[12,"b2f2ffff"],[13,"abebffff"],[14,"a5e5ffff"],[15,"9fdfffff"],[16,"98d8ffff"],[17,"92d2ffff"],[18,"8bcbffff"],[19,"85c5ffff"],[20,"7fbfffff"],[21,"78b8ffff"],[22,"72b2ffff"],[23,"6babffff"],[24,"65a5ffff"],[25,"5f9fffff"],[26,"5b9bffff"],[27,"5898ffff"],[28,"5595ffff"],[29,"5292ffff"],[30,"4f8fffff"],[31,"4b8bffff"],[32,"4888ffff"],[33,"4585ffff"],[34,"4282ffff"],[35,"3f7fffff"],[36,"3b7bffff"],[37,"3878ffff"],[38,"3575ffff"],[39,"3272ffff"],[40,"2f6fffff"],[41,"2b6bffff"],[42,"2868ffff"],[43,"2565ffff"],[44,"2262ffff"],[45,"1f5fffff"],[46,"1b5bffff"],[47,"1858ffff"],[48,"1555ffff"],[49,"1252ffff"],[50,"0f4fffff"],[51,"0c4bffff"],[52,"0948ffff"],[53,"0645ffff"],[54,"0242ffff"],[55,"003fffff"],[56,"003bffff"],[57,"0038ffff"],[58,"0035ffff"],[59,"0032ffff"],[60,"002fffff"],[61,"002bffff"],[62,"0028ffff"],[63,"0025ffff"],[64,"0022ffff"],[65,"001fffff"],[66,"001bffff"],[67,"0018ffff"],[68,"0015ffff"],[69,"0012ffff"],[70,"000fffff"],[71,"000cffff"],[72,"0009ffff"],[73,"0006ffff"],[74,"0002ffff"],[75,"0000ffff"],[76,"0000ffff"],[77,"0000ffff"],[78,"0000ffff"],[79,"0000ffff"],[80,"0000ffff"],[81,"0000ffff"],[82,"0000ffff"],[83,"0000ffff"],[84,"0000ffff"],[85,"0000ffff"],[86,"0000ffff"],[87,"0000ffff"],[88,"0000ffff"],[89,"0000ffff"],[90,"0000ffff"],[91,"0000ffff"],[92,"0000ffff"],[93,"0000ffff"],[94,"0000ffff"],[95,"0000ffff"]];
const MAPA=new Map();const PAL=[];
for(const [z,h] of TAB){const r=parseInt(h.slice(0,2),16),g=parseInt(h.slice(2,4),16),b=parseInt(h.slice(4,6),16),a=parseInt(h.slice(6,8),16);const k=((r<<24)|(g<<16)|(b<<8)|a)>>>0;if(!MAPA.has(k))MAPA.set(k,z);PAL.push([r,g,b,a,z]);}
const perto=(r,g,b,a)=>{let m=1e9,z=-128;for(const p of PAL){const d=(p[0]-r)**2+(p[1]-g)**2+(p[2]-b)**2+((p[3]-a)**2)/4;if(d<m){m=d;z=p[4];}}return m<600?z:-128;};
const pxDe=(lat,lon)=>{const n=T*2**Z,x=(lon+180)/360*n,s=Math.sin(lat*Math.PI/180),y=(0.5-Math.log((1+s)/(1-s))/(4*Math.PI))*n;return [x,y];};
const [GX,GY]=pxDe(LAT,LON),TX=Math.floor(GX/T),TY=Math.floor(GY/T),PX=GX-(TX-1)*T,PY=GY-(TY-1)*T;
const KM=40075.017*Math.cos(LAT*Math.PI/180)/(T*2**Z); /* km por pixel (~1,12) */
const tiles=()=>{const o=[];for(let j=-1;j<=1;j++)for(let i=-1;i<=1;i++)o.push({x:TX+i,y:TY+j,ox:(i+1)*T,oy:(j+1)*T});return o;};
/* converte um tile RGBA (Uint8ClampedArray 256*256*4) para dBZ na grade 768x768 */
function poeTile(G,rgba,ox,oy){const cache=new Map();for(let y=0;y<T;y++)for(let x=0;x<T;x++){const o=(y*T+x)*4,a=rgba[o+3];if(!a)continue;
  const k=((rgba[o]<<24)|(rgba[o+1]<<16)|(rgba[o+2]<<8)|a)>>>0;let z=MAPA.get(k);if(z===undefined){z=cache.get(k);if(z===undefined){z=perto(rgba[o],rgba[o+1],rgba[o+2],a);cache.set(k,z);}}
  G[(oy+y)*N+ox+x]=z;}}
const novaGrade=()=>new Int8Array(N*N).fill(-128);
/* cobertura: no tile de cobertura, pixel opaco = área SEM radar */
function poeCobertura(C,rgba,ox,oy){for(let y=0;y<T;y++)for(let x=0;x<T;x++)if(rgba[(y*T+x)*4+3]>0)C[(oy+y)*N+ox+x]=1;}
const semRadar=(C,x,y,r)=>{if(!C)return 0;let n=0,s=0;for(let j=Math.floor(y-r);j<=Math.ceil(y+r);j+=2)for(let i=Math.floor(x-r);i<=Math.ceil(x+r);i+=2){if((i-x)**2+(j-y)**2>r*r)continue;n++;if(i<0||j<0||i>=N||j>=N||C[j*N+i])s++;}return n?s/n:1;};
/* deslocamento entre dois quadros (B depois de A) por correlação, em pixels; janela quadrada de meia-largura R em volta de (cx,cy) */
function movimento(A,B,cx,cy,R,S){const D=2,W=Math.floor(2*R/D),x0=Math.round(cx-R),y0=Math.round(cy-R);
  const a=new Float32Array(W*W),b=new Float32Array(W*W);let nA=0,nB=0;
  for(let j=0;j<W;j++)for(let i=0;i<W;i++){let sa=0,sb=0;for(let v=0;v<D;v++)for(let u=0;u<D;u++){const X=x0+i*D+u,Y=y0+j*D+v;if(X<0||Y<0||X>=N||Y>=N)continue;const q=Y*N+X;sa+=Math.min(40,Math.max(0,A[q]-15));sb+=Math.min(40,Math.max(0,B[q]-15));}
    a[j*W+i]=sa;b[j*W+i]=sb;if(sa>0)nA++;if(sb>0)nB++;}
  if(nA<40||nB<40)return null;
  const s=Math.ceil(S/D);let best=-2,bx=0,by=0;const C={};
  for(let dy=-s;dy<=s;dy++)for(let dx=-s;dx<=s;dx++){let sa=0,sb=0,saa=0,sbb=0,sab=0,n=0;
    for(let j=Math.max(0,-dy);j<Math.min(W,W-dy);j++){const ra=j*W,rb=(j+dy)*W;for(let i=Math.max(0,-dx);i<Math.min(W,W-dx);i++){const p=a[ra+i],q=b[rb+i+dx];if(p===0&&q===0)continue;sa+=p;sb+=q;saa+=p*p;sbb+=q*q;sab+=p*q;n++;}}
    const tot=(W-Math.abs(dx))*(W-Math.abs(dy));if(n<20){C[dx+','+dy]=-1;continue;}
    const ma=sa/tot,mb=sb/tot,cov=sab/tot-ma*mb,va=saa/tot-ma*ma,vb=sbb/tot-mb*mb,c=va>0&&vb>0?cov/Math.sqrt(va*vb):-1;C[dx+','+dy]=c;
    if(c>best){best=c;bx=dx;by=dy;}}
  const pf=(m,z,p)=>{const d=m-2*z+p;return d<0?0.5*(m-p)/d:0;};
  const g=(x,y)=>C[x+','+y]??best;
  const fx=bx+(Math.abs(bx)<s?pf(g(bx-1,by),best,g(bx+1,by)):0),fy=by+(Math.abs(by)<s?pf(g(bx,by-1),best,g(bx,by+1)):0);
  return {dx:fx*D,dy:fy*D,c:best,borda:Math.abs(bx)>=s||Math.abs(by)>=s};}
/* amostra um disco no quadro G: fração com chuva (>=20 dBZ) e intensidade típica */
function disco(G,x,y,rp){const r=Math.max(1.5,rp),r2=r*r;let n=0,c=0,c15=0;const zs=[];
  for(let j=Math.floor(y-r);j<=Math.ceil(y+r);j++)for(let i=Math.floor(x-r);i<=Math.ceil(x+r);i++){if((i-x)**2+(j-y)**2>r2)continue;if(i<0||j<0||i>=N||j>=N)continue;n++;const z=G[j*N+i];if(z>=20){c++;zs.push(z);}else if(z>=15)c15++;}
  if(!n)return {p:0,z:null,p15:0};zs.sort((a,b)=>a-b);return {p:c/n,z:zs.length?zs[Math.floor(zs.length*0.75)]:null,p15:(c+c15)/n};}
const cat=z=>z==null?null:z>=55?{k:5,t:'temporal (possível granizo)',c:'#d946ef'}:z>=48?{k:4,t:'muito forte',c:'#dc2626'}:z>=40?{k:3,t:'forte',c:'#f59e0b'}:z>=30?{k:2,t:'moderada',c:'#2563eb'}:{k:1,t:'fraca',c:'#38bdf8'};
const mmh=z=>z==null?0:Math.pow(Math.pow(10,z/10)/200,1/1.6);
/* previsão: quadros [{t (s), G}], velocidade v={vx,vy} px/min, tAgora (s); devolve minuto a minuto (0..90) */
function prever(Q,v,tAgora,alvo,Cv){const [ax,ay]=alvo||[PX,PY];const f0=Q[Q.length-1],f1=Q.length>1?Q[Q.length-2]:null,out=[];
  for(let m=0;m<=90;m++){const L=(tAgora-f0.t)/60+m,rk=(2.5+0.09*L)/KM;
    const a=disco(f0.G,ax-v.vx*L,ay-v.vy*L,rk);let p=a.p,z=a.z,p15=a.p15;
    if(f1){const L1=(tAgora-f1.t)/60+m,b=disco(f1.G,ax-v.vx*L1,ay-v.vy*L1,(2.5+0.09*L1)/KM);p=(2*a.p+b.p)/3;p15=(2*a.p15+b.p15)/3;if(z==null)z=b.z;else if(b.z!=null)z=Math.round((2*z+b.z)/3);}
    out.push({m,p,z,p15,u:semRadar(Cv,ax-v.vx*L,ay-v.vy*L,rk)});}
  return out;}
/* estima o movimento com os últimos quadros; usa o vento em 700 hPa (vento={vx,vy} px/min) se o radar não tiver ecos suficientes */
function velocidade(Q,vento,alvo,R1=130){const [ax,ay]=alvo||[PX,PY];const vs=[];
  for(let k=Math.max(1,Q.length-3);k<Q.length;k++){const dt=(Q[k].t-Q[k-1].t)/60;if(dt<=0||dt>20)continue;
    let r=movimento(Q[k-1].G,Q[k].G,ax,ay,R1,24);if(!r||r.c<0.3)r=movimento(Q[k-1].G,Q[k].G,ax,ay,250,24);
    if(r&&r.c>=0.3&&!r.borda)vs.push({vx:r.dx/dt,vy:r.dy/dt,c:r.c});}
  let v,fonte,disp=null;
  if(vs.length){const w=vs.reduce((s,x)=>s+x.c,0);v={vx:vs.reduce((s,x)=>s+x.vx*x.c,0)/w,vy:vs.reduce((s,x)=>s+x.vy*x.c,0)/w};fonte='radar';
    disp=Math.sqrt(vs.reduce((s,x)=>s+(x.vx-v.vx)**2+(x.vy-v.vy)**2,0)/vs.length)*KM*60;}
  else if(vento){v=vento;fonte='vento';}else{v={vx:0,vy:0};fonte='parado';}
  return {v,fonte,disp,n:vs.length,kmh:Math.hypot(v.vx,v.vy)*KM*60,vs};}
/* eco de chuva mais próximo (>=20 dBZ) no último quadro */
function maisProximo(G,v,alvo){const [ax,ay]=alvo||[PX,PY];let best=null;const R=170/KM;
  for(let j=Math.max(0,Math.floor(ay-R));j<Math.min(N,ay+R);j++)for(let i=Math.max(0,Math.floor(ax-R));i<Math.min(N,ax+R);i++){const z=G[j*N+i];if(z<20)continue;const d=Math.hypot(i-ax,j-ay);if(!best||d<best.d)best={d,i,j,z};}
  if(!best)return null;const ex=best.i-ax,ey=best.j-ay,az=(Math.atan2(ex,-ey)*180/Math.PI+360)%360,sp=Math.hypot(v.vx,v.vy);
  let vem=null;if(sp>0.05){const cl=-(ex*v.vx+ey*v.vy)/sp,lat=Math.abs(ex*v.vy-ey*v.vx)/sp;vem=cl>0?(lat*KM<12?'vindo em direção a '+NOME:'passando ao lado'):'se afastando';}
  let zm=-128;for(let j=best.j-6;j<=best.j+6;j++)for(let i=best.i-6;i<=best.i+6;i++)if(i>=0&&j>=0&&i<N&&j<N)zm=Math.max(zm,G[j*N+i]);
  return {km:Math.round(best.d*KM),dir:['norte','nordeste','leste','sudeste','sul','sudoeste','oeste','noroeste'][Math.round(az/45)%8],z:zm,vem};}
/* área com chuva e chuva forte num raio, para classificar o tipo de evento */
function tipo(G,R){const r=R/KM,r2=r*r;let n=0,c=0,f=0;for(let j=Math.floor(PY-r);j<=PY+r;j++)for(let i=Math.floor(PX-r);i<=PX+r;i++){if((i-PX)**2+(j-PY)**2>r2||i<0||j<0||i>=N||j>=N)continue;n++;const z=G[j*N+i];if(z>=20)c++;if(z>=40)f++;}
  return {cob:c/n,forte:c?f/c:0};}
return {Z,T,N,PX,PY,KM,tiles,poeTile,poeCobertura,semRadar,novaGrade,movimento,velocidade,prever,disco,cat,mmh,maisProximo,tipo};})();
if(typeof module!=='undefined')module.exports=NC;
