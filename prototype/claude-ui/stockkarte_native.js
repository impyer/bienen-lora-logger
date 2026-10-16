/* SPDX-License-Identifier: GPL-3.0-or-later
 * Bienenlogger native stockcard taxonomy/checklist engine.
 * Own implementation of publicly documented BEEP category-id based behavior;
 * does NOT load BEEP UI code, use BEEP APIs, or call external servers.
 * Source concepts: beepnl/BEEP CategoryInput, Checklist, InspectionsController;
 * beepnl/beep-vue-app checklist-fieldset, checklist-input, inspect.
 */
(function(root, factory) {
  const result=factory();
  if (typeof module==='object' && module.exports) module.exports=result;
  root.BienenStockkarte=result;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const escape=s=>String(s??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
const multi=new Set(['list']);
const choices=new Set(['select','options','list','list_item','bee_subspecies']);
const decimal=new Set(['number','number_0_decimals','number_1_decimals','number_2_decimals','number_3_decimals','number_positive','number_negative','number_percentage','number_degrees','slider']);
const scores=new Set(['score','score_amount','score_quality','grade','smileys_3']);
const yesNo=new Set(['boolean','boolean_yes_red']);
function title(o){
  const t=o?.trans;
  if(t&&typeof t==='object')return String(t.de||t.de_DE||t.en||o.name||o.text||'Unbenannt');
  return String(o?.text||o?.name||'Unbenannt');
}
function prepare(payload){
  let roots=Array.isArray(payload)?payload:payload?.taxonomy||payload?.categories||[];
  if(!Array.isArray(roots))throw Error('Katalog muss ein Array von Kategorien enthalten');
  if(roots.length>5000)throw Error('Zu viele Kategorien (max. 5000)');
  const nodes=[], ids=new Set();
  function walk(item,parent,depth){
    if(!item||typeof item!=='object'||depth>16)throw Error('Ungültige/zu tiefe Kategorie');
    const id=String(item.id??item.category_id??'');
    if(!id||!(/^[a-zA-Z0-9_.:-]{1,100}$/).test(id)||ids.has(id))throw Error('Doppelte oder ungültige Kategorie-ID: '+id);
    ids.add(id);
    const kids=Array.isArray(item.children)?item.children:[];
    let input=String(item.input||item.input_type||item.inputType||item.category_input?.type||'');
    // In BEEP 'type' is taxonomy provenance ('system' etc.) and not the input widget.
    if(!input)input=kids.length?'label':'text';
    const node={id,label:title(item).slice(0,250),parent,depth,input,required:Boolean(item.required),
      min:Number.isFinite(Number(item.min))&&item.min!==null?Number(item.min):null,
      max:Number.isFinite(Number(item.max))&&item.max!==null?Number(item.max):null,
      decimals:Number.isInteger(Number(item.decimals))?Number(item.decimals):null,
      unit:item.unit?String(item.unit).slice(0,25):'',
      children:kids.map(k=>String(k?.id??k?.category_id??'')),
      sourceId:item.source_id??null,description:String(item.description||'').slice(0,800)};
    nodes.push(node);
    for(const child of kids)walk(child,id,depth+1);
  }
  for(const item of roots)walk(item,null,0);
  return nodes;
}
function fallback(labels){
  const nodes=[],grps=new Map();
  for(const label of labels){
    const parts=String(label).split(' > ').map(s=>s.trim()).filter(Boolean);
    if(!parts.length)continue;
    let parent=null,path='';
    for(let i=0;i<parts.length;i++){
      path+=(path?' > ':'')+parts[i];
      let id='export:'+path;
      if(!grps.has(id)){
        let input=i<parts.length-1?'label':'text';
        const n={id,label:parts[i],parent,depth:i,input,required:false,min:null,max:null,decimals:null,unit:'',children:[],sourceId:null,description:'Nur Kategoriepfad im BEEP-Export belegt. Typ und Optionen nicht bekannt.'};
        nodes.push(n);grps.set(id,n);
        if(parent)grps.get(parent).children.push(id);
      }
      parent=id;
    }
  }
  return nodes;
}
function paths(nodes){
  const by=new Map(nodes.map(n=>[n.id,n]));
  return new Map(nodes.map(n=>{let names=[],curr=n,limit=0;while(curr&&limit++<18){names.unshift(curr.label);curr=by.get(curr.parent);}return [n.id,names.join(' > ')];}));
}
function template(name,categoryIds,id){return {id:id||('local-'+Date.now().toString(36)),name:String(name||'Meine Checkliste').slice(0,100),category_ids:[...new Set(categoryIds.map(String))],source:'Lokaler Entwurf',updatedAt:new Date().toISOString()};}
function checklistNormalize(payload,nodes){
  let lists=Array.isArray(payload)?payload:payload?.checklists||[];
  if(!Array.isArray(lists))throw Error('Checklisten müssen ein Array sein');
  const allowed=new Set(nodes.map(n=>n.id));
  return lists.slice(0,200).map((c,i)=>{
    const ids=c.category_ids||c.categoryIds||c.categories?.map(x=>typeof x==='object'?x.id:x)||[];
    const selected=[...new Set((Array.isArray(ids)?ids:[]).map(String))].filter(id=>allowed.has(id));
    return {id:String(c.id||('import-'+i)),name:String(c.name||('Checkliste '+(i+1))).slice(0,100),category_ids:selected,source:'Katalog-Import (lokal)',updatedAt:c.updated_at||null};
  });
}
function selectedLeaves(nodes,ids){
  const selected=new Set(ids.map(String)),by=new Map(nodes.map(x=>[x.id,x]));
  const out=[],seen=new Set();
  function visit(id){
    if(seen.has(id))return;seen.add(id);
    const n=by.get(id);if(!n)return;
    if(choices.has(n.input)||(!n.children.length&&n.input!=='label'))out.push(n);
    else n.children.forEach(visit);
  }
  ids.forEach(visit);
  return out;
}

function validateValues(nodes, ids, raw) {
  const fields=selectedLeaves(nodes,ids), by=new Map(nodes.map(n=>[n.id,n]));
  const values={},errors=[];
  const src=raw&&typeof raw==='object'&&!Array.isArray(raw)?raw:{};
  for(const n of fields) {
    const present=Object.prototype.hasOwnProperty.call(src,n.id);
    const v=src[n.id];
    const missing=!present||v==null||v===''||(Array.isArray(v)&&v.length===0);
    if(n.input==='image'||n.input==='file') {
      if(n.required||!missing)errors.push(n.label+': Dateianhang hier nicht unterstützt');
      continue;
    }
    if(missing) {if(n.required)errors.push(n.label+': Pflichtfeld');continue;}
    if(yesNo.has(n.input)) {
      if(v===true||v===1||v==='1'||v==='true')values[n.id]=true;
      else if(v===false||v===0||v==='0'||v==='false')values[n.id]=false;
      else errors.push(n.label+': ungültiger Ja/Nein-Wert');
    } else if(choices.has(n.input)) {
      const allowed=new Set(n.children.filter(id=>by.has(id)).map(String));
      if(!allowed.size)errors.push(n.label+': Optionen fehlen');
      else if(multi.has(n.input)) {
        if(!Array.isArray(v)||v.some(x=>!allowed.has(String(x))))errors.push(n.label+': ungültige Mehrfachauswahl');
        else values[n.id]=[...new Set(v.map(String))];
      } else if(!allowed.has(String(v)))errors.push(n.label+': ungültige Auswahl');
      else values[n.id]=String(v);
    } else if(decimal.has(n.input)||scores.has(n.input)) {
      const str=String(v).trim();
      const num=/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/.test(str)?Number(str):NaN;
      const min=n.min!==null?n.min:(n.input==='number_positive'||n.input==='number_percentage'?0:n.input==='smileys_3'?1:null);
      const max=n.max!==null?n.max:(n.input==='number_percentage'?100:n.input==='smileys_3'?3:null);
      const digits=n.decimals!==null?n.decimals:(/^number_([0-3])_decimals$/.test(n.input)?Number(n.input.match(/^number_([0-3])_decimals$/)[1]):null);
      const goodDigits=digits===null||(digits>=0&&digits<=8&&Math.abs(num*10**digits-Math.round(num*10**digits))<1e-7);
      if(!Number.isFinite(num)||(min!==null&&num<min)||(max!==null&&num>max)||(scores.has(n.input)&&!Number.isInteger(num))||!goodDigits)
        errors.push(n.label+': ungültiger Zahlenwert');
      else values[n.id]=num;
    } else if(n.input==='date') {
      const s=String(v),d=/^\d{4}-\d{2}-\d{2}$/.test(s)?new Date(s+'T00:00:00Z'):null;
      if(!d||Number.isNaN(d.getTime())||d.toISOString().slice(0,10)!==s)errors.push(n.label+': ungültiges Kalenderdatum');
      else values[n.id]=s;
    } else if(n.input==='color_picker') {
      if(!/^#[a-f\d]{6}$/i.test(String(v)))errors.push(n.label+': ungültiger Farbwert');
      else values[n.id]=String(v);
    } else {
      const s=String(v).trim();
      if(s.length>(n.input==='text'?4000:600))errors.push(n.label+': Text zu lang');
      else values[n.id]=s;
    }
  }
  return {values,errors};
}
function widget(node,nodes,priorValue){
  const nm='tax_'+node.id,att='data-native-category="'+escape(node.id)+'"',required=node.required?' required':'';
  const val=priorValue===null||priorValue===undefined?'':String(priorValue);
  const pick=(value)=>val===String(value)?' selected':'';
  let html='';
  if(yesNo.has(node.input)){
    const yn=priorValue===true||priorValue==='true'? '1':priorValue===false||priorValue==='false'?'0':val;
    html=`<select name="${escape(nm)}" ${att}${required}><option value="">Nicht erfasst</option><option value="1"${yn==='1'?' selected':''}>Ja</option><option value="0"${yn==='0'?' selected':''}>Nein</option></select>`;
  } else if(choices.has(node.input)){
    const by=new Map(nodes.map(x=>[x.id,x]));const opts=node.children.map(id=>by.get(id)).filter(Boolean);
    if(node.input==='list'){
      let vals=new Set(Array.isArray(priorValue)?priorValue.map(String):val?val.split(',').map(x=>x.trim()):[]);
      html=opts.map(o=>`<label class="checkline"><input type="checkbox" ${att} name="${escape(nm)}" value="${escape(o.id)}" ${vals.has(o.id)?'checked':''}> ${escape(o.label)}</label>`).join('');
    }else{
      html=`<select name="${escape(nm)}" ${att}${required}><option value="">Nicht erfasst</option>${opts.map(o=>`<option value="${escape(o.id)}"${pick(o.id)}>${escape(o.label)}</option>`).join('')}</select>`;
    }
    if(!opts.length)html='<p class="small muted">Optionen fehlen im Katalog; Eingabe erst nach Kategorienimport möglich.</p>';
  } else if(decimal.has(node.input)||scores.has(node.input)){
    let min=node.min,max=node.max,step=node.input==='number_0_decimals'?'1':node.decimals!==null?(1/Math.pow(10,Math.max(0,Math.min(node.decimals,4)))).toString():'any';
    if(node.input==='number_positive')min=Math.max(0,min??0);
    if(node.input==='number_percentage'){min=min??0;max=max??100;}
    if(scores.has(node.input)){min=min??(node.input==='smileys_3'?1:0);max=max??(node.input==='smileys_3'?3:5);step='1';}
    html=`<input type="number" name="${escape(nm)}" ${att} value="${escape(val)}" step="${escape(step)}" ${min!==null?'min="'+min+'"':''} ${max!==null?'max="'+max+'"':''}${required}>`;
  } else if(node.input==='date'){
    html=`<input type="date" name="${escape(nm)}" ${att} value="${escape(val.slice(0,10))}"${required}>`;
  } else if(node.input==='color_picker'){
    html=`<input type="text" pattern="#[a-fA-F0-9]{6}" name="${escape(nm)}" ${att} value="${escape(val)}" placeholder="#FFFFFF"${required}>`;
  } else if(node.input==='text'){
    html=`<textarea name="${escape(nm)}" ${att} maxlength="4000"${required}>${escape(val)}</textarea>`;
  } else if(node.input==='image'||node.input==='file'){
    html='<p class="small muted">Bild-/Dateiupload benötigt eine geschützte eigene Datenablage. Hier keine Fake-Speicherung.</p>';
  } else if(node.input==='label'){
    return '';
  } else {
    html=`<input type="text" name="${escape(nm)}" ${att} value="${escape(val)}" maxlength="600"${required}>`;
  }
  return `<div class="form-field"><label>${escape(node.label)}${node.required?' *':''}${node.unit?' · '+escape(node.unit):''}</label>${html}${node.description?'<small>'+escape(node.description)+'</small>':''}</div>`;
}
function renderFields(nodes,selectedIds,prior={}){
  const by=new Map(nodes.map(n=>[n.id,n]));const path=paths(nodes);const leaves=selectedLeaves(nodes,selectedIds);
  let lastRoot='',html='';
  for(const node of leaves){
    const pathText=path.get(node.id)||node.label;const root=pathText.split(' > ')[0];
    if(root!==lastRoot){if(lastRoot)html+='</div></details>';html+=`<details class="taxonomy-group" open><summary>${escape(root)}</summary><div class="form-grid">`;lastRoot=root;}
    const decorated={...node,label:pathText.split(' > ').slice(1).join(' › ')||node.label};
    html+=widget(decorated,nodes,prior[node.id]);
  }
  if(lastRoot)html+='</div></details>';
  return html||'<p class="small muted">Keine Kategorien in dieser Checkliste. Checkliste bearbeiten.</p>';
}
function collect(form,nodes,selectedIds){
  const fields=selectedLeaves(nodes,selectedIds),raw={};
  for(const n of fields){
    const inputs=Array.from(form.querySelectorAll('[data-native-category]')).filter(x=>x.dataset.nativeCategory===n.id);
    if(!inputs.length)continue;
    raw[n.id]=multi.has(n.input)?inputs.filter(x=>x.checked).map(x=>x.value):inputs[0].value.trim();
  }
  return validateValues(nodes,selectedIds,raw);
}

return {prepare,fallback,paths,template,checklistNormalize,selectedLeaves,renderFields,validateValues,collect,escape};
});
