/* SPDX-License-Identifier: GPL-3.0-or-later
 * Authenticated environment vertical slice. No local measurements or entity IDs.
 */
(()=>{
'use strict';
const API='/api/v1/umwelt',AUTH='/api/v1/stockkarte/session';
const POLL_MS=30000;
let root=null,session=null,sites=[],site=null,timer=null,generation=0,loading=false;
let days=1,fixed=null,selected=null,charts=[],latestSeries=[];
let activeRequest=null,registrySignature='';
const timeLabel=t=>new Intl.DateTimeFormat('de-DE',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',timeZoneName:'shortOffset'}).format(new Date(t));
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function make(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function clearCharts(){for(const chart of charts)chart.dispose();charts=[];}
function reload(rebuild=true){activeRequest?.abort();generation++;loading=false;clearCharts();refresh(generation,rebuild);}
function unmount(){activeRequest?.abort();generation++;clearInterval(timer);timer=null;clearCharts();root=null;loading=false;}
async function request(url,{method='GET',body,csrf,signal}={}){
 const headers={Accept:'application/json'};
 if(body!==undefined)headers['Content-Type']='application/json';
 if(csrf)headers['X-CSRF-Token']=csrf;
 const response=await fetch(url,{method,headers,signal,credentials:'same-origin',cache:'no-store',redirect:'error',body:body===undefined?undefined:JSON.stringify(body)});
 let value;try{value=await response.json();}catch{value={};}
 if(!response.ok){const error=Error(response.status===401?'Sitzung fehlt oder ist abgelaufen':response.status===404?'Stand nicht freigegeben oder nicht vorhanden':response.status===503?'Umwelt-Teststack noch nicht eingerichtet':typeof value.detail==='string'?value.detail:'Anfrage fehlgeschlagen ('+response.status+')');error.status=response.status;throw error;}
 return value;
}
function notice(text){if(root){const target=root.querySelector('#umStatus');if(target)target.textContent=text;}}
function loginForm(message=''){
 if(!root)return;
 generation++;loading=false;
 activeRequest?.abort();
 clearInterval(timer);clearCharts();session=null;
 root.replaceChildren();
 root.append(make('p',message||'Für freigegebene Umweltmessreihen am Testserver anmelden.','note'));
 const form=make('form',undefined,'um-login');form.id='umLogin';
 for(const [name,label,type] of [['username','Benutzername','text'],['password','Passwort','password']]){
  const field=make('label',label);const input=make('input');input.name=name;input.type=type;input.required=true;input.autocomplete=name==='username'?'username':'current-password';field.append(input);form.append(field);
 }
 const submit=make('button','Anmelden','btn primary');submit.type='submit';form.append(submit);
 const error=make('p','');error.setAttribute('role','alert');form.append(error);
 form.addEventListener('submit',async event=>{
  event.preventDefault();submit.disabled=true;
  const username=form.elements.username.value.trim(),password=form.elements.password.value;
  form.elements.password.value='';
  const token=generation;
  try{session=await request(AUTH+'/login',{method:'POST',body:{username,password}});if(token!==generation)return;await initialize(token);}
  catch(exc){if(token===generation)error.textContent=exc.message;}finally{submit.disabled=false;}
 });
 root.append(form);
}
function buildControls(){
 clearCharts();root.replaceChildren();
 const toolbar=make('div',undefined,'toolbar um-controls');
 const who=make('span','Angemeldet: '+session.username);toolbar.append(who);
 const logout=make('button','Abmelden','btn');logout.id='umLogout';logout.type='button';
 logout.addEventListener('click',async()=>{try{await request(AUTH+'/logout',{method:'POST',csrf:session.csrf_token});loginForm('Abgemeldet.');}catch(exc){notice(exc.message);}});toolbar.append(logout);
 const label=make('label','Stand '),select=make('select');select.id='umStand';select.setAttribute('aria-label','Freigegebenen Umweltstand auswählen');
 for(const item of sites){const o=make('option',item.name);o.value=String(item.id);select.append(o);}select.value=String(site);label.append(select);toolbar.append(label);
 select.addEventListener('change',()=>{site=Number(select.value);selected=null;reload();});
 root.append(toolbar);
 const mode=make('p','Quellen werden geprüft …','note');mode.id='umMode';root.append(mode);
 const ranges=make('div',undefined,'toolbar');
 for(const [n,labelText] of [[1,'24 h'],[7,'7 Tage'],[30,'30 Tage'],[0,'Saison']]){
  const button=make('button',labelText,'btn');button.type='button';button.addEventListener('click',()=>{days=n;fixed=null;reload();});ranges.append(button);
 }
 const custom=make('form',undefined,'um-range');
 for(const [name,labelText,value] of [['from','Von (UTC)',new Date(Date.now()-86400000)],['to','Bis (UTC)',new Date()]]){
  const labelNode=make('label',labelText);const input=make('input');input.name=name;input.type='datetime-local';input.required=true;input.value=value.toISOString().slice(0,16);labelNode.append(input);custom.append(labelNode);
 }
 const apply=make('button','Zeitraum anwenden','btn');apply.type='submit';custom.append(apply);
 custom.addEventListener('submit',e=>{e.preventDefault();fixed=[custom.elements.from.value+'Z',custom.elements.to.value+'Z'];reload();});
 root.append(ranges,custom);
 const fields=make('fieldset',undefined,'um-fields');fields.id='umFields';fields.append(make('legend','Messkanäle'));root.append(fields);
 const status=make('p','','small muted');status.id='umStatus';status.setAttribute('role','status');root.append(status);
 const quality=make('div');quality.id='umSources';root.append(quality);
 const plots=make('div',undefined,'um-plots');plots.id='umPlots';root.append(plots);
 root.append(make('p','Automatische Abfrage alle 30 Sekunden. Rohwerte, keine Interpolation oder Regenzähler-Summe. Zeitangaben: Europe/Berlin. Andere Ansichten bleiben bis R3 ausdrücklich Offline-Prototypen.','small muted'));
}
function windowParams(){
 if(fixed)return fixed;
 const end=new Date(),start=days?new Date(end.getTime()-days*86400000):new Date(Date.UTC(end.getUTCFullYear(),0,1));
 return [start.toISOString(),end.toISOString()];
}
function plotData(points,interval){
 const data=[];let previous=null;
 for(const point of points){
  const time=Date.parse(point.time);
  if(point.gap_before||(previous!==null&&!point.bucket&&interval&&time-previous>interval*2500)){
   // This null is a line break, explicitly not a synthetic observation.
   data.push({value:[previous+1,null],meta:{gap:true}});
  }
  data.push({value:[time,point.value],meta:point});previous=time;
 }
 return data;
}
function renderPlots(series){
 clearCharts();const plots=root.querySelector('#umPlots');plots.replaceChildren();
 const groups=new Map();
 for(const item of series){
  if(!selected.has(item.channel.id))continue;
  const key=item.channel.profile+' / '+item.channel.unit;
  if(!groups.has(key))groups.set(key,[]);groups.get(key).push(item);
 }
 if(!groups.size){plots.append(make('p','Keine ausgewählten Messkanäle.','empty'));return;}
 for(const [key,items] of groups){
  const section=make('section',undefined,'panel');section.append(make('h2',(items[0].channel.profile==='boden'?'Boden':'Wetter')+' · '+items[0].channel.unit));
  const summaries=items.map(item=>item.channel.name+': '+item.summary.source_points+' Quellwerte, '+item.summary.missing+' fehlend, '+(item.summary.method==='raw'?'Rohwerte vollständig':item.summary.rendered_points+' Originalpunkte aus Min/Max-Intervallen ('+item.summary.bucket_seconds+' s)'));
  section.append(make('p',summaries.join(' · '),'small muted'));
  if(!items.some(s=>s.points.some(p=>p.value!==null))){section.append(make('p','Keine Messwerte im ausgewählten Zeitraum.','empty'));plots.append(section);continue;}
  const div=make('div',undefined,'um-chart');div.dataset.unit=items[0].channel.unit;div.setAttribute('role','img');div.setAttribute('aria-label',items.map(i=>i.channel.name).join(', '));section.append(div);plots.append(section);
  const chart=window.echarts.init(div);charts.push(chart);
  chart.setOption({animation:false,aria:{enabled:true},grid:{left:65,right:25,top:70,bottom:75,containLabel:true},
   legend:{type:'scroll',top:5},toolbox:{feature:{dataZoom:{yAxisIndex:'none'},restore:{}}},
   xAxis:{type:'time',axisLabel:{formatter:value=>new Intl.DateTimeFormat('de-DE',{timeZone:'Europe/Berlin',day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}).format(new Date(value))}},
   yAxis:{type:'value',name:items[0].channel.unit,scale:true},dataZoom:[{type:'inside'},{type:'slider'}],
   tooltip:{trigger:'axis',confine:true,formatter:params=>params.map(p=>{
    const point=p.data?.meta;if(!point||point.gap)return '';
    const item=items.find(i=>String(i.channel.id)===p.seriesId),channel=item?.channel;
    const bucket=point.bucket;
    return escape(p.seriesName)+'<br>'+escape(timeLabel(point.time))+' · '+(point.value===null?'fehlend':escape(point.value))+' '+escape(items[0].channel.unit)+'<br>Kanal '+escape(channel?.id)+' · Gerät '+escape(channel?.device_name)+(channel?.depth_cm?' · Tiefe '+escape(channel.depth_cm)+' cm':'')+' · Position '+escape(channel?.position_id)+'<br>Quelle: '+escape(point.source)+' · '+(point.synthetic?'synthetisch':'Messquelle')+' · '+escape(point.time_quality)+' · Revision '+point.revision+(point.quality.length?'<br>QC: '+escape(point.quality.join(', ')):'')+(bucket?'<br>Min/Max-Intervall '+escape(timeLabel(bucket.start))+' – '+escape(timeLabel(bucket.end))+'<br>'+bucket.count+' Quellwerte · '+bucket.missing+' fehlend · Min '+escape(bucket.minimum)+' / Max '+escape(bucket.maximum)+'<br>Intervall-QC: '+escape(bucket.quality.join(', ')||'keine')+' · Quellen: '+escape(bucket.sources.join(', ')):'');
   }).filter(Boolean).join('<hr>')},
   series:items.map(item=>({id:String(item.channel.id),name:items.filter(other=>other.channel.name===item.channel.name).length>1?item.channel.name+' · '+item.channel.device_name:item.channel.name,type:item.channel.display==='balken'?'bar':item.channel.display==='punkte'?'scatter':'line',
    step:item.channel.display==='stufe'?'end':undefined,connectNulls:false,smooth:false,showSymbol:true,symbolSize:5,
    data:plotData(item.points,item.channel.interval_seconds)}))});
 }
}
async function loadEcharts(){
 if(window.echarts)return;
 await new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='vendor/echarts.min.js';script.onload=resolve;script.onerror=()=>reject(Error('ECharts konnte nicht geladen werden'));document.head.append(script);});
}
async function completeSeries(params,signal){
 // One fixed query window per poll. Never render incomplete pages as success.
 for(let attempt=0;attempt<2;attempt++){
  let cursor=null,first=null,count=0,pages=0;const series=new Map(),seen=new Set();
  try{
   do{
    if(++pages>8)throw Error('Diagramm überschreitet das Seitenbudget; keine vollständige Anzeige.');
    const query=new URLSearchParams(params);if(cursor)query.set('cursor',cursor);
    const result=await request(API+'/zeitreihen?'+query,{signal});
    if(result.version!==2||result.offset!==count||result.total_points>40000)throw Error('Inkonsistente Diagrammseite.');
    if(!first){first=result;for(const item of result.series)series.set(item.channel.id,{...item,points:[]});}
    if(result.snapshot!==first.snapshot||result.total_points!==first.total_points||result.source_points!==first.source_points)throw Error('Diagramm-Snapshot während Paging verändert.');
    let received=0;
    for(const item of result.series){
     const target=series.get(item.channel.id);if(!target)throw Error('Kanalregister während Paging verändert.');
     for(const point of item.points){
      const key=item.channel.id+':'+point.time;
      if(seen.has(key)||target.points.length&&Date.parse(target.points.at(-1).time)>=Date.parse(point.time))throw Error('Doppelte oder unsortierte Diagrammpunkte.');
      seen.add(key);target.points.push(point);received++;
     }
    }
    if(received!==result.returned_points||result.next_cursor&&!received||result.complete!==!result.next_cursor)throw Error('Unvollständige Diagrammseite.');
    count+=received;cursor=result.next_cursor;
    if(cursor)notice('Lade Folgeseite '+(pages+1)+' · '+count+' von '+first.total_points+' Diagrammpunkten · noch unvollständig');
   }while(cursor);
   if(count!==first.total_points)throw Error('Diagrammpunkte fehlen nach Paging.');
   for(const item of series.values()){
    if(item.summary.last_time&&Date.parse(item.points.at(-1)?.time)!==Date.parse(item.summary.last_time))throw Error('Jüngster Quellwert fehlt.');
   }
   return {...first,series:[...series.values()],pages};
  }catch(error){if(error.status===410&&!attempt){notice('Snapshot abgelaufen; Abfrage wird einmal neu begonnen.');continue;}throw error;}
 }
}
function renderRegistry(registry,rebuild){
 if(selected===null)selected=new Set(registry.length<=30?registry.map(c=>c.id):[]);
 const ids=new Set(registry.map(c=>c.id));selected=new Set([...selected].filter(id=>ids.has(id)));
 const signature=JSON.stringify(registry);
 if(!rebuild&&signature===registrySignature)return;
 registrySignature=signature;
 const fields=root.querySelector('#umFields');fields.replaceChildren(make('legend','Messkanäle (höchstens 30 pro Abfrage)'));
 for(const channel of registry){
  const label=make('label'),input=make('input');input.type='checkbox';input.checked=selected.has(channel.id);input.value=String(channel.id);
  input.addEventListener('change',()=>{input.checked?selected.add(channel.id):selected.delete(channel.id);reload(false);});
  label.append(input,document.createTextNode(channel.name+' ('+channel.unit+' · '+channel.device_name+')'));fields.append(label);
 }
}
async function refresh(token,rebuild=false){
 if(!root||token!==generation||loading)return;loading=true;
 const controller=new AbortController();activeRequest=controller;
 try{
  notice('Datenabfrage läuft · Anzeige wird erst nach vollständigem Paging aktualisiert.');
  const [registry,sources]=await Promise.all([request(API+'/kanaele?stand_id='+site,{signal:controller.signal}),request(API+'/quellen?stand_id='+site,{signal:controller.signal})]);
  if(token!==generation||!root)return;
  renderRegistry(registry,rebuild);
  const mode=sources.length&&sources.every(s=>s.synthetic)?'SYNTHETISCHE TESTDATEN · keine aktuellen Feldmessungen':sources.some(s=>s.synthetic)?'Gemischte Quellen · Testdaten sind je Punkt gekennzeichnet':'Freigegebene Messquellen';
  root.querySelector('#umMode').textContent=mode;document.querySelector('#modeMark').textContent=mode;
  const sourceStatus=root.querySelector('#umSources');sourceStatus.replaceChildren();
  for(const source of sources){
   const stale=source.last_value&&source.interval_seconds&&Date.now()-Date.parse(source.last_value)>source.interval_seconds*2500;
   sourceStatus.append(make('p',source.key+' · '+(source.last_value?'Letzter Quellzeitpunkt: '+timeLabel(source.last_value):'Noch kein gültiger Messwert')+(stale?' · QUELLE VERALTET':'')+' · Importprüfung: '+(source.last_checked?timeLabel(source.last_checked):'nie')+' · '+(source.success===true?'erfolgreich':source.success===false?'IMPORTFEHLER':'noch nicht importiert'),'small'));
   if(source.report?.fehler?.length)sourceStatus.append(make('p','Importhinweise: '+JSON.stringify(source.report.fehler),'note warning'));
  }
  if(selected.size>30)throw Error('Höchstens 30 Messkanäle auswählen.');
  if(!selected.size){clearCharts();latestSeries=[];root.querySelector('#umPlots').replaceChildren(make('p','Keine ausgewählten Messkanäle.','empty'));notice(registry.length?'Messkanäle auswählen (höchstens 30).':'Für diesen Stand sind keine Kanäle registriert.');return;}
  const [from,to]=windowParams();
  const params=new URLSearchParams({stand_id:site,von:from,bis:to,limit:'5000',resolution:'auto'});
  for(const id of [...selected].sort((a,b)=>a-b))params.append('kanal_id',id);
  const result=await completeSeries(params,controller.signal);
  if(token!==generation||!root)return;
  await loadEcharts();if(token!==generation||!root)return;
  latestSeries=result.series;renderPlots(latestSeries);
  const aggregated=result.series.some(s=>s.summary.method!=='raw');
  const first=result.series.map(s=>s.summary.first_time).filter(Boolean).sort()[0];
  const last=result.series.map(s=>s.summary.last_time).filter(Boolean).sort().at(-1);
  notice('Vollständig geladen · '+(aggregated?'fachlich verdichtet':'Rohwerte')+' · '+result.source_points+' Quellwerte → '+result.total_points+' Originalpunkte · '+result.pages+' Seiten · Quellenzeitraum: '+(first?timeLabel(first)+' – '+timeLabel(last):'leer')+' · Snapshot: '+timeLabel(result.as_of)+' · letzte erfolgreiche Abfrage: '+timeLabel(new Date()));
 }catch(exc){if(token!==generation||!root||exc.name==='AbortError')return;if(exc.status===401){loginForm(exc.message);}else{clearCharts();root.querySelector('#umPlots')?.replaceChildren(make('p','Keine Datenanzeige nach fehlgeschlagener Abfrage.','empty'));notice(exc.message);}}
 finally{if(token===generation){loading=false;activeRequest=null;}}
}
async function initialize(token){
 sites=await request(API+'/staende');if(token!==generation||!root)return;
 if(!sites.length){root.replaceChildren(make('p','Keine Stände freigegeben. Ein Administrator muss ein ausdrückliches Standrecht einrichten.','empty'));const logout=make('button','Abmelden','btn');logout.addEventListener('click',async()=>{await request(AUTH+'/logout',{method:'POST',csrf:session.csrf_token});loginForm('Abgemeldet.');});root.append(logout);return;}
 if(!sites.some(s=>s.id===site))site=sites[0].id;
 selected=null;buildControls();clearInterval(timer);timer=setInterval(()=>refresh(generation),POLL_MS);await refresh(token,true);
}
async function mount(node){
 unmount();root=node;const token=generation;
 if(location.protocol==='file:'){root.append(make('p','Umwelt-Zeitreihen benötigen den eingerichteten HTTPS-Testserver. Die Offline-Datei enthält keine Servermessdaten.','empty'));return;}
 root.append(make('p','Sitzung wird geprüft …','small'));
 try{session=await request(AUTH);if(token===generation)await initialize(token);}catch(exc){if(token===generation)loginForm(exc.message);}
}
window.addEventListener('resize',()=>charts.forEach(chart=>chart.resize()));
window.BienenUmwelt={mount,unmount};
})();
