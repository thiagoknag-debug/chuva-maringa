// Guarda a última versão da página para abrir sem internet (rede primeiro, cópia só se cair)
const C='chuva-v1';
self.addEventListener('install',e=>{self.skipWaiting();e.waitUntil(caches.open(C).then(c=>c.add('./')).catch(()=>{}));});
self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));
self.addEventListener('fetch',e=>{if(e.request.mode!=='navigate')return;
  e.respondWith(fetch(e.request).then(r=>{if(r.ok){const cp=r.clone();caches.open(C).then(c=>c.put('./',cp));}return r;}).catch(()=>caches.match('./').then(r=>r||Response.error())));});
