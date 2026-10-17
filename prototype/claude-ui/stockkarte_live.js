/* SPDX-License-Identifier: GPL-3.0-or-later
 * Lesende Stockkartenansicht am SELBEN Origin wie der lokale Sitzungsdienst.
 * Keine API-Schlüssel, keine Speicherung von Passwörtern oder CSRF-Werten.
 * Die übrige Bienenlogger-App läuft unverändert offline weiter.
 */
(() => {
'use strict';
const base='/api/v1/stockkarte';
const root=document.getElementById('modalRoot');
let csrf=null;
let currentColony=null;
let colonyPermissions=new Map();
let entries=[];
const make=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=String(text);if(cls)e.className=cls;return e};
const add=(target,tag,text,cls)=>{const e=make(tag,text,cls);target.append(e);return e};
function alertText(text){let p=document.getElementById('liveError');if(!p)return;p.textContent=text||'';}
async function request(url,{method='GET',body,csrfToken}={}){
 const headers={'Accept':'application/json'};
 if(body!==undefined)headers['Content-Type']='application/json';
 if(csrfToken)headers['X-CSRF-Token']=csrfToken;
 const response=await fetch(url,{method,body:body===undefined?undefined:JSON.stringify(body),
   credentials:'same-origin',cache:'no-store',headers,redirect:'error'});
 let data={};try{data=await response.json();}catch{}
 if(!response.ok)throw Error(response.status===401?'Sitzung fehlt oder abgelaufen':
   response.status===503?'Sitzungsdienst noch nicht freigeschaltet':
   response.status===403?'Keine Berechtigung':
   'Serverfehler ('+response.status+')');
 return data;
}
function open(){
 if(window.location.protocol==='file:'){
  root.replaceChildren();
  const p=make('div',undefined,'modal-backdrop'),panel=make('section',undefined,'modal');
  panel.append(make('h2','Serveransicht – nur am eigenen Testserver'));
  panel.append(make('p','Die lokale HTML-Datei ist weiterhin ein Offline-Prototyp. Serverdaten sind nur beim ausdrücklich aktivierten lokalen Entwicklungsdienst verfügbar.'));
  const close=make('button','Schließen','btn');close.type='button';close.addEventListener('click',()=>root.replaceChildren());panel.append(close);p.append(panel);root.append(p);return;
 }
 root.innerHTML='<div class="modal-backdrop"><section class="modal wide" role="dialog" aria-modal="true" aria-labelledby="liveHeading"><div class="panel-head"><div><div class="eyebrow">DATENBANK · EIGENER BIENENLOGGER</div><h2 id="liveHeading">Stockkarte – Heimnetz-Test</h2></div><button type="button" class="btn" data-action="close-modal">✕</button></div><p class="small muted">Eigenständiger Bienenlogger-Code. Server-Völker sind unabhängig von den lokalen Demo-Volknummern. Hier sind neue Durchsichten und Korrekturen nur mit Schreibberechtigung möglich. Die lokalen Testentwürfe bleiben getrennt.</p><p class="small" id="liveError" role="status"></p><div id="liveBody"></div></section></div>';
 const body=document.getElementById('liveBody');
 add(body,'p','Anmeldung wird geprüft …','small muted');
 loadSession();
}
function showLogin(){
 const body=document.getElementById('liveBody');if(!body)return;
 body.replaceChildren();
 add(body,'p','Nur für einen lokal freigeschalteten Entwicklungsserver.','small muted');
 const form=make('form');form.id='serverLoginForm';form.className='form-grid';
 const u=make('div',undefined,'form-field'),pw=make('div',undefined,'form-field');
 const label=add(u,'label','Benutzername');const input=make('input');input.name='username';input.required=true;input.autocomplete='username';label.append(input);
 const pwLabel=add(pw,'label','Passwort');const password=make('input');password.name='password';password.type='password';password.required=true;password.autocomplete='current-password';pwLabel.append(password);
 form.append(u,pw);
 const submit=make('button','Lokal anmelden','btn primary');submit.type='submit';form.append(submit);
 form.addEventListener('submit',async e=>{
  e.preventDefault();submit.disabled=true;alertText('');
  const username=input.value.trim(),secret=password.value;password.value='';
  try{
   const s=await request(base+'/session/login',{method:'POST',body:{username,password:secret}});
   csrf=s.csrf_token;await loadColonies();
  }catch(err){alertText(err.message);}finally{submit.disabled=false;}
 });
 body.append(form);
}
async function loadSession(){
 try{
  const s=await request(base+'/session');
  csrf=s.csrf_token;await loadColonies();
 }catch(err){alertText(err.message);showLogin();}
}
async function loadColonies(){
 const body=document.getElementById('liveBody');if(!body)return;
 const colonies=await request(base+'/voelker');body.replaceChildren();
 colonyPermissions=new Map(colonies.map(c=>[Number(c.id),!!c.can_write]));
 const bar=make('div',undefined,'toolbar');
 add(bar,'strong','Daten aus eigener PostgreSQL-Stockkarte');
 const logout=make('button','Abmelden','btn');logout.type='button';logout.addEventListener('click',async()=>{
  try{await request(base+'/session/logout',{method:'POST',csrfToken:csrf});csrf=null;currentColony=null;alertText('Abgemeldet.');showLogin();}
  catch(err){alertText(err.message);}
 });
 bar.append(logout);body.append(bar);
 const wrap=make('div',undefined,'form-field'),label=add(wrap,'label','Server-Volk');
 const select=make('select');select.id='serverColonySelect';label.append(select);body.append(wrap);
 const content=make('section');content.id='serverInspections';body.append(content);
 if(!Array.isArray(colonies)||!colonies.length){add(content,'p','Keine freigegebenen Völker vorhanden.','small muted');return;}
 for(const c of colonies){
  if(!Number.isInteger(c.id)||c.id<=0)continue;
  const opt=make('option',c.name+' · interne ID '+c.id);opt.value=String(c.id);select.append(opt);
 }
 select.addEventListener('change',()=>loadEntries(Number(select.value)));
 if(select.options.length){if(currentColony!==null&&colonyPermissions.has(currentColony))select.value=String(currentColony);await loadEntries(Number(select.value));}
}
async function loadEntries(id){
 const panel=document.getElementById('serverInspections');if(!panel)return;
 if(!Number.isInteger(id)||id<=0)return;
 currentColony=id;panel.replaceChildren();add(panel,'p','Durchsichten werden geladen …','small muted');
 try{
  const list=await request(base+'/voelker/'+id+'/durchsichten?limit=100');
  if(currentColony!==id||!document.getElementById('serverInspections'))return;
  panel.replaceChildren();
  entries=Array.isArray(list)?list:[];
  add(panel,'h3','Durchsichten · '+entries.length+' Datensätze');
  if(colonyPermissions.get(id)){
   const newButton=make('button','+ Durchsicht erfassen','btn primary');
   newButton.type='button';
   newButton.addEventListener('click',()=>window.BienenloggerStockkarteEditor.openEditor({
    id,canWrite:true,entry:null,fetcher:request,csrfToken:csrf,
    onSaved:()=>loadColonies(),onCancel:()=>loadColonies()
   }));
   panel.append(newButton);
  }
  if(!Array.isArray(list)||!list.length){add(panel,'p','Keine gespeicherten Durchsichten.','small muted');return;}
  for(const row of list){
   const section=make('div',undefined,'row-small');
   const text=make('span',String(row.event_date||'Datum unbekannt')+' · '+String(row.note||'Ohne Notiz')+' · Revision '+String(row.revision||'?'));
   section.append(text);
   if(colonyPermissions.get(id)){
    const correct=make('button','Korrigieren','btn small');correct.type='button';
    correct.addEventListener('click',()=>window.BienenloggerStockkarteEditor.openEditor({
     id,canWrite:true,entry:row,fetcher:request,csrfToken:csrf,
     onSaved:()=>loadColonies(),onCancel:()=>loadColonies()
    }));
    section.append(correct);
   }
   const button=make('button','Revisionen','btn small');button.type='button';button.addEventListener('click',()=>loadRevisions(row.id,section));section.append(button);panel.append(section);
  }
 }catch(err){panel.replaceChildren();add(panel,'p',err.message,'small muted');}
}
async function loadRevisions(id, section){
 try{
  const records=await request(base+'/durchsichten/'+encodeURIComponent(id)+'/revisionen');
  const old=section.querySelector('.live-revisions');if(old)old.remove();
  const panel=make('div',undefined,'live-revisions');
  for(const r of records){
   const text='Revision '+r.revision+' · '+r.event_date+' · '+(r.accuracy||'')+' · '+(r.reason||'')+' · '+(r.author||'');
   add(panel,'p',text,'small');
  }
  section.append(panel);
 }catch(err){alertText(err.message);}
}
document.addEventListener('click',e=>{
 const button=e.target.closest('[data-action="server-preview"]');if(!button)return;
 e.preventDefault();open();
});
})();
