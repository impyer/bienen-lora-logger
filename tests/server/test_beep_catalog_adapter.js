// SPDX-License-Identifier: GPL-3.0-or-later
'use strict';
const assert=require('node:assert/strict'),s=require('../../prototype/claude-ui/stockkarte_native.js');
let n=0;function eq(a,b){assert.deepEqual(a,b);n++}
const exportData={categories:[
{id:1,parent:'#',name:'Bienenvolk',input:'label'},
{id:2,parent:1,name:'Königin?',category_input_id:10,required:1},
{id:3,parent:1,name:'Auffälligkeit',input:'list_item'},
{id:4,parent:1,name:'Behandlung',input:'select'},
{id:5,parent:4,name:'Oxalsäure',input:'label'},
{id:6,parent:4,name:'VarroMed',input:'label'},
{id:7,parent:1,name:'Foto',input:'image'},
{id:8,parent:1,name:'Beutenauswahl',input:'select_hive',required:0},
{id:9,parent:1,name:'Anzahl',input:'number_0_decimals',required:'0'}
],categoryinputs:[{id:10,type:'boolean',name:'Ja/Nein'}],
checklists:[{id:24,name:'Standard',category_ids:[2,3,4,8,9]}]};
const normalized=s.normalizeCatalog(exportData);
eq(normalized.taxonomy.length,1);eq(exportData.categories[0].children,undefined);
const categories=s.prepare(exportData);
eq(categories.length,9);
eq(categories.find(x=>x.id==='2').input,'boolean');
eq(categories.find(x=>x.id==='9').required,false);
eq(categories.find(x=>x.id==='3').input,'list_item');
eq(s.checklistNormalize(exportData,categories)[0].category_ids,['2','3','4','8','9']);
eq(s.catalogReport(categories).blocked.map(x=>x.id),['7','8']);
const valid=s.validateValues(categories,['2','3','4'],{'2':'0','3':'1','4':'6'});
eq(valid.errors,[]);eq(valid.values,{'2':false,'3':true,'4':'6'});
eq(s.renderFields(categories,['3']).includes('>Ja</option>'),true);
eq(s.validateValues(categories,['8'],{}).errors.some(x=>x.includes('Feldtyp')),true);
for(const bad of [
{categories:[{id:1,parent:2},{id:2,parent:1}]},
{categories:[{id:1,parent:99}]},
{categories:[{id:1,parent:'#',category_input_id:777}]},
{categories:[{id:1,parent:'#'},{id:1,parent:'#'}]}
]){assert.throws(()=>s.normalizeCatalog(bad));n++;}
console.log('BEEP-Katalogadapter:',n,'Tests PASS');
