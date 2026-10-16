// SPDX-License-Identifier: GPL-3.0-or-later
'use strict';
const a=require('node:assert/strict'),n=require('../../prototype/claude-ui/stockkarte_native.js');
const nodes=n.prepare([{id:1,name:'V',input:'label',children:[
 {id:2,name:'Königin',input:'boolean',required:true},
 {id:3,name:'Waben',input:'number_0_decimals',min:0,max:20,required:true},
 {id:4,name:'Methode',input:'select',children:[{id:5,name:'Puderzucker'}]},
 {id:6,name:'Fütterung',input:'list',children:[{id:7,name:'Sirup'}]},
 {id:8,name:'Datum',input:'date'},
 {id:9,name:'Menge',input:'number_2_decimals'},
 {id:10,name:'Foto',input:'file'}]}]);
let count=0;
function valid(raw,expect){const r=n.validateValues(nodes,['1'],raw);a.deepEqual(r.errors,[]);a.deepEqual(r.values,expect);count++;}
function invalid(raw,fragment){const r=n.validateValues(nodes,['1'],raw);a.ok(r.errors.some(x=>x.includes(fragment)),JSON.stringify(r));count++;}
valid({'2':'0','3':'0','4':'5','6':['7','7'],'8':'2024-02-29','9':'1.25'},{'2':false,'3':0,'4':'5','6':['7'],'8':'2024-02-29','9':1.25});
valid({'2':true,'3':2},{'2':true,'3':2});
invalid({'3':2},'Pflichtfeld');
invalid({'2':'not-a-bool','3':2},'Ja/Nein');
invalid({'2':'1','3':30},'Zahlenwert');
invalid({'2':false,'3':1.5},'Zahlenwert');
invalid({'2':false,'3':1,'9':1.234},'Zahlenwert');
invalid({'2':false,'3':1,'4':'999'},'Auswahl');
invalid({'2':false,'3':1,'6':['999']},'Mehrfachauswahl');
invalid({'2':false,'3':1,'8':'2026-02-29'},'Kalenderdatum');
invalid({'2':false,'3':1,'10':'test.jpg'},'Dateianhang');
invalid({'2':false,'3':'Infinity'},'Zahlenwert');
valid({'2':false,'3':1,'999':'<script>'},{'2':false,'3':1});
const fake={querySelectorAll:()=>[{dataset:{nativeCategory:'3'},value:'2'}]};
a.ok(n.collect(fake,nodes,['1']).errors.some(x=>x.includes('Königin')));count++;
console.log('Bienenlogger-Wertepruefung',count,'Tests PASS');
