/* SPDX-License-Identifier: GPL-3.0-or-later
 * Eigenständige Bienenlogger-Stockkarte: serverseitige Durchsichten erfassen
 * und korrigieren. Session/CSRF nur im Arbeitsspeicher des Tabs.
 */
(() => {
'use strict';
const api='/api/v1/stockkarte';
let current=null;
const $=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=String(text);if(cls)e.className=cls;return e};
const add=(parent,tag,text,cls)=>{const el=$(tag,text,cls);parent.append(el);return el};
function inputField(parent,name,type,value,opts={}){
 const wrap=add(parent,'div',undefined,'form-field');const label=add(wrap,'label',name);
 const control=type==='textarea'?$('textarea'): $('input');
 if(type!=='textarea')control.type=type;
 control.value=value==null?'':String(value);
 if(opts.required)control.required=true;
 if(opts.maxLength)control.maxLength=opts.maxLength;
 if(opts.min!==undefined)control.min=String(opts.min);
 if(opts.max!==undefined)control.max=String(opts.max);
 if(opts.step!==undefined)control.step=opts.step;
 if(type==='textarea')control.rows=3;
 label.append(control);return control;
}
function renderCategory(parent,field,existing,options){
 const wrap=add(parent,'div',undefined,'form-field');
 const label=add(wrap,'label',field.name+(field.required?' *':''));
 const type=field.input;
 let control;
 if(['boolean','boolean_yes_red','list_item','select','options','bee_subspecies'].includes(type)){
  control=$('select');const placeholder=$('option','Nicht erfasst');placeholder.value='';control.append(placeholder);
  const opts=['boolean','boolean_yes_red','list_item'].includes(type)
   ? [{id:'true',name:'Ja'},{id:'false',name:'Nein'}]
   : options.filter(x=>x.category_id===field.id&&!x.inactive);
  for(const opt of opts){const element=$('option',opt.name);element.value=opt.id;control.append(element);}
  control.value=existing===true?'true':existing===false?'false':existing==null?'':String(existing);
 }else if(type==='list'){
  control=$('div');control.className='live-checkboxes';
  for(const opt of options.filter(x=>x.category_id===field.id&&!x.inactive)){
   const line=$('label',undefined,'checkline'),cb=$('input');cb.type='checkbox';cb.value=opt.id;
   if(Array.isArray(existing)&&existing.includes(opt.id))cb.checked=true;
   line.append(cb,$('span',opt.name));control.append(line);
  }
 }else if(type==='text'||type==='string'){
  control=$('textarea');control.rows=3;control.maxLength=type==='text'?4000:600;
  control.value=existing??'';
 }else if(type==='date'){
  control=$('input');control.type='date';control.value=existing??'';
 }else if(type==='number'||type==='number_positive'||type==='number_negative'||
    type==='number_percentage'||/^number_[0-3]_decimals$/.test(type)||
    ['score','grade','score_amount','score_quality','smileys_3','slider'].includes(type)){
  control=$('input');control.type='number';control.step=/number_0_decimals|score|grade|smileys_3/.test(type)?'1':'any';
  if(field.meta?.min!=null)control.min=String(field.meta.min);
  if(field.meta?.max!=null)control.max=String(field.meta.max);
  if(existing!=null)control.value=String(existing);
 }else{
  add(wrap,'p','Nicht unterstützter Feldtyp '+type+' – Korrektur gesperrt.','small muted');
  return {unsupported:true,wrapper:wrap};
 }
 control.dataset.category=field.id;control.dataset.kind=type;
 label.append(control);return {control,wrapper:wrap,unsupported:false};
}
function valuesOf(root){
 const data={};
 for(const node of root.querySelectorAll('[data-category]')){
  const id=node.dataset.category,type=node.dataset.kind;
  let value=null;
  if(type==='list')value=Array.from(node.querySelectorAll('input:checked')).map(x=>x.value);
  else if(['boolean','boolean_yes_red','list_item'].includes(type))value=node.value==='true'?true:node.value==='false'?false:null;
  else if(node.type==='number')value=node.value===''?null:Number(node.value);
  else value=node.value||null;
  if(value!==null&&(!Array.isArray(value)||value.length))data[id]=value;
 }
 return data;
}
async function openEditor({id,canWrite,entry,fetcher,csrfToken,onSaved,onCancel}){
 if(!canWrite)return;
 const root=document.getElementById('liveBody');if(!root)return;
 const status=document.getElementById('liveError');
 const notice=txt=>{if(status)status.textContent=txt;};
 try{
  const catalog=await fetcher(api+'/katalog');
  if(!document.getElementById('liveBody'))return;
  root.replaceChildren();add(root,'h3',entry?'Durchsicht korrigieren':'Neue Durchsicht erfassen');
  add(root,'p','Server-Volk '+id+' · jede Korrektur schreibt eine neue Revision.','small muted');
  const form=$('form');form.id='serverEntryForm';form.className='form-grid';
  const date=inputField(form,'Datum der Durchsicht','date',entry?.event_date||new Date().toLocaleDateString('en-CA',{timeZone:'Europe/Berlin'}),{required:true});
  const wrap=add(form,'div',undefined,'form-field'),tplLabel=add(wrap,'label','Checkliste');
  const tpl=$('select');tpl.id='serverChecklist';tplLabel.append(tpl);
  const empty=$('option','Ohne Checkliste');empty.value='';tpl.append(empty);
  for(const item of catalog.checklists||[]){const option=$('option',item.name+' · v'+item.version);option.value=item.id+':'+item.version;tpl.append(option);}
  if(entry?.checklist_id)tpl.value=entry.checklist_id+':'+entry.checklist_version;
  else if(tpl.options.length>1)tpl.selectedIndex=tpl.options.length-1;
  if(entry?.checklist_id&&!tpl.value)throw Error('Historische Checklisten-Version fehlt.');
  const fields=add(form,'div',undefined,'form-grid');fields.id='serverEntryFields';
  const note=inputField(form,'Notiz','textarea',entry?.note||'',{maxLength:10000});
  const reason=inputField(form,'Grund der Erfassung/Korrektur','text',entry?'Korrektur':'Durchsicht erfasst',{required:true,maxLength:1000});
  const bar=add(form,'div',undefined,'toolbar');
  const save=$('button',entry?'Als neue Revision speichern':'Auf Server speichern','btn primary');save.type='submit';
  const cancel=$('button','Abbrechen','btn');cancel.type='button';cancel.addEventListener('click',onCancel);
  bar.append(save,cancel);root.append(form);
  function buildFields(){
   fields.replaceChildren();let blocked=false;
   const selected=(catalog.checklists||[]).find(x=>x.id+':'+x.version===tpl.value);
   const ids=selected?selected.fields.slice().sort((a,b)=>a.position-b.position).map(x=>x.category_id):
    (catalog.categories||[]).filter(x=>x.input!=='label').map(x=>x.id);
   const byId=new Map((catalog.categories||[]).map(x=>[x.id,x]));
   for(const fieldId of ids){
    const definition=byId.get(fieldId);if(!definition)continue;
    const item=renderCategory(fields,definition,entry?.values?.[fieldId],catalog.options||[]);
    blocked=blocked||item.unsupported;
   }
   if(entry&&Object.keys(entry.values||{}).some(x=>!ids.includes(x))){
    add(fields,'p','Die bisherige Durchsicht enthält zusätzliche Felder. Eine verlustfreie Korrektur ist hier noch nicht möglich.','small muted');
    blocked=true;
   }
   save.disabled=blocked;
  }
  tpl.addEventListener('change',buildFields);buildFields();
  form.addEventListener('submit',async e=>{
   e.preventDefault();if(save.disabled)return;save.disabled=true;notice('Speichere …');
   const [clId,clVersion]=tpl.value?tpl.value.split(':').map(Number):[null,null];
   const payload={event_date:date.value,accuracy:'nur_datum',
    checklist_id:clId,checklist_version:clVersion,values:valuesOf(fields),
    note:note.value,reason:reason.value.trim()};
   if(entry)payload.expected_revision=entry.revision;
   try{
    const endpoint=entry?api+'/durchsichten/'+entry.id+'/revisionen':api+'/voelker/'+id+'/durchsichten';
    const result=await fetcher(endpoint,{method:'POST',body:payload,csrfToken});
    notice('Gespeichert: Durchsicht '+result.id+', Revision '+result.revision);
    await onSaved();
   }catch(err){notice(err.message);save.disabled=false;}
  });
 }catch(err){notice(err.message);if(onCancel)await onCancel();}
}
window.BienenloggerStockkarteEditor={openEditor};
})();
