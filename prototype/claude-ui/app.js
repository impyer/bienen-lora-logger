/* SPDX-License-Identifier: GPL-3.0-or-later
 * Bienenlogger – interaktiver, lokal ausführbarer UI-Prototyp.
 * Nach der Claude-Referenz vom 16.10.2026, ohne Backend-Schreibzugriff.
 * Keine erfundenen Produktivmesswerte: Musterreihen sind separat zuschaltbar.
 */
(()=>{
'use strict';
const STORE='bienenlogger-claude-beep-offline-v04';
const localId=()=>`local-${Date.now()}-${Math.random().toString(36).slice(2,11)}`;
// Nur lokaler Offline-Export: Die Quelldaten werden nicht an Server übertragen.
const fixtureNode=document.getElementById('beep-source-data');
let beepFixture=null;
if(fixtureNode){try{beepFixture=JSON.parse(fixtureNode.textContent);}catch(error){console.error('BEEP-Testdaten konnten nicht gelesen werden',error);}}
const hasBeepExport=Boolean(beepFixture?.schema==='bienenlogger-beep-export-local-v1' && Array.isArray(beepFixture.colonies));
const rawSample={id:'sample-20261016-volk8',zeit_utc:'2026-10-16T00:51:32.772Z',gewicht_roh:1398777,gewicht_kg:(1398777-101109)*0.000024211515512725,temperatur_c:18.43,batterie_v:3.262,fft_baender:[
  [71,122,19],[122,173,11],[173,224,17],[224,276,7],[276,327,6],[327,378,6],[378,429,4],[429,480,3],[480,532,4],[532,583,0]
].map(([von_hz,bis_hz,wert])=>({von_hz,bis_hz,wert}))};
const claudeStandVolker=hasBeepExport ? beepFixture.colonies.map(c=>String(c.key)) : ['1','2','4','5','6','7','8','9','10','20','21'];
const importedMeasurements=hasBeepExport ? Object.fromEntries(beepFixture.devices.map(d=>[String(d.volk),d.rows])) : {};
const importedStockcards=hasBeepExport ? beepFixture.inspections : [];
const importedReminders=importedStockcards.filter(e=>e.reminder?.at);
const exportAlerts=hasBeepExport ? beepFixture.anomalies : [];
let standLayout='kacheln',standSort='nr';
const standMetric={spark:true,temp:true,audio:true};
const staticVolker={
 '5':{id:5,name:'Volk 5',device:'BEEP Base',beute:null,queen:null,frames:null,source:'Gerätezuordnung vom Betreiber'},
 '8':{id:8,name:'Volk 8',device:'BEEP Base',beute:{typ:'Segeberger 1,5',brood:1,honey:0,frames:11,quelle:'Claude-Referenz; noch nicht aus BEEP geprüft'},queen:{year:2026,color:'weiß',since:'2026-06-14',quelle:'Claude-Referenz'},source:'Gerätezuordnung vom Betreiber'}
};
// Diese Metadaten entstammen dem *hochgeladenen* BEEP-Kontoexport, nicht Claude-Musterdaten.
if(hasBeepExport){
 for(const col of beepFixture.colonies){
  const key=String(col.key);
  staticVolker[key]={id:key,name:String(col.name),device:col.device||null,beute:col.beute||null,queen:col.queen||null,beep_hive_id:col.beep_hive_id||null,status:col.status||null,source:'BEEP-Kontoexport'};
 }
}
const colonyName=v=>data.colonyDrafts[v]?.name||staticVolker[v]?.name||('Volk '+v);
// Nur Identität aus der Claude-Gestaltungsvorlage; zu den übrigen Völkern liegen
// hier weder Live-Messdaten noch verifizierte Beutenkonfigurationen vor.
for(const id of claudeStandVolker){if(!staticVolker[id])staticVolker[id]={id:Number(id),name:'Volk '+id,device:null,beute:null,queen:null,frames:null,source:'Claude-Ansichtsreferenz; nicht importiert'};}
const defaultChannels=[
 {key:'gewicht_kg',name:'Stockgewicht',unit:'kg',quelle:'Stockmessgerät',agg:'Median / Verlauf',status:'zugeordnet',color:'#277254'},
 {key:'temperatur_c',name:'Brutnesttemperatur',unit:'°C',quelle:'Stockmessgerät',agg:'Mittelwert',status:'Position prüfen',color:'#cb8b38'},
 {key:'fft_baender',name:'Akustisches Spektrum',unit:'FFT-Rohwert',quelle:'Stockmessgerät',agg:'Vektor / keine dB',status:'zugeordnet',color:'#557ca2'},
 {key:'batterie_v',name:'Batteriespannung',unit:'V',quelle:'Stockmessgerät',agg:'letzter',status:'zugeordnet',color:'#899a7e'},
 {key:'temp_5cm',name:'Bodentemperatur 5 cm',unit:'°C',quelle:'Umweltsensor',agg:'Mittelwert',status:'geplant',color:'#b77a3b'},
 {key:'temp_20cm',name:'Bodentemperatur 20 cm',unit:'°C',quelle:'Umweltsensor',agg:'Mittelwert',status:'geplant',color:'#775b9b'},
 {key:'temp_50cm',name:'Bodentemperatur 50 cm',unit:'°C',quelle:'Umweltsensor',agg:'Mittelwert',status:'geplant',color:'#456a9d'}
];
const defaultChecklist=['Königin gesehen','Eier gesehen','Brutbild geprüft','Futter ausreichend','Keine Schwarmzellen','Varroakontrolle durchgeführt'];
// Ausschließlich Kategorien, die im vorliegenden BEEP-Export vorkommen. Die vollständige
// Taxonomie kann nur über den BEEP-Endpunkt /api/categories importiert werden.
const categoryLabels=[...new Set(importedStockcards.flatMap(e=>(e.fields||[]).map(f=>f.label)))].filter(Boolean).sort((a,b)=>a.localeCompare(b,'de'));
const taxonomyGroup=label=>label.split(' > ')[0];
function fieldKind(label){
 if(/(?:Anwesenheit|Alle Stadien|Behandlung|Zählung|Mit Zuckermethode ermittelt|Volk vereinigt)$/i.test(label))return 'boolean';
 if(/(?:Brutwaben|Honigrähmchen|Anzahl der Rähmchen)$/i.test(label))return 'integer';
 if(/natürlicher Fall$/i.test(label))return 'fall';
 return 'text';
}
function queenOf(v){const drafts=data.queens.filter(q=>q.volk===v).sort((a,b)=>String(a.effectiveDate||'').localeCompare(String(b.effectiveDate||''))||String(a.editedAt||'').localeCompare(String(b.editedAt||'')));return drafts.length?drafts.at(-1):staticVolker[v]?.queen||null;}
function colonyOf(v){return {...staticVolker[v],...(data.colonyDrafts[v]||{})};}

const data={view:'stand',volk:'8',days:7,mode:'real',inspections:[],hiveDrafts:[],queens:[],colonyDrafts:{},channels:[],checklist:defaultChecklist.slice(),imports:{},nativeNodes:[],nativeTemplates:[],activeNativeTemplate:'native-default',menu:false};
try{const s=JSON.parse(localStorage.getItem(STORE)||'{}');if(Array.isArray(s.inspections))data.inspections=s.inspections;if(Array.isArray(s.hiveDrafts))data.hiveDrafts=s.hiveDrafts;if(Array.isArray(s.channels))data.channels=s.channels;if(Array.isArray(s.checklist)&&s.checklist.length)data.checklist=s.checklist.filter(x=>typeof x==='string').slice(0,30);if(s.imports&&typeof s.imports==='object')data.imports=s.imports;if(Array.isArray(s.queens))data.queens=s.queens.filter(q=>q&&typeof q.volk==='string'&&typeof q.id==='string').slice(-300);if(s.colonyDrafts&&typeof s.colonyDrafts==='object'&&!Array.isArray(s.colonyDrafts))data.colonyDrafts=s.colonyDrafts;if(Array.isArray(s.nativeNodes))data.nativeNodes=s.nativeNodes.slice(0,5000);if(Array.isArray(s.nativeTemplates))data.nativeTemplates=s.nativeTemplates.slice(0,100);if(typeof s.activeNativeTemplate==='string')data.activeNativeTemplate=s.activeNativeTemplate;}catch(e){}
const Native=window.BienenStockkarte;
if(!Native)throw Error('Eigene Bienenlogger-Stockkarten-Engine wurde nicht geladen');
try {
 if(!data.nativeNodes.length){
  data.nativeNodes=categoryLabels.length?Native.fallback(categoryLabels):Native.prepare({taxonomy:[
    {id:'demo-volk',name:'Volk · Beispielkatalog',input:'label',children:[
      {id:'demo-queen',name:'Königin gesehen',input:'boolean'},
      {id:'demo-eggs',name:'Eier gesehen',input:'boolean'},
      {id:'demo-brood',name:'Brutbild',input:'score_quality',min:1,max:5},
      {id:'demo-food',name:'Futtervorrat',input:'number_1_decimals',min:0,unit:'kg'},
      {id:'demo-varroa',name:'Varroa-Methode',input:'select',children:[{id:'demo-natural',name:'Natürlicher Fall'},{id:'demo-sugar',name:'Puderzuckerprobe'}]},
      {id:'demo-observe',name:'Beobachtung',input:'text'}
    ]}
  ]});
 }
 const goodIds=new Set(data.nativeNodes.map(n=>n.id));
 data.nativeTemplates=data.nativeTemplates.filter(t=>t&&Array.isArray(t.category_ids));
 if(!data.nativeTemplates.length)data.nativeTemplates=[Native.template('BEEP-Export · erfasste Kategorien',data.nativeNodes.filter(n=>n.input!=='label'&&(!n.parent||!['select','options','list'].includes(data.nativeNodes.find(x=>x.id===n.parent)?.input))).map(n=>n.id),'native-default')];
 if(!data.nativeTemplates.some(t=>t.id===data.activeNativeTemplate))data.activeNativeTemplate=data.nativeTemplates[0].id;
} catch(e) { console.error('Ungültige lokale Taxonomie',e);data.nativeNodes=Native.fallback(categoryLabels);data.nativeTemplates=[Native.template('BEEP-Export',data.nativeNodes.filter(n=>!n.children.length).map(n=>n.id),'native-default')];data.activeNativeTemplate='native-default';}
function currentTemplate(){return data.nativeTemplates.find(t=>t.id===data.activeNativeTemplate)||data.nativeTemplates[0];}
const $=sel=>document.querySelector(sel); const main=$('#main');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number=(n,places=2)=>typeof n==='number'&&Number.isFinite(n)?n.toLocaleString('de-DE',{minimumFractionDigits:places,maximumFractionDigits:places}):'—';
const locDate=s=>s?new Intl.DateTimeFormat('de-DE',{timeZone:'Europe/Berlin',day:'2-digit',month:'2-digit',year:'numeric'}).format(new Date(s)):'—';
const locTime=s=>s?new Intl.DateTimeFormat('de-DE',{timeZone:'Europe/Berlin',day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}).format(new Date(s)):'—';
const label=(name,unit='')=>`<div class="kpi-label">${esc(name)}</div><div class="kpi-number">${unit}</div>`;
const card=(name,value,subtitle)=>`<div class="card"><div class="kpi-label">${esc(name)}</div><div class="kpi-number">${esc(value)}</div><div class="kpi-foot">${esc(subtitle)}</div></div>`;
const tag=(txt,cls='')=>`<span class="badge ${cls}">${esc(txt)}</span>`;
const persist=()=>{try{localStorage.setItem(STORE,JSON.stringify({inspections:data.inspections,hiveDrafts:data.hiveDrafts,channels:data.channels,checklist:data.checklist,imports:data.imports,nativeNodes:data.nativeNodes,nativeTemplates:data.nativeTemplates,activeNativeTemplate:data.activeNativeTemplate,queens:data.queens,colonyDrafts:data.colonyDrafts}));}catch(e){toast('Browser-Speicherung nicht verfügbar. Testentwürfe bitte als JSON exportieren.');}};
function toast(txt){const t=$('#toast');t.textContent=txt;t.style.display='block';clearTimeout(toast.timeout);toast.timeout=setTimeout(()=>t.style.display='none',4200);}
const rng=(seed)=>{const s=Math.sin(seed*34.98)*18273.198;return s-Math.floor(s)};
function demoRows(v){let arr=[];let start=Date.parse('2026-09-26T00:00:00Z');for(let i=0;i<=160;i++){
 const tm=start+i*3*3600000;const day=i/8;const base=v==='8'?31.8:26.8;
 let wt=base+day*.043+(Math.sin(day*1.6)*.28)+Math.sin(i*.87)*.018+(day>12?-.45:0);
 arr.push({id:'muster-'+v+'-'+i,zeit_utc:new Date(tm).toISOString(),gewicht_kg:wt,temperatur_c:20.4+Math.sin(day*.6)*1.25+Math.sin(i*.73)*.27,batterie_v:3.26,fft_baender:rawSample.fft_baender.map((b,j)=>({...b,wert:Math.max(0,Math.round(b.wert+(rng(i*j+8)-.5)*8))}))});
}return arr;}
function rows(v){
 if(data.mode==='demo')return demoRows(v);
 if(Array.isArray(data.imports[v])&&data.imports[v].length)return data.imports[v].slice().sort((a,b)=>Date.parse(a.zeit_utc)-Date.parse(b.zeit_utc));
 if(hasBeepExport)return Array.isArray(importedMeasurements[v])?importedMeasurements[v]:[];
 return v==='8'?[rawSample]:[];
}
function latest(v){const r=rows(v);return r.at(-1)||null;}
function chosenRows(v){let all=rows(v);let end=all.length?Date.parse(all.at(-1).zeit_utc):Date.now();return all.filter(r=>Date.parse(r.zeit_utc)>=end-data.days*86400000);}
function kpi(value,unit='',dp=2){return typeof value==='number'&&Number.isFinite(value)?number(value,dp)+(unit?' '+unit:''):'—';}
function localParts(t){const p=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',hourCycle:'h23'}).formatToParts(new Date(t));return Object.fromEntries(p.map(o=>[o.type,o.value]));}
function berlinToday(){const p=localParts(Date.now());return `${p.year}-${p.month}-${p.day}`;}
function dailyReference(arr){const b=new Map();for(const r of arr){if(!Number.isFinite(r.gewicht_kg)||r.gewicht_qualitaet==='auffällige Initialmessung – prüfen')continue;const p=localParts(r.zeit_utc);if(Number(p.hour)>=4)continue;const day=`${p.year}-${p.month}-${p.day}`;if(!b.has(day))b.set(day,[]);b.get(day).push(r.gewicht_kg);}return [...b].sort(([a],[b])=>a.localeCompare(b)).map(([day,nums])=>{const v=[...nums].sort((a,b)=>a-b);return {day,weight:v.length%2?v[(v.length-1)/2]:(v[v.length/2-1]+v[v.length/2])/2,n:v.length};});}
function dailyChange(v){const daily=dailyReference(rows(v));if(daily.length<2)return null;const a=daily.at(-1),b=daily.at(-2);const diff=Math.round((Date.parse(a.day)-Date.parse(b.day))/86400000);return diff===1?a.weight-b.weight:null;}
function head(title,desc,action=''){return `<div class="intro"><div><div class="eyebrow">BIENENLOGGER / ${esc(data.view)}</div><h1>${esc(title)}</h1><p>${esc(desc)}</p></div>${action}</div>`;}
function actions(){return `<div class="toolbar"><button class="btn small" data-action="import">JSON-Messdaten importieren</button><button class="btn small" data-action="export">Testdaten exportieren</button></div>`;}
function chartSVG(values,{color='#277254',valueKey='gewicht_kg',unit='kg',labelText='Zeitverlauf',height=240,events=[]}={}){
 const list=values.map(x=>({t:Date.parse(x.zeit_utc),v:x[valueKey]===null||x[valueKey]===undefined?NaN:Number(x[valueKey])})).filter(p=>Number.isFinite(p.t)&&Number.isFinite(p.v));
 if(!list.length)return `<div class="empty">Keine Messreihe für den ausgewählten Zeitraum.</div>`;
 const minT=Math.min(...list.map(a=>a.t)),maxT=Math.max(...list.map(a=>a.t));const low=Math.min(...list.map(a=>a.v)),high=Math.max(...list.map(a=>a.v));const delta=Math.max((high-low)*.15,.07);const min=low-delta,max=high+delta;
 const left=57,right=740,top=22,bottom=height-42;
 const x=t=>minT===maxT?(left+right)/2:left+(t-minT)/(maxT-minT)*(right-left),y=v=>bottom-(v-min)/(max-min)*(bottom-top);
 const tick=[0,.25,.5,.75,1].map(v=>{const yp=bottom-v*(bottom-top);return `<line x1="${left}" x2="${right}" y1="${yp}" y2="${yp}" stroke="#e9ede7"/><text x="${left-8}" y="${yp+4}" font-size="10" fill="#7c8a80" text-anchor="end">${number(min+v*(max-min),1)}</text>`;}).join('');
 const path=list.map((a,i)=>`${i?'L':'M'} ${x(a.t).toFixed(2)} ${y(a.v).toFixed(2)}`).join(' ');
 const points=list.length<55?list.map(p=>`<circle cx="${x(p.t)}" cy="${y(p.v)}" r="3.3" fill="white" stroke="${color}" stroke-width="2"><title>${esc(locTime(p.t))}: ${number(p.v,3)} ${esc(unit)}</title></circle>`).join(''):'';
 const stamps=(minT===maxT?[minT]:[minT,(minT+maxT)/2,maxT]).map(t=>`<text x="${x(t)}" y="${height-12}" font-size="10" text-anchor="middle" fill="#829086">${esc(locDate(t))}</text>`).join('');
 const annotations=(Array.isArray(events)&&list.length>1?events:[]).map(e=>{const t=Date.parse(e.date+'T10:00:00Z');if(t<minT||t>maxT)return '';return `<line x1="${x(t)}" y1="${top}" x2="${x(t)}" y2="${bottom}" stroke="#c18a38" stroke-dasharray="4 5" opacity=".6"><title>Dokumentationstag ${esc(e.date)} · Uhrzeit unbekannt, Markierung nur schematisch</title></line>`}).join('');
 const shape=list.length===1?`<circle cx="${x(list[0].t)}" cy="${y(list[0].v)}" r="6" fill="white" stroke="${color}" stroke-width="3"><title>${esc(locTime(list[0].t))}: ${number(list[0].v,3)} ${esc(unit)}</title></circle>`:`<path d="${path}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>${points}`;
 return `<svg viewBox="0 0 760 ${height}" role="img" aria-label="${esc(labelText)}: ${list.length} Messwerte in ${esc(unit)}"><text x="${left}" y="13" font-size="11" fill="#738477">${esc(unit)}</text>${tick}<line x1="${left}" y1="${bottom}" x2="${right}" y2="${bottom}" stroke="#d2dad0"/>${stamps}${annotations}${shape}</svg>`;
}
function spectrumSVG(fft){if(!fft?.length)return '<div class="empty">Kein FFT-Spektrum verfügbar.</div>';const max=Math.max(1,...fft.map(b=>b.wert));return `<svg viewBox="0 0 760 245" role="img" aria-label="FFT-Spektrum mit ${fft.length} Bändern">${[0,.5,1].map(f=>`<line x1="48" x2="740" y1="${188-f*154}" y2="${188-f*154}" stroke="#e5ebe4"/><text x="40" y="${192-f*154}" font-size="10" fill="#8a958b" text-anchor="end">${Math.round(f*max)}</text>`).join('')}${fft.map((b,i)=>{let x=57+i*680/fft.length,w=Math.max(12,680/fft.length-10),h=(b.wert/max)*154;return `<rect x="${x}" y="${188-h}" width="${w}" height="${h}" rx="3" fill="#c18a38"><title>${b.von_hz}–${b.bis_hz} Hz: ${b.wert}</title></rect><text x="${x+w/2}" y="202" text-anchor="middle" font-size="9" fill="#7f8d80">${b.von_hz}</text>`;}).join('')}<text x="400" y="231" font-size="11" fill="#879489" text-anchor="middle">Bandbeginn (Hz) · relative, nicht kalibrierte FFT-Rohwerte</text></svg>`;}
function hiveMini(){return `<svg class="hive-mini" viewBox="0 0 60 72" aria-hidden="true"><rect x="3" y="11" width="54" height="6" rx="1" fill="#45514C"/><rect x="7" y="18" width="46" height="37" fill="#E9D8B6" stroke="#A78A5A" stroke-width="1.3"/><path d="M7 26 H53 M7 48 H53" stroke="#C2A67D" stroke-width="1"/><rect x="3" y="54" width="54" height="5" fill="#A68E65"/><rect x="6" y="63" width="48" height="4" fill="#48514B"/><path d="M25 54h12" stroke="#202522" stroke-width="2"/></svg>`;}
function standColony(v){
 const info=colonyOf(v),r=latest(v),active=v===data.volk;
 const hasMany=rows(v).filter(x=>Number.isFinite(x.gewicht_kg_chart??x.gewicht_kg)).length>=2;
 const w=r?.gewicht_kg!=null?number(r.gewicht_kg,3):'—';
 const temp=r?.temperatur_c!=null?number(r.temperatur_c,2)+' °C':'—';
 const summary=hasBeepExport?(queenOf(v)?.name||'Königinnenangabe nicht vorhanden'):(v==='8'?'Königin weiß 2026 · Claude-Referenz':'Königin / Beute nicht importiert');
 const metric=standMetric;
 return `<button class="colony ${active?'selected':''}" data-volk="${esc(v)}" aria-label="${esc(info.name)} öffnen">
  <div class="colony-head"><span class="colony-id">${esc(info.name)} <span class="queen-dot" style="background:${/^#[0-9a-fA-F]{6}$/.test(queenOf(v)?.color||'')?queenOf(v).color:'transparent'}" aria-hidden="true"></span></span><span class="hive-kind">${esc(info.beute?.typ||'Beute unbekannt')}</span></div>
  <div class="colony-queen">${esc(summary)}</div>
  <div class="colony-weight">${hiveMini()}<div><span class="measure-title">Gewicht</span><div class="weight-line"><strong>${w}</strong><small>kg</small></div><div class="mini-sub">${r?(hasMany?'CSV-Messreihe · Zeitzone Europe/Berlin':'Einzelmessung; kein Tagesvergleich'):'Keine Messreihe vorhanden'}</div></div></div>
  ${metric.spark?`<div class="mini-curve">${r?chartSpark(v):'<span>Gewichtsverlauf: keine Zeitreihe</span>'}</div><div class="mini-caption">Gewicht, letzte 7 Tage</div>`:''}
  ${metric.temp?`<div class="colony-sub-grid"><div><small>Brutnest t₀</small><strong>${temp}</strong></div><div><small>Deckel t₁</small><strong>—</strong></div></div>`:''}
  ${metric.audio?`<div class="colony-audio"><span>Akustik · FFT-Spektrum</span><strong>${r?.fft_baender?.length||'—'} Bänder</strong></div>`:''}
  <div class="colony-meta"><span>${esc(info.device||'Kein Stockmessgerät zugeordnet')}</span><span>${r?'Messung vorhanden':'Ohne Messung'}</span></div>
 </button>`;
}
function chartSpark(v){const values=rows(v).filter(r=>Number.isFinite(r.gewicht_kg)&&r.gewicht_qualitaet!=='auffällige Initialmessung – prüfen');if(values.length<2)return '<span>Ein Messpunkt – noch keine Kurve</span>';
 const min=Math.min(...values.map(x=>x.gewicht_kg)),max=Math.max(...values.map(x=>x.gewicht_kg)),delta=max-min||1;
 const pts=values.map((r,i)=>`${i?'L':'M'}${(i/Math.max(values.length-1,1)*235).toFixed(1)} ${(30-(r.gewicht_kg-min)/delta*24).toFixed(1)}`).join(' ');
 return `<svg viewBox="0 0 240 35" role="img" aria-label="Gewichtsverlauf als Miniatur"><path d="${pts}" fill="none" stroke="#1F4E79" stroke-width="1.5"/></svg>`;}
function standTable(series){return `<div class="panel table-wrap"><table class="data-table"><thead><tr><th>Volk</th><th>Gewicht</th><th>Temperatur t₀</th><th>Akustik</th><th>Messquelle</th><th>Details</th></tr></thead><tbody>${series.map(v=>{let r=latest(v);return `<tr><td><strong>${esc(colonyName(v))}</strong></td><td>${r?.gewicht_kg!=null?number(r.gewicht_kg,3)+' kg':'—'}</td><td>${r?.temperatur_c!=null?number(r.temperatur_c)+' °C':'—'}</td><td>${r?.fft_baender?.length||'—'}</td><td>${esc(staticVolker[v].device||'Nicht erfasst')}</td><td><button class="btn small" data-volk="${esc(v)}">Öffnen</button></td></tr>`}).join('')}</tbody></table></div>`;}
function viewsStand(){
 let list=claudeStandVolker.slice();
 if(standSort==='gewicht')list.sort((a,b)=>(latest(b)?.gewicht_kg??-1)-(latest(a)?.gewicht_kg??-1));
 else if(standSort==='nr')list.sort((a,b)=>colonyName(a).localeCompare(colonyName(b),'de',{numeric:true}));
 else if(standSort==='status')list.sort((a,b)=>Number(Boolean(latest(b)))-Number(Boolean(latest(a)))||Number(a)-Number(b));
 const ndata=list.filter(v=>latest(v)).length;
 const compact=(name,value,unit,source)=>`<div class="stand-metric"><span>${name}</span><strong>${value}<small> ${unit}</small></strong><small>${source}</small></div>`;
 const measured=hasBeepExport?'Echte BEEP-Exporte vom 16.10.2026 · Offline-Test ohne Serverzugriff.': 'Ein BEEP-Beispielmesspunkt, keine Live-Verbindung.';
 const countCards=hasBeepExport?importedStockcards.length:0;
 const activeReminders=hasBeepExport?importedReminders.length:0;
 const alertBox=(cls,title,body,footer)=>`<div class="alert-card"><i class="alert-dot ${cls}"></i><div><strong>${esc(title)}</strong><p>${esc(body)}</p><small>${esc(footer)}</small></div></div>`;
 return `<div class="banner"><strong>${data.mode==='demo'?'Simulation':'BEEP-Export'}</strong><span>${data.mode==='demo'?'SIMULATION – künstliche Kurven':measured}</span></div>
 <div class="stand-title"><h1>${esc(hasBeepExport?beepFixture.stand:'Teststand')}</h1><span>${list.length} Beuteneinträge · ${ndata} primäre Stockmessgeräte mit Messungen · ${countCards} Stockkarteneinträge</span><small>Exportstand 16.10.2026</small></div>
 <div class="stand-metrics">
 ${compact('Außentemperatur','—','°C','Wetterstations-CSV enthält keine Wetterwerte')}
 ${compact('Luftfeuchte','—','%','Nicht im Export')}
 ${compact('Wind / Böen','—','m/s','Nicht im Export')}
 ${compact('Regen 24 h','—','mm','Nicht im Export')}
 ${compact('Licht','—','lx','Nicht im Export')}
 ${compact('Boden Sonde 1','12,4','°C','Projektmessung 14.10. · 5 cm, separat')}
 ${compact('Boden Sonde 2','12,3','°C','Projektmessung 14.10. · 20 cm, separat')}
 ${compact('Boden Sonde 3','13,1','°C','Projektmessung 14.10. · 50 cm, separat')}
 </div>
 <section class="stand-alerts"><h2>Handlungsbedarf & Datenqualität</h2><div class="alert-grid">
 ${alertBox('orange',`${activeReminders} Erinnerungen aus BEEP`,activeReminders?'BEEP-Stockkarte enthält fällige bzw. zukünftige Erinnerungen.':'Noch keine BEEP-Erinnerungen importiert.','Quelle: BEEP-Stockkarte')}
 ${alertBox('blue',`${ndata} Völker mit Sensorreihen`,hasBeepExport?'Volk 5 und Volk 8: jeweils 126 Datensätze; 124 mit Gewicht und Temperatur.':'Nur bekannte Beispieldaten vorhanden.','Gewicht, Temperatur und 10 FFT-Bänder')}
 ${alertBox('orange',`${exportAlerts.length} auffällige Anfangsgewichte`,exportAlerts.length?'Plausibilitätsverdacht – Werte unverändert archiviert, aber in Trendkurven ausgeblendet.':'Kein auffälliger Messwert identifiziert.','Nur automatische Regel; Kalibrierung vor Ort prüfen')}
 ${alertBox('',`${countCards} BEEP-Stockkarteneinträge`,hasBeepExport?'Mit Notizen, Checklistenfeldern, Varroazählungen und Beuten-Stammdaten.':'Stockkartenimport noch offen.','Lokal geladen, BEEP bleibt führende Quelle')}
 </div></section>
 <div class="stand-controls"><h2>Völker</h2><div class="segmented"><button class="${standLayout==='kacheln'?'active':''}" data-action="view-cards">Kacheln</button><button class="${standLayout==='liste'?'active':''}" data-action="view-table">Liste</button></div>
 <span class="sort-label">Sortieren</span><div class="pill-choices"><button class="${standSort==='nr'?'active':''}" data-action="sort-nr">Nummer</button><button class="${standSort==='gewicht'?'active':''}" data-action="sort-gewicht">Gewicht</button><button class="${standSort==='status'?'active':''}" data-action="sort-status">Messstatus</button></div>
 <div class="toolbar stand-options"><span class="sort-label">Kennzahlen</span>${[['spark','Verlauf 7 T'],['temp','Temperatur'],['audio','Akustik']].map(([key,name])=>`<button class="${standMetric[key]?'active':''}" aria-pressed="${standMetric[key]}" data-action="toggle-${key}">${name}</button>`).join('')}</div></div>
 ${standLayout==='kacheln'?`<div class="colony-grid">${list.map(standColony).join('')}</div>`:standTable(list)}
 <div class="section-heading"><h2>Messdaten & Einträge</h2><span>Nachweise statt interpolierter Zeitreihen</span></div>
 <div class="layout-two"><section class="panel"><div class="panel-head"><div><h2>Gewichtsverlauf · Volk 8</h2><div class="panel-subtitle">${data.mode==='demo'?'Simuliert':hasBeepExport?'BEEP-Geräte-CSV · Auffällige Initialmessungen ausgelassen':'Bekannter Einzelmesspunkt'}</div></div><button class="btn small" data-volk="8">Cockpit öffnen →</button></div>${chartSVG(chosenRows('8'),{labelText:'Gewichtsverlauf Volk 8',valueKey:hasBeepExport?'gewicht_kg_chart':'gewicht_kg'})}</section><section class="panel"><h2>Stockkarte & Beutenaufbau</h2><p class="small muted" style="margin:10px 0">Die BEEP-Stockkarte bleibt führende Datenquelle. Änderungen im Prototyp sind lokale Entwürfe.</p><button class="btn" data-view="stockkarte">Stockkarte öffnen</button><button class="btn" data-view="beute">Beute ansehen</button></section></div>`;
}
function tabs(){return `<div class="tabs"><button class="text-back" data-view="stand">← ${esc(hasBeepExport?beepFixture.stand:'Teststand')}</button><label for="colonyPicker" class="small muted">Volk wählen</label><select id="colonyPicker" aria-label="Volk auswählen">${claudeStandVolker.map(v=>`<option value="${esc(v)}" ${v===data.volk?'selected':''}>${esc(colonyName(v))}</option>`).join('')}</select><button class="chip" data-view="stockkarte">Stockkarte</button><button class="chip" data-view="beute">Beutenaufbau</button></div>`;}
function range(){return `<div class="toolbar">${[1,7,21,90].map(d=>`<button class="chip ${d===data.days?'active':''}" data-days="${d}">${d===1?'24 h':d===7?'7 Tage':d===21?'21 Tage':'Saison'}</button>`).join('')}</div>`;}
function viewsVolk(){let v=data.volk,info=colonyOf(v),r=latest(v);let row=chosenRows(v);return `${head(info.name+' · Volk-Cockpit','Messdaten, Stockkarte und Eingriffe auf einer Zeitachse · Zeitstempel in Europe/Berlin.',`<button class="btn primary" data-action="new-inspection">+ Durchsicht erfassen</button>`)}${tabs()}<div class="toolbar"><button class="btn" data-action="edit-colony">Volk bearbeiten</button><button class="btn" data-action="edit-queen">Königin bearbeiten</button><button class="btn" data-action="new-queen">Königin ersetzen</button></div>
<div class="kpi-grid">${card('Gewicht',kpi(r?.gewicht_kg,'kg',3),r?.gewicht_kg!=null?'Kalibrierter CSV-Wert':'Kein Gewichtswert')}${card('Brutnesttemperatur',kpi(r?.temperatur_c,'°C'),r?.temperatur_c!=null?'BEEP-Sensor t₀ (Position prüfen)':'Keine Temperatur')}${card('Tagesbilanz',kpi(dailyChange(v),'kg',3),'Median 00–04 Uhr · nur bei 2 Folgetagen')}${card('FFT-Spektrum',r?.fft_baender?.length?String(r.fft_baender.length)+' Bänder':'—','Relative akustische Bandwerte')}</div>
<div class="section-heading"><h2>Messdaten und Stockkarte</h2>${range()}</div><div class="layout-two"><section class="panel"><div class="panel-head"><div><h2>Gewichtsverlauf</h2><div class="panel-subtitle">${row.length} Meldungen · ${data.mode==='demo'?'Muster':hasBeepExport?'BEEP-CSV inkl. Lücken und Qualitätshinweisen':'Einzelwert / JSON-Import'}</div></div>${tag('Gewicht · kg','blue')}</div>${chartSVG(row,{labelText:'Gewichtskurve',valueKey:hasBeepExport?'gewicht_kg_chart':'gewicht_kg'})}<div class="chart-legend"><span><span class="legend-dot" style="background:#277254"></span>Gewicht</span><span>${row.length>1?'Ausgewählte Werte ohne Lückenfüllung':'Nur einzelner Messwert – noch keine Trenddiagnose'}</span></div></section><section class="panel"><h2>Temperaturverlauf</h2><div class="panel-subtitle">Brutnest / Sensorposition wird mit Kanalregister verknüpft</div>${chartSVG(row,{color:'#c18a38',valueKey:'temperatur_c',unit:'°C',labelText:'Temperatur'})}</section></div>
<div class="section-heading"><h2>Akustik und Stockkarte</h2></div><div class="layout-two"><section class="panel"><div class="panel-head"><h2>FFT-Spektrum der letzten Messung</h2>${tag('Rohwerte','amber')}</div>${spectrumSVG(r?.fft_baender)}<p class="small muted">Keine akustische Diagnose aus einem einzelnen Spektrum. Vergleich erst bei längeren Zeitreihen.</p></section><section class="panel"><div class="panel-head"><h2>Letzte Stockkartenereignisse</h2><button class="btn small" data-view="stockkarte">Alle Einträge →</button></div>${eventList(v,4)}<hr><div class="note">Beutenaufbau, Königin und Eingriffe sind unabhängig von der Messgerät-ID. Ein Gerätewechsel verändert keine Volk-ID.</div></section></div>`;}
function allEvents(v){
 const fromBeep=hasBeepExport?importedStockcards.filter(e=>e.volk===v):[];
 return fromBeep.concat(data.inspections.filter(e=>e.volk===v)).sort((a,b)=>b.date.localeCompare(a.date));
}
function eventList(v,limit=30){const ev=allEvents(v).slice(0,limit);
 return ev.length?`<div class="timeline" style="margin-top:15px">${ev.map(e=>{
 const isBeep=String(e.source||'').startsWith('BEEP-');
 const details=(Array.isArray(e.fields)&&e.fields.length)?`<details class="source-details"><summary>Originalfelder (${e.fields.length})</summary>${e.fields.map(f=>`<div class="stat-row"><span>${esc(f.label)}</span><strong>${esc(f.value)}</strong></div>`).join('')}</details>`:'';
 return `<div class="event"><div class="event-meta">${esc(e.date)} · ${isBeep?'BEEP-Originalexport · Quelle ohne Zeitzone':'Lokaler Testentwurf'}</div>
 <div class="event-title">${esc(e.type)}${e.needs_attention?' · Handlungsbedarf':''}</div>
 <div class="event-text">${esc(e.summary||'Keine Notiz')} ${e.flags?.length?'· '+esc(e.flags.join(', ')):''}</div>
 ${e.reminder?.at?`<div class="reminder"><strong>Erinnerung: ${esc(e.reminder.at)}</strong>${e.reminder.text?' · '+esc(e.reminder.text):''}</div>`:''}
 ${details}<div class="event-actions"><button class="btn small" data-action="${isBeep?'correct-beep':'edit-inspection'}" data-id="${esc(e.id)}">${isBeep?'Korrektur als Entwurf':'Eintrag bearbeiten'}</button></div></div>`;}).join('')}</div>`:'<div class="empty">Keine Stockkartenereignisse vorhanden.</div>';
}
function viewsStockkarte(){let v=data.volk;const queen=queenOf(v);return `${head('Digitale Stockkarte · '+colonyName(v),'BEEP-Prinzip: flexible Checklisten, Verlauf, Maßnahmen und Königinneninformationen.',`<button class="btn primary" data-action="new-inspection">+ Durchsicht / Maßnahme</button>`)}${tabs()}
<div class="toolbar"><button class="btn primary" data-action="edit-colony">Volk bearbeiten</button><button class="btn" data-action="edit-queen">Königin bearbeiten / korrigieren</button><button class="btn" data-action="new-queen">Neue Königin erfassen</button></div><div class="layout-two"><section class="panel"><div class="panel-head"><div><h2>Chronik und Maßnahmen</h2><div class="panel-subtitle">${hasBeepExport?'BEEP-Originalexport (nur lesend) + lokale Testentwürfe':'Lokale Testentwürfe; kein BEEP-Sync'}</div></div>${tag(allEvents(v).length+' Einträge','blue')}</div>${eventList(v,100)}</section><section class="panel"><h2>Königin & biologische Identität</h2><div class="stat-list" style="margin-top:17px"><div class="stat-row"><span>Königin laut BEEP</span><strong>${esc(queen?.name||'Nicht erfasst')}</strong></div><div class="stat-row"><span>Jahrgang</span><strong>${esc(queen?.year??'—')}</strong></div><div class="stat-row"><span>Farbwert</span><strong>${esc(queen?.color||'—')}</strong></div><div class="stat-row"><span>Herkunft der Angabe</span><strong>${esc(queen?.source||queen?.quelle||'Keine Angabe')}</strong></div></div><hr><h3>Königinnenhistorie (lokale Entwürfe)</h3>${queenHistory(v)}<hr><h3>Dynamische BEEP-ähnliche Checklisten</h3><p class="small muted">Eigener Bienenlogger-Code mit hierarchischen Kategorien, Kategorie-IDs und Eingabetypen. Kein BEEP-Frontend/Server eingebunden.</p><div class="toolbar"><button class="btn" data-action="manage-templates">Checklisten verwalten</button><button class="btn" data-action="import-native-schema">BEEP-Kategorien / Checklisten als JSON importieren</button></div><div class="small muted">${esc(data.nativeNodes.length)} Katalogeinträge · ${esc(data.nativeTemplates.length)} Checklisten · aktiv: ${esc(currentTemplate()?.name||'—')}</div><hr><h3>Zusätzliche Schnellprüfliste</h3><div class="small muted" style="margin:7px 0">Bei einer neuen Durchsicht können die folgenden Punkte dokumentiert werden:</div>${data.checklist.map(x=>`<div class="row-small"><span>☐ ${x}</span><span class="source-tag">optional</span></div>`).join('')}<hr><form id="checklistForm" class="form-grid"><div class="form-field full"><label>Eigenen Checklistenpunkt hinzufügen (Test)</label><input name="item" required maxlength="90" placeholder="z. B. Honigraum kontrolliert"></div><div class="form-field full"><button class="btn small" type="submit">Zur Test-Checkliste hinzufügen</button></div></form><hr><div class="note warning">Die BEEP-Einträge stammen aus einem lokalen Export und sind schreibgeschützt. Neue Einträge sind getrennte lokale Testentwürfe, keine Synchronisation mit BEEP.</div></section></div>`;}
function hiveOf(v){let b=staticVolker[v].beute;const drafts=data.hiveDrafts.filter(x=>x.volk===v).sort((a,b)=>a.date.localeCompare(b.date));if(!b&&!drafts.length)return null;return {...(b||{typ:'',brood:0,honey:0,frames:null}),...(drafts.length?drafts.at(-1):{}),isDraft:!!drafts.length};}
function hiveLayers(c){if(!c)return `<div class="hive-diagram"><div class="no-data">Beutenaufbau unbekannt<br><span class="small">Keine Zargenzahl ohne belegte Quelle ableiten</span></div></div>`;let layers=[];for(let i=0;i<Math.min(8,Number(c.honey)||0);i++)layers.push('<div class="hive-layer honey">Honigzarge <small>Position '+(i+1)+'</small></div>');for(let i=0;i<Math.min(8,Number(c.brood)||0);i++)layers.push('<div class="hive-layer brood">Brutzarge <small>Position '+(i+1+(Number(c.honey)||0))+'</small></div>');return `<div class="hive-diagram"><div class="hive-roof">Deckel</div>${layers.join('')||'<div class="no-data">Keine konfigurierte Zarge</div>'}<div class="hive-base">Boden / Waage</div></div>`;}
function viewsBeute(){let v=data.volk,c=hiveOf(v),info=staticVolker[v];let drafts=data.hiveDrafts.filter(e=>e.volk===v).sort((a,b)=>b.date.localeCompare(a.date));return `${head('Beutenkonfiguration · '+colonyName(v),'Physische Beute und Volk bleiben unabhängige Identitäten. BEEP-Stockkarte ist führende Dokumentation.')}${tabs()}
<div class="layout-two"><section class="panel"><div class="panel-head"><div><h2>Zargenaufbau · ${esc(c?.typ||'Unbekannt')}</h2><div class="panel-subtitle">${c?.isDraft?'Aktuelle Ansicht ist ein lokaler Änderungsentwurf':c?(hasBeepExport?'BEEP-Stammdatensnapshot, keine Konfigurationshistorie':'Claude-Referenz (nicht live geprüft)'):'Kein bestätigter Beutenaufbau'}</div></div>${tag(c?.isDraft?'Entwurf':c?(hasBeepExport?'BEEP-Export':'Claude-Referenz'):'Unbekannt',c?.isDraft?'amber':'gray')}</div>${hiveLayers(c)}<div class="stat-list" style="margin-top:21px"><div class="stat-row"><span>BEEP-Beuten-ID</span><strong>${esc(info.beep_hive_id||'Nicht erfasst')}</strong></div><div class="stat-row"><span>Brutzargen</span><strong>${c?.brood??'—'}</strong></div><div class="stat-row"><span>Honigzargen</span><strong>${c?.honey??'—'}</strong></div><div class="stat-row"><span>Rähmchen</span><strong>${c?.frames??'—'}</strong></div></div><div class="note warning" style="margin-top:15px">Ein Zargenwechsel ist ein Ereignis in der Stockkarte und kann einen Gewichtssprung erklären. Eine Gewichts-Korrektur ohne bekannte Zargenmasse wird nicht berechnet.</div></section><section class="panel"><h2>Beutenänderung simulieren</h2><div class="panel-subtitle">Keine Übertragung an BEEP oder Server, nur Bedien- und Modelltest.</div><form id="hiveForm" class="form-grid" style="margin-top:17px"><div class="form-field full"><label for="hivetyp">Beutentyp</label><input id="hivetyp" name="typ" value="${esc(c?.typ||'')}" maxlength="80" placeholder="Nur falls bekannt"></div><div class="form-field"><label for="brood">Brutzargen</label><input id="brood" name="brood" type="number" min="0" max="8" value="${c?.brood??''}" required></div><div class="form-field"><label for="honey">Honigzargen</label><input id="honey" name="honey" type="number" min="0" max="8" value="${c?.honey??''}" required></div><div class="form-field"><label for="frames">Rähmchen</label><input id="frames" name="frames" type="number" min="0" max="100" value="${c?.frames??''}"></div><div class="form-field"><label for="hivedate">Gültig ab</label><input id="hivedate" name="date" type="date" value="${berlinToday()}" required></div><div class="form-field full"><label for="hivenote">Dokumentation / Quelle</label><textarea id="hivenote" name="note" placeholder="Zum Beispiel Zarge aufgesetzt – hier nur als lokaler Entwurf"></textarea></div><div class="form-field full"><button class="btn primary" type="submit">Änderung als Testentwurf speichern</button></div></form><hr><h3>Konfigurationshistorie (Test)</h3>${drafts.length?drafts.map(d=>`<div class="row-small"><span>${esc(d.date)} · ${d.brood} Brut / ${d.honey} Honig · ${esc(d.note||'Ohne Notiz')}</span>${tag('Entwurf','amber')}</div>`).join(''):'<p class="small muted" style="margin-top:8px">Noch keine Änderungsentwürfe.</p>'}<hr><div class="note">Bei einer späteren BEEP-Anbindung werden Einträge aus der Stockkarte als Quelle und versionierte Beutenhistorie übernommen. Keine zweite parallele Stammdatenpflege.</div></section></div>`;}
function viewsAnalyse(){let v=data.volk;let arr=rows(v);const daily=dailyReference(arr),deltas=daily.slice(1).map((d,i)=>({...d,delta:(Date.parse(d.day)-Date.parse(daily[i].day)===86400000)?d.weight-daily[i].weight:null}));const anomalies=deltas.filter(x=>x.delta!==null&&Math.abs(x.delta)>1);const qualityAlerts=arr.filter(r=>r.gewicht_qualitaet==='auffällige Initialmessung – prüfen');return `${head('Analysen & Völkervergleich','beelogger-orientiert: Median der Nachtwerte, Tagesbilanz, Signalprüfung und Ereignisbezug.')}${tabs()}
<div class="kpi-grid">${card('Nacht-Referenzwerte',String(daily.length),'Median 00:00–04:00 Uhr, Europe/Berlin')}${card('Letzte Tagesbilanz',kpi(dailyChange(v),'kg',3),'Nur zwei aufeinanderfolgende Tage')}${card('Plausibilitäts-Hinweise',String(anomalies.length+qualityAlerts.length),'Bei Initialmessungen: Medianabweichung > 15 % und > 2 kg')}${card('Messpunkte',String(arr.length),data.mode==='demo'?'Ausschließlich simuliert':'Vorliegende Daten')}</div>
<div class="section-heading"><h2>Gewichtsanalyse · ${esc(colonyName(v))}</h2></div><div class="layout-two"><section class="panel"><div class="panel-head"><div><h2>Gewicht und Tagesentwicklung</h2><div class="panel-subtitle">${data.mode==='demo'?'Musterverlauf':'Realdaten – keine geglätteten oder interpolierten Lücken'}</div></div>${tag('beelogger-Prinzip','blue')}</div>${chartSVG(arr,{labelText:'Messgewicht '+colonyName(v),height:270,events:allEvents(v),valueKey:hasBeepExport?'gewicht_kg_chart':'gewicht_kg'})}</section><section class="panel"><h2>Berechnungsmethodik</h2><div class="stat-list" style="margin-top:14px"><div class="stat-row"><span>Referenz</span><strong>Median 00–04 Uhr</strong></div><div class="stat-row"><span>Tagesbilanz</span><strong>Tag t − Vortag</strong></div><div class="stat-row"><span>Zeitbasis</span><strong>Europe/Berlin</strong></div><div class="stat-row"><span>Eingriffe</span><strong>Separat markieren</strong></div><div class="stat-row"><span>FFT</span><strong>Vektor, keine dB</strong></div></div><hr><div class="note">Gewichtsänderungen können durch Tracht, Wetter oder Eingriffe verursacht sein. Keine automatische Schwarm- oder Varroa-Diagnose aus diesen Kennzahlen.</div></section></div>
<div class="section-heading"><h2>Völkervergleich am Stand</h2><span>Nacht-Median · bei dieser kurzen Zeitreihe eingeschränkt</span></div><div class="layout-two"><section class="panel"><h2>Tagesreferenz · letzte verfügbare Nacht</h2><div class="compare-bars" style="margin-top:19px">${['5','8'].map(id=>{let d=dailyReference(rows(id)).at(-1);return `<div class="compare-bar"><span>Volk ${id}</span><div class="bar-track"><div class="bar-fill" style="width:${d?Math.min(100,d.weight/45*100):0}%"></div></div><strong>${d?number(d.weight,2)+' kg':'—'}</strong></div>`;}).join('')}</div><p class="small muted" style="margin-top:17px">Nur Nachtwerte. Unterschiedliche Beutenmasse und Kalibrierung sind bei Vergleichen zu berücksichtigen.</p></section><section class="panel"><h2>Tagesbilanzen und Maßnahmen</h2>${deltas.length?`<div class="table-wrap"><table class="data-table"><thead><tr><th>Tag</th><th>Nachtmedian</th><th>Δ kg</th><th>Eintrag im Entwurf</th></tr></thead><tbody>${deltas.slice(-8).reverse().map(d=>`<tr><td>${esc(d.day)}</td><td>${number(d.weight,3)}</td><td>${kpi(d.delta,'',3)}</td><td>${allEvents(v).filter(e=>e.date===d.day).length?'Ja':'—'}</td></tr>`).join('')}</tbody></table></div>`:'<div class="empty">Für eine Tagesbilanz fehlen aufeinanderfolgende Nächte.</div>'}</section></div>`;}
function viewsUmwelt(){const soil=[['5 cm','12,4 °C'],['20 cm','12,3 °C'],['50 cm','13,1 °C']];return `${head('Umwelt & Tracht','Standortbezogene Messungen – nicht als zusätzliche Stockmessgeräte zählen.')}
<div class="kpi-grid">${card('Wetterstation','SenseCAP S2120','Vorhandene Datenquelle, aktuelle Daten hier nicht geladen')}${card('Boden 5 cm','12,4 °C','Bekannter Einzelwert vom 14.10.2026')}${card('Boden 20 cm','12,3 °C','Bekannter Einzelwert vom 14.10.2026')}${card('Boden 50 cm','13,1 °C','Bekannter Einzelwert vom 14.10.2026')}</div>
<div class="section-heading"><h2>Wetter, Phänologie und Tracht</h2></div><div class="layout-two"><section class="panel"><h2>Bodentemperatur und Messpositionen</h2>${soil.map(([t,v])=>`<div class="row-small"><span>Tiefe ${t}</span><strong>${v}</strong></div>`).join('')}<div class="note" style="margin-top:16px">Hier werden nur die im Projekt bereits übermittelten drei Einzelwerte dargestellt. Für echte Zeitverläufe braucht die Oberfläche die Bodenmessreihen des Servers.</div><hr><h3>Temperaturverlauf</h3><div class="empty">Noch keine vollständige Umwelt-Zeitreihe in dieser Offline-Vorschau.</div></section><section class="panel"><h2>Phänologie, Grünlandtemperatursumme und Tracht</h2><div class="stat-list" style="margin-top:15px"><div class="stat-row"><span>Grünlandtemperatursumme</span>${tag('Noch nicht berechenbar','gray')}</div><div class="stat-row"><span>DWD-Phänologie</span>${tag('Anbindung vorbereitet','gray')}</div><div class="stat-row"><span>Blütenprognose</span>${tag('Geplant','gray')}</div><div class="stat-row"><span>Trachtflächen</span>${tag('Noch keine GIS-Daten','gray')}</div></div><hr><div class="note warning">Keine erfundene GTS, Pollenprognose oder Flugkreis-Karte. Eine reale Blütenprognose benötigt Wetterhistorie, DWD-Beobachtungen und eine klar dokumentierte Berechnung.</div></section></div>`;}
function viewsQuellen(){const ch=defaultChannels.concat(data.channels);return `${head('Datenquellen & Kanäle','Nach Claude: Feldnamen, Einheiten, Achsen und Verdichtung werden über ein Kanalregister bestimmt.',actions())}
<div class="layout-equal"><section class="panel"><h2>Messquellen</h2><div class="stat-list" style="margin-top:16px"><div class="stat-row"><span>BEEP Bases · Stockmessgeräte</span>${tag('2 Geräte','blue')}</div><div class="stat-row"><span>Wetterstation S2120</span>${tag('Am Stand','gray')}</div><div class="stat-row"><span>Bodensonde LSN50v2-D23</span>${tag('5 / 20 / 50 cm','gray')}</div><div class="stat-row"><span>Stockkarte · BEEP</span>${tag('Import noch offen','amber')}</div><div class="stat-row"><span>Klassischer beelogger</span>${tag('Alternatives Primärgerät','gray')}</div></div><hr><div class="note">BEEP Base, klassischer beelogger und Eigenentwicklung sind Alternativen als primäres Gerät. Feuchte, CO₂ oder weitere Messgrößen dürfen ergänzend dazu erfasst werden.</div></section><section class="panel"><h2>Import und Datensicherheit</h2><p class="small muted" style="margin-top:13px">Hier kannst du eine JSON-Datei mit dem Format der geschützten BEEP-Messdaten-API aus Pull Request #13 lokal in die Ansicht laden. Die Datei verlässt den Browser nicht.</p><pre style="background:#f6f8f4;padding:14px;border-radius:9px;overflow:auto;font-size:11px;line-height:1.55">{"devices":[{"volk":"Volk 8", "rows":[
  {"zeit_utc":"2026-10-16T00:51:32Z",
   "gewicht_kg":31.4185,"temperatur_c":18.43,
   "fft_baender":[]}
]}]}</pre><div class="action-row"><button class="btn primary" data-action="import">JSON-Datei öffnen</button><button class="btn" data-action="clear-import">Importierte Messungen löschen</button></div></section></div>
<div class="section-heading"><h2>Kanalregister</h2>${tag(ch.length+' Definitionen','blue')}</div><div class="panel table-wrap"><table class="data-table"><thead><tr><th>Quelle</th><th>Messkanal</th><th>Bezeichnung</th><th>Einheit</th><th>Verdichtung</th><th>Status</th></tr></thead><tbody>${ch.map(k=>`<tr><td>${esc(k.quelle)}</td><td><code>${esc(k.key)}</code></td><td><span class="channel-dot" style="background:${/^#[0-9a-fA-F]{6}$/.test(k.color)?k.color:'#899a7e'}"></span>${esc(k.name)}</td><td>${esc(k.unit)}</td><td>${esc(k.agg)}</td><td>${tag(k.status,k.status==='geplant'?'gray':'blue')}</td></tr>`).join('')}</tbody></table></div>
<div class="section-heading"><h2>Neuen Kanal vorschlagen</h2></div><section class="panel"><form id="channelForm" class="form-grid"><div class="form-field"><label>Quellfeld-Schlüssel</label><input name="key" placeholder="z. B. co2_ppm" maxlength="40" pattern="[A-Za-z][A-Za-z0-9_]*" required></div><div class="form-field"><label>Bezeichnung</label><input name="name" placeholder="CO₂ im Stock" maxlength="80" required></div><div class="form-field"><label>Einheit</label><input name="unit" placeholder="ppm" maxlength="20" required></div><div class="form-field"><label>Quelle</label><select name="quelle"><option>Zusatzgerät</option><option>Stockmessgerät</option><option>Umweltsensor</option></select></div><div class="form-field full"><button class="btn primary" type="submit">Als lokalen Kanalvorschlag ergänzen</button></div></form><p class="small muted" style="margin-top:12px">Ein neuer Kanal in dieser Vorschau aktiviert noch keinen echten Decoder. Für die Produktivversion müssen Messstellen, Gerätemetadaten und Gültigkeitszeiträume in PostgreSQL geführt werden.</p></section>`;}
const viewNames={stand:'Bienenstand',volk:'Volk-Cockpit',stockkarte:'Stockkarte',beute:'Beutenkonfiguration',analyse:'Analysen & Vergleich',umwelt:'Umwelt & Tracht',quellen:'Datenquellen & Kanäle'};
const views={stand:viewsStand,volk:viewsVolk,stockkarte:viewsStockkarte,beute:viewsBeute,analyse:viewsAnalyse,umwelt:viewsUmwelt,quellen:viewsQuellen};
function render(){main.innerHTML=views[data.view]();$('#breadcrumbs').textContent=(hasBeepExport?beepFixture.stand:'Teststand')+' / '+viewNames[data.view];$('#modeMark').textContent=data.mode==='demo'?'SIMULATION · ausschließlich künstliche Zeitreihen':hasBeepExport?'BEEP-Export · Offline-Test, keine Liveverbindung':'Bekannter BEEP-Messpunkt · kein Livezugriff';$('#dataToggle').textContent=data.mode==='demo'?'Realdaten anzeigen':'Musteranalyse aktivieren';document.querySelectorAll('.nav-link').forEach(b=>b.classList.toggle('active',b.dataset.view===data.view));document.title='Bienenlogger · '+viewNames[data.view];}
function queenHistory(v){
 const entries=data.queens.filter(q=>q.volk===v).sort((a,b)=>String(b.effectiveDate||'').localeCompare(String(a.effectiveDate||'')));
 const b=staticVolker[v]?.queen;
 const imported=b?`<div class="row-small"><span>BEEP-Snapshot (Zeitpunkt der königinnenbezogenen Stammdaten unbekannt): ${esc(b.name||'Ohne Namen')} · ${esc(b.year??'ohne Jahr')}</span>${tag('Original unverändert','blue')}</div>`:'';
 return imported+(entries.length?entries.map(q=>`<div class="row-small"><span>${esc(q.effectiveDate||'Datum unbekannt')} · ${esc(q.name||'Unbenannt')} · ${esc(q.recordType==='new'?'Neue Königin':'Korrektur')} · ${esc(q.source||'Lokaler Entwurf')}${q.revisions?.length?' · '+q.revisions.length+' ältere Bearbeitung(en)':''}</span><button class="btn small" data-action="edit-queen-record" data-id="${esc(q.id)}">Bearbeiten</button></div>`).join(''):'<div class="small muted">Noch keine lokalen Königinnenänderungen.</div>');
}
function queenFormValue(q,k){return esc(q?.[k]??'');}
function openQueen(mode='correct',id=''){
 const current=queenOf(data.volk)||{},stored=data.queens.find(q=>q.volk===data.volk&&q.id===id);
 const q=mode==='new'?{}:stored||current;
 const m=$('#modalRoot');
 m.innerHTML=`<div class="modal-backdrop"><section class="modal wide" role="dialog" aria-modal="true" aria-labelledby="dlgtitle"><div class="panel-head"><div><div class="eyebrow">KÖNIGIN · LOKALER ENTWURF</div><h2 id="dlgtitle">${mode==='new'?'Neue Königin':stored?'Königinnendatensatz bearbeiten':'Königinnenangaben korrigieren'} · ${esc(colonyName(data.volk))}</h2></div><button class="btn small" data-action="close-modal">✕</button></div><p class="small muted">BEEP-Originaldaten bleiben unverändert. Ein Jahrgang ist kein belegtes vollständiges Geburtsdatum. Änderungen werden ausschließlich im Browser gespeichert.</p><form id="queenForm" class="form-grid"><input type="hidden" name="record_id" value="${esc(stored?.id||'')}"><input type="hidden" name="record_type" value="${mode==='new'?'new':(stored?.recordType||'correct')}">
 <div class="form-field"><label>Königinnenname</label><input name="name" maxlength="100" value="${queenFormValue(q,'name')}" placeholder="Noch unbekannt"></div>
 <div class="form-field"><label>Gültig ab / Einweiselung</label><input type="date" name="effectiveDate" value="${queenFormValue(q,'effectiveDate')}"></div>
 <div class="form-field"><label>Geburtsjahr (falls nur Jahr bekannt)</label><input type="number" name="year" min="1900" max="2100" value="${queenFormValue(q,'year')}"></div>
 <div class="form-field"><label>Genaues Geburtsdatum (nur falls belegt)</label><input type="date" name="birth_date" value="${queenFormValue(q,'birth_date')}"></div>
 <div class="form-field"><label>Zeichenfarbe (HEX)</label><input name="color" maxlength="7" placeholder="#FFFFFF oder leer" pattern="#[a-fA-F0-9]{6}" value="${queenFormValue(q,'color')}"><small>Leer = keine gesicherte Farbangabe</small></div>
 <div class="form-field"><label>Unterart / Rasse</label><input name="race" maxlength="90" value="${queenFormValue(q,'race')}"></div>
 <div class="form-field"><label>Begattet</label><select name="fertilized">${triOptions(q.fertilized)}</select></div>
 <div class="form-field"><label>Flügel geschnitten</label><select name="clipped">${triOptions(q.clipped)}</select></div>
 <div class="form-field"><label>Herkunft / Züchter</label><input name="origin" maxlength="150" value="${queenFormValue(q,'origin')}"></div>
 <div class="form-field"><label>Begattungsort</label><input name="fertilizing_location" maxlength="150" value="${queenFormValue(q,'fertilizing_location')}"></div>
 <div class="form-field"><label>Linie</label><input name="line" maxlength="100" value="${queenFormValue(q,'line')}"></div>
 <div class="form-field"><label>Stammbaum</label><input name="tree" maxlength="150" value="${queenFormValue(q,'tree')}"></div>
 <div class="form-field"><label>Mutter-Königin / Referenz</label><input name="mother" maxlength="150" value="${queenFormValue(q,'mother')}"></div>
 <div class="form-field"><label>Bewertung / Qualität</label><input name="quality" maxlength="100" value="${queenFormValue(q,'quality')}"></div><div class="form-field"><label>Zuchtziel</label><input name="goal" maxlength="150" value="${queenFormValue(q,'goal')}"></div><div class="form-field"><label>Markierung</label><input name="marker" maxlength="100" value="${queenFormValue(q,'marker')}"></div>
 <div class="form-field full"><label>Notizen / Quelle</label><textarea name="description" maxlength="2000">${queenFormValue(q,'description')}</textarea></div>
 <div class="form-field full action-row"><button type="button" class="btn" data-action="close-modal">Abbrechen</button><button type="submit" class="btn primary">${stored?'Korrektur speichern':'Königin als Testentwurf speichern'}</button></div></form></section></div>`;
 m.querySelector('input[name=name]').focus();
}
function triOptions(value){return [['','Unbekannt / nicht erfasst'],['yes','Ja'],['no','Nein']].map(([val,label])=>`<option value="${val}" ${value===val?'selected':''}>${label}</option>`).join('');}
function saveQueen(form){const f=new FormData(form);const color=String(f.get('color')||'').trim();const y=String(f.get('year')||'').trim(),birth=String(f.get('birth_date')||'').trim();
 if(color&&!/^#[0-9a-f]{6}$/i.test(color))return toast('Farbe nur als #RRGGBB oder leer.');
 if(y&&(!/^\d{4}$/.test(y)||Number(y)<1900||Number(y)>2100))return toast('Jahrgang ungültig.');
 if(birth&&(!/^\d{4}-\d{2}-\d{2}$/.test(birth)||!Number.isFinite(Date.parse(birth))))return toast('Geburtsdatum ungültig.');
 if(y&&birth&&Number(birth.slice(0,4))!==Number(y))return toast('Geburtsjahr und Geburtsdatum widersprechen sich.');
 const id=String(f.get('record_id')||'');const prior=data.queens.find(q=>q.id===id&&q.volk===data.volk);
 const fields=['name','effectiveDate','birth_date','race','fertilized','clipped','origin','fertilizing_location','line','tree','mother','quality','goal','marker','description'];
 const next={id:prior?.id||'q-'+localId(),volk:data.volk,recordType:prior?.recordType||String(f.get('record_type')),source:'Lokaler Testentwurf',editedAt:new Date().toISOString(),year:y?Number(y):null,color:color||null};
 fields.forEach(k=>{next[k]=String(f.get(k)||'').trim()||null;});
 next.revisions=prior?[...(prior.revisions||[]),{...prior,revisions:undefined}]:[];
 if(prior)data.queens.splice(data.queens.indexOf(prior),1);
 data.queens.push(next);persist();closeModal();render();toast('Königinnenangabe lokal gespeichert – BEEP-Original unverändert.');
}
function openColony(){const v=data.volk,info=colonyOf(v);const m=$('#modalRoot');m.innerHTML=`<div class="modal-backdrop"><section class="modal" role="dialog" aria-modal="true" aria-labelledby="dlgtitle"><div class="panel-head"><div><div class="eyebrow">VOLK · LOKALER ENTWURF</div><h2 id="dlgtitle">Volk bearbeiten: ${esc(colonyName(v))}</h2></div><button class="btn small" data-action="close-modal">✕</button></div><p class="small muted">Die biologische Volk-ID und BEEP-Hive-ID bleiben unverändert. Keine Synchronisierung mit BEEP.</p><form id="colonyForm" class="form-grid"><div class="form-field full"><label>Anzeigename</label><input name="name" required maxlength="100" value="${esc(info.name)}"></div><div class="form-field full"><label>Statusbeschreibung</label><input name="status" maxlength="150" value="${esc(info.status||'')}" placeholder="Nur belegten Status eintragen"></div><div class="form-field full"><label>Notiz</label><textarea name="notes" maxlength="1500">${esc(info.notes||'')}</textarea></div><div class="form-field full action-row"><button type="button" class="btn" data-action="close-modal">Abbrechen</button><button class="btn primary" type="submit">Lokal speichern</button></div></form></section></div>`;m.querySelector('input[name=name]').focus();}
function saveColony(form){const f=new FormData(form),name=String(f.get('name')||'').trim();if(!name||name.length>100)return toast('Gültigen Volknamen eingeben.');data.colonyDrafts[data.volk]={name,status:String(f.get('status')||'').trim(),notes:String(f.get('notes')||'').trim(),source:'Lokaler Testentwurf'};persist();closeModal();render();toast('Volk-Stammdaten als lokaler Entwurf gespeichert.');}
function taxonomyInputs(existing=[],templateId=null){
 const chosen=data.nativeTemplates.find(x=>x.id===templateId)||currentTemplate();
 const paths=Native.paths(data.nativeNodes),values={};
 for(const e of existing){
   const id=e.category_id!=null?String(e.category_id):data.nativeNodes.find(n=>paths.get(n.id)===e.label)?.id;
   if(id)values[id]=e.value;
 }
 return Native.renderFields(data.nativeNodes,chosen?.category_ids||[],values);
}
function getTaxonomyFields(form){
 const chosen=data.nativeTemplates.find(t=>t.id===form.dataset.checklistId)||currentTemplate();
 const result=Native.collect(form,data.nativeNodes,chosen?.category_ids||[]);
 if(result.errors.length)throw Error(result.errors.join('; '));
 const path=Native.paths(data.nativeNodes);
 return Object.entries(result.values).map(([id,value])=>({category_id:id,label:path.get(id)||id,value}));
}
function templatePanel(){const t=currentTemplate();return `<div class="form-field full"><label>Checklisten-Vorlage</label><select name="nativeChecklist" id="nativeChecklist">${data.nativeTemplates.map(x=>`<option value="${esc(x.id)}" ${t?.id===x.id?'selected':''}>${esc(x.name)}</option>`).join('')}</select><small>Die Reihenfolge, Kategorien und Feldtypen stammen aus der ausgewählten Vorlage. Bei Vorlagenwechsel werden noch nicht gespeicherte Eingaben zurückgesetzt.</small></div>`;}
function manageTemplates(id=''){
 const selected=id==='__new__'?null:(data.nativeTemplates.find(t=>t.id===id)||currentTemplate()), nodes=data.nativeNodes;
 const leafs=nodes.filter(n=>n.input!=='label' && !(['select','options','list'].includes(nodes.find(x=>x.id===n.parent)?.input))).sort((a,b)=>{const ia=selected?.category_ids?.indexOf(a.id)??-1,ib=selected?.category_ids?.indexOf(b.id)??-1;return (ia<0?9999:ia)-(ib<0?9999:ib);});
 const paths=Native.paths(nodes),ids=new Set(selected?.category_ids||[]);
 const m=$('#modalRoot');m.innerHTML=`<div class="modal-backdrop"><section class="modal wide" role="dialog" aria-modal="true" aria-labelledby="dlgtitle"><div class="panel-head"><h2 id="dlgtitle">Bienenlogger-Checklisten verwalten</h2><button class="btn" data-action="close-modal">✕</button></div><p class="small muted">Wie bei BEEP: Kategorien und Reihenfolge sind pro Vorlage frei wählbar. Änderungen bleiben lokal; kein Zugriff auf BEEP.</p><form id="nativeTemplateForm"><input name="template_id" type="hidden" value="${esc(selected?.id||'')}"><div class="form-grid"><div class="form-field full"><label>Name</label><input name="template_name" value="${esc(selected?.name||'')}" required maxlength="100"></div></div><div class="native-tree">${leafs.map(n=>`<div class="native-order-row"><label class="checkline"><input type="checkbox" name="selected_category" value="${esc(n.id)}" ${ids.has(n.id)?'checked':''}>${esc(paths.get(n.id)||n.label)} <small>${esc(n.input)}${n.required?' · Pflichtfeld':''}</small></label><div><button type="button" class="btn small" data-action="native-up" aria-label="Kategorie nach oben">↑</button><button type="button" class="btn small" data-action="native-down" aria-label="Kategorie nach unten">↓</button></div></div>`).join('')}</div><div class="form-field full action-row"><button class="btn" type="button" data-action="new-native-template">Neue Vorlage</button><button class="btn" type="button" data-action="delete-native-template">Aktive Vorlage löschen</button><button class="btn primary" type="submit">Checkliste lokal speichern</button></div></form></section></div>`;m.querySelector('input[name="template_name"]').focus();
}
function saveTemplate(form){
 const f=new FormData(form),name=String(f.get('template_name')||'').trim();if(!name)return toast('Name erforderlich');
 const ids=f.getAll('selected_category').map(String);
 if(!ids.length)return toast('Bitte mindestens eine Kategorie wählen.');
 const old=data.nativeTemplates.find(x=>x.id===f.get('template_id'));
 const template=Native.template(name,ids,old?.id||('local-'+localId()));
 if(old){template.revisions=[...(old.revisions||[]),{...old,revisions:undefined}];data.nativeTemplates.splice(data.nativeTemplates.indexOf(old),1);}
 data.nativeTemplates.push(template);data.activeNativeTemplate=template.id;persist();closeModal();render();toast('Bienenlogger-Checkliste lokal gespeichert.');
}
async function importNativeSchema(file){
 if(!file||file.size>4*1024*1024)return toast('Maximal 4 MB JSON-Katalog');
 try{
  const raw=JSON.parse(await file.text());const nodes=Native.prepare(raw);const report=Native.catalogReport(nodes);
  if(!nodes.length)throw Error('Keine Kategorien');
  const imported=Native.checklistNormalize(raw,nodes);
  data.nativeNodes=nodes;data.nativeTemplates=imported.length?imported:[Native.template('Alle importierten Kategorien',nodes.filter(n=>n.input!=='label'&&!(['select','options','list'].includes(nodes.find(p=>p.id===n.parent)?.input))).map(n=>n.id),'native-import')];
  data.activeNativeTemplate=data.nativeTemplates[0].id;persist();render();toast(nodes.length+' Kategorien importiert. '+(report.blocked.length?report.blocked.length+' Feldtypen/Optionen noch nicht nutzbar.':'Keine blockierten Felder.'));
 }catch(e){toast('Katalogimport fehlgeschlagen: '+e.message);}
}
function openInspection(id=''){
 const orig=id?(importedStockcards.find(e=>e.id===id&&e.volk===data.volk)||data.inspections.find(e=>e.id===id&&e.volk===data.volk)):null;
 const origTemplate=data.nativeTemplates.find(t=>t.id===orig?.checklist_id);if(origTemplate)data.activeNativeTemplate=origTemplate.id;
 const isBeep=Boolean(orig&&String(orig.source||'').startsWith('BEEP-'));
 const today=berlinToday(),date=orig?.date||today, modal=$('#modalRoot');
 modal.innerHTML=`<div class="modal-backdrop"><section class="modal wide" role="dialog" aria-modal="true" aria-labelledby="dlgtitle"><div class="panel-head"><div><div class="eyebrow">STOCKKARTE · ${isBeep?'KORREKTURENTWURF':'LOKALER TESTENTWURF'}</div><h2 id="dlgtitle">${orig?'Eintrag bearbeiten':'Durchsicht erfassen'} · ${esc(colonyName(data.volk))}</h2></div><button class="btn small" data-action="close-modal" aria-label="Schließen">✕</button></div><p class="small muted">${isBeep?'Das importierte Original bleibt unverändert, eine referenzierte lokale Korrektur wird angelegt.':'Nur lokale Bearbeitung. Ohne BEEP-Synchronisierung.'}</p><form id="inspectionForm" data-checklist-id="${esc(currentTemplate()?.id||'')}" class="form-grid"><input type="hidden" name="entry_id" value="${esc(orig&&!isBeep?orig.id:'')}"><input type="hidden" name="source_inspection_id" value="${isBeep?esc(id):esc(orig?.sourceInspectionId||'')}">
 <div class="form-field"><label>Datum</label><input name="date" type="date" value="${esc(date)}" required></div><div class="form-field"><label>Art des Eintrags</label><select name="type">${['Durchsicht','Behandlung','Fütterung','Honigernte','Beutenänderung','Königinnenwechsel','Sonstiges'].map(t=>`<option ${orig?.type===t?'selected':''}>${t}</option>`).join('')}</select></div>
 <div class="form-field"><label>Gesamteindruck</label><select name="mood">${[['','Nicht bewertet'],['gut','Gut'],['beobachten','Beobachten'],['Handlungsbedarf','Handlungsbedarf']].map(([v,t])=>`<option value="${v}" ${orig?.mood===v?'selected':''}>${t}</option>`).join('')}</select></div>
 <div class="form-field"><label>Handlungsbedarf</label><select name="attention">${triOptions(orig?.needs_attention===true?'yes':orig?.needs_attention===false?'no':'')}</select></div>
 <div class="form-field"><label>Erinnerung / Termin (optional)</label><input type="date" name="reminderDate" value="${esc(orig?.reminder?.at?.slice(0,10)||'')}"></div>
 <div class="form-field"><label>Erinnerungstext</label><input name="reminderText" maxlength="400" value="${esc(orig?.reminder?.text||'')}"></div>
 <div class="form-field full"><h3>Persönliche Prüfliste</h3>${data.checklist.map(x=>`<label class="checkline"><input type="checkbox" name="flag" value="${esc(x)}" ${(orig?.flags||[]).includes(x)?'checked':''}> ${esc(x)}</label>`).join('')}</div>
 ${templatePanel()}<div class="form-field full"><h3>Ausgewählte Kategorien · nach BEEP-Datenmodell</h3><p class="small muted">Originale Kategorie-IDs, verschachtelte Gruppen und Eingabetypen werden berücksichtigt, wenn ein vollständiger Katalog importiert wurde. Das Excel allein enthält keine kompletten Auswahlmöglichkeiten.</p><div id="nativeFields">${taxonomyInputs(orig?.fields||[])}</div></div>
 <div class="form-field full"><label>Notiz</label><textarea name="summary" maxlength="4000">${esc(orig?.summary||'')}</textarea></div>
 <div class="form-field full action-row"><button type="button" class="btn" data-action="close-modal">Abbrechen</button><button class="btn primary" type="submit">${orig?'Änderung als Entwurf speichern':'Als Testentwurf speichern'}</button></div></form></section></div>`;
 modal.querySelector('input[name=date]').focus();
}
function closeModal(){$('#modalRoot').replaceChildren();}
function saveInspection(form){
 const f=new FormData(form),date=String(f.get('date')||'');if(!/^\d{4}-\d{2}-\d{2}$/.test(date))return toast('Ungültiges Datum');
 let fields;try{fields=getTaxonomyFields(form);}catch(e){return toast(e.message);}
 const flags=f.getAll('flag').map(String);const old=data.inspections.find(e=>e.id===f.get('entry_id')&&e.volk===data.volk);
 const attention=String(f.get('attention')||'');const summary=String(f.get('summary')||'').trim();
 const reminderDate=String(f.get('reminderDate')||'');const reminderText=String(f.get('reminderText')||'').trim();
 const row={id:old?.id||localId(),volk:data.volk,date,type:String(f.get('type')),
 mood:String(f.get('mood')||''),needs_attention:attention==='yes'?true:attention==='no'?false:null,
 flags,fields,checklist_id:form.dataset.checklistId||null,taxonomyValues:Object.fromEntries(fields.map(x=>[x.category_id,x.value])),summary,reminder:reminderDate||reminderText?{at:reminderDate||null,text:reminderText}:null,
 sourceInspectionId:String(f.get('source_inspection_id')||'')||null,source:'Lokaler Testentwurf',updatedAt:new Date().toISOString(),
 revisions:old?[...(old.revisions||[]),{...old,revisions:undefined}]:[]};
 if(old)data.inspections.splice(data.inspections.indexOf(old),1);
 data.inspections.push(row);persist();closeModal();render();toast('Stockkarteneintrag lokal gespeichert; BEEP-Original unverändert.');
}
function saveHive(form){const f=new FormData(form);const brood=Number(f.get('brood')),honey=Number(f.get('honey')),frames=f.get('frames')===''?null:Number(f.get('frames'));const date=String(f.get('date'));if(!Number.isInteger(brood)||!Number.isInteger(honey)||brood<0||honey<0||brood>8||honey>8||brood+honey<1){toast('Eine aufgebaute Beute benötigt mindestens eine Zarge (max. 8 je Art).');return;}if(frames!==null&&(!Number.isInteger(frames)||frames<0||frames>100)){toast('Rähmchenanzahl ungültig.');return;}const entry={volk:data.volk,date,typ:String(f.get('typ')||''),brood,honey,frames,note:String(f.get('note')||'').trim(),source:'Lokaler Testentwurf'};data.hiveDrafts.push(entry);data.inspections.push({id:'hive-local-'+Date.now(),volk:data.volk,date,type:'Beutenänderung',mood:'',flags:[],varroa:null,summary:entry.note||`Beutenkonfiguration: ${brood} Brut- und ${honey} Honigzargen`,source:'Lokaler Testentwurf'});persist();render();toast('Beutenänderung als lokaler Stockkartenentwurf gespeichert.');}
function saveChecklist(form){const item=String(new FormData(form).get('item')||'').trim();if(item.length<3||item.length>90)return toast('Checklistenpunkt: 3 bis 90 Zeichen.');if(data.checklist.length>=30)return toast('Maximal 30 Testmerkmale.');if(data.checklist.some(x=>x.toLowerCase()===item.toLowerCase()))return toast('Merkmal bereits vorhanden.');data.checklist.push(item);persist();render();toast('Checklistenmerkmal lokal ergänzt.');}
function saveChannel(form){const f=new FormData(form),key=String(f.get('key')||'').trim();if(!/^[A-Za-z][A-Za-z0-9_]{0,39}$/.test(key)){toast('Ungültiger Kanalname.');return;}if(defaultChannels.concat(data.channels).some(c=>c.key===key)){toast('Dieser Kanal ist bereits registriert.');return;}data.channels.push({key,name:String(f.get('name')||'').slice(0,80),unit:String(f.get('unit')||'').slice(0,20),quelle:String(f.get('quelle')),agg:'noch festzulegen',status:'Testvorschlag',color:'#789985'});persist();render();toast('Neuer Kanalvorschlag ergänzt.');}
function download(obj,filename){const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function validateRows(rows){
 if(!Array.isArray(rows))return [];
 const numeric=v=>(v===null||v===undefined||(typeof v==='string'&&!v.trim())||typeof v==='boolean'||!Number.isFinite(Number(v)))?null:Number(v);
 return rows.slice(-15000).map(r=>{
  if(!r||typeof r!=='object'||typeof r.zeit_utc!=='string'||!Number.isFinite(Date.parse(r.zeit_utc)))return null;
  const item={zeit_utc:new Date(r.zeit_utc).toISOString()};
  for(const k of ['gewicht_kg','gewicht_roh','temperatur_c','batterie_v'])item[k]=numeric(r[k]);
  item.fft_baender=Array.isArray(r.fft_baender)?r.fft_baender.slice(0,24).map(b=>{
   if(!b||typeof b!=='object')return null;
   const from=numeric(b.von_hz),to=numeric(b.bis_hz),value=numeric(b.wert);
   return from!==null&&to!==null&&value!==null&&from>=0&&to>from&&value>=0?{von_hz:from,bis_hz:to,wert:value}:null;
  }).filter(Boolean):[];
  return item;
 }).filter(Boolean);
}
function importJson(file){if(file.size>12*1024*1024)return toast('JSON-Datei zu groß (maximal 12 MB).');file.text().then(txt=>{let obj=JSON.parse(txt);if(!Array.isArray(obj.devices))throw new Error('Erwartet JSON mit Feld "devices".');let found=0;for(const dev of obj.devices){let v=String(dev.volk||'').match(/\b(5|8)\b/)?.[1];if(!v)continue;const rows=validateRows(dev.rows);if(!rows.length)continue;data.imports[v]=rows;found+=rows.length;}if(!found)throw new Error('Keine zuordenbaren Messpunkte für Volk 5 oder 8.');data.mode='real';persist();render();toast(found+' Messwerte lokal importiert. Keine Daten an Server übertragen.');}).catch(err=>toast('Importfehler: '+err.message));}
let activeActionId='';function invokeAction(name){switch(name){case 'view-cards':standLayout='kacheln';render();break;case 'view-table':standLayout='liste';render();break;case 'sort-nr':standSort='nr';render();break;case 'sort-gewicht':standSort='gewicht';render();break;case 'sort-status':standSort='status';render();break;case 'toggle-spark':standMetric.spark=!standMetric.spark;render();break;case 'toggle-temp':standMetric.temp=!standMetric.temp;render();break;case 'toggle-audio':standMetric.audio=!standMetric.audio;render();break;case 'manage-templates':manageTemplates();break;
 case 'new-native-template':manageTemplates('__new__');break;
 case 'delete-native-template':if(data.nativeTemplates.length<=1){toast('Mindestens eine Vorlage behalten.');break;}if(confirm('Aktive Checkliste lokal löschen?')){data.nativeTemplates=data.nativeTemplates.filter(t=>t.id!==data.activeNativeTemplate);data.activeNativeTemplate=data.nativeTemplates[0].id;persist();manageTemplates();}break;
 case 'import-native-schema':{let input=document.createElement('input');input.type='file';input.accept='.json,application/json';input.addEventListener('change',()=>importNativeSchema(input.files[0]));input.click();break;}
 case 'new-inspection':openInspection();break;case 'edit-colony':openColony();break;case 'edit-queen':openQueen('correct');break;case 'new-queen':openQueen('new');break;case 'edit-queen-record':openQueen('correct',activeActionId);break;case 'correct-beep':openInspection(activeActionId);break;case 'edit-inspection':openInspection(activeActionId);break;case 'close-modal':closeModal();break;case 'import':{let input=document.createElement('input');input.type='file';input.accept='.json,application/json';input.addEventListener('change',()=>{if(input.files[0])importJson(input.files[0]);});input.click();break;}case 'export':download({created_at:new Date().toISOString(),marker:'LOKALE TESTENTWÜRFE – NICHT BEEP',inspections:data.inspections,hiveDrafts:data.hiveDrafts,queens:data.queens,colonyDrafts:data.colonyDrafts,channels:data.channels,checklist:data.checklist,imports:data.imports,nativeNodes:data.nativeNodes,nativeTemplates:data.nativeTemplates},'bienenlogger-testentwuerfe.json');break;case 'clear-import':if(confirm('Alle lokal importierten Messdaten löschen? Die Vorlage bleibt erhalten.')){data.imports={};persist();render();}break;}}
document.addEventListener('click',e=>{const n=e.target.closest('[data-view],[data-volk],[data-choose-volk],[data-days],[data-action]');if(!n)return;
 if(['native-up','native-down'].includes(n.dataset.action)){
  const row=n.closest('.native-order-row');if(!row)return;
  const other=n.dataset.action==='native-up'?row.previousElementSibling:row.nextElementSibling;
  if(other?.classList.contains('native-order-row')){
   if(n.dataset.action==='native-up')other.before(row);else other.after(row);
  }
  return;
 }
 if(n.dataset.view){data.view=n.dataset.view;render();}else if(n.dataset.volk){data.volk=n.dataset.volk;data.view='volk';render();}else if(n.dataset.chooseVolk){data.volk=n.dataset.chooseVolk;render();}else if(n.dataset.days){data.days=Number(n.dataset.days);render();}else if(n.dataset.action){activeActionId=n.dataset.id||'';invokeAction(n.dataset.action);} });
document.addEventListener('change',e=>{
 if(e.target.id==='colonyPicker'){data.volk=e.target.value;render();}
 if(e.target.id==='nativeChecklist'){
  const form=e.target.closest('form');data.activeNativeTemplate=e.target.value;form.dataset.checklistId=e.target.value;
  const id=form.querySelector('[name="entry_id"]')?.value||form.querySelector('[name="source_inspection_id"]')?.value||'';
  const prior=data.inspections.find(x=>x.id===id)||importedStockcards.find(x=>x.id===id);
  form.querySelector('#nativeFields').innerHTML=taxonomyInputs(prior?.fields||[],e.target.value);
  persist();
 }
});
document.addEventListener('submit',e=>{if(!['inspectionForm','hiveForm','channelForm','checklistForm','queenForm','colonyForm','nativeTemplateForm'].includes(e.target.id))return;e.preventDefault();if(e.target.id==='inspectionForm')saveInspection(e.target);if(e.target.id==='nativeTemplateForm')saveTemplate(e.target);if(e.target.id==='queenForm')saveQueen(e.target);if(e.target.id==='colonyForm')saveColony(e.target);if(e.target.id==='hiveForm')saveHive(e.target);if(e.target.id==='channelForm')saveChannel(e.target);if(e.target.id==='checklistForm')saveChecklist(e.target);});
$('#dataToggle').addEventListener('click',()=>{data.mode=data.mode==='demo'?'real':'demo';render();toast(data.mode==='demo'?'Ausschließlich synthetische Musteranalyse aktiviert.':'Musteranalyse deaktiviert.');});

document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();});
render();
})();
