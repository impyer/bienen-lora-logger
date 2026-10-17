// SPDX-License-Identifier: GPL-3.0-or-later
'use strict';
const assert = require('node:assert/strict');
const n = require('../../prototype/claude-ui/stockkarte_native.js');
let checks=0;
const assertEq=(a,b)=>{assert.deepEqual(a,b);checks++};
const schema={taxonomy:[{id:100,name:'Stand',input:'label',children:[
 {id:101,name:'Königin',input:'boolean',required:true},
 {id:102,name:'Brut-Score',input:'smileys_3',min:1,max:3},
 {id:103,name:'Behandlung',input:'select',children:[{id:104,name:'VarroMed'},{id:105,name:'Oxalsäure'}]},
 {id:106,name:'Fütterung',input:'list',children:[{id:107,name:'Sirup'},{id:108,name:'Teig'}]},
 {id:109,name:'Notiz',input:'text'},
 {id:110,name:'Messung',input:'number_2_decimals',min:0,max:100}
]}]};
const nodes=n.prepare(schema);
assertEq(nodes.length,11);
assertEq(n.selectedLeaves(nodes,['100']).map(v=>v.id),['101','102','103','106','109','110']);
assertEq(n.checklistNormalize({checklists:[{id:44,name:'Meine Liste',category_ids:[101,103]}]},nodes)[0].category_ids,['101','103']);
assertEq(n.template('Unten zuerst',[110,101], 'ABC').category_ids,['110','101']);
assertEq(n.paths(nodes).get('105'),'Stand > Behandlung > Oxalsäure');
assertEq(n.renderFields(nodes,['100'],{'101':true}).includes('value="1" selected'),true);
assertEq(n.renderFields(nodes,['100'],{'101':false}).includes('value="0" selected'),true);
assertEq(n.renderFields(nodes,['103']).includes('<option value="105"'),true);
assertEq(n.renderFields(nodes,['106'],{'106':['107']}).includes('value="107" checked'),true);
assertEq(n.escape('<script>alert(1)</script>'),'&lt;script&gt;alert(1)&lt;/script&gt;');
const fallback=n.fallback(['Bienenvolk > Königin > Anwesenheit','Bienenvolk > Brut > Alter']);
assertEq(fallback.length,5);
assertEq(fallback.filter(x=>x.input==='text').length,2);
for(const bad of [[{id:'x'},{id:'x'}], [{id:'../../p'}]]){assert.throws(()=>n.prepare(bad));checks++;}
console.log('Bienenlogger native taxonomy engine:',checks,'Node tests PASS');
