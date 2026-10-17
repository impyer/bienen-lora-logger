// SPDX-License-Identifier: GPL-3.0-or-later
'use strict';
const assert=require('node:assert/strict');
const n=require('../../prototype/claude-ui/stockkarte_native.js');
let checks=0;function eq(a,b){assert.deepEqual(a,b);checks++;}
const imported=n.prepare([{id:101,name:'Bienenvolk',input:'label',children:[{id:102,name:'Brut',input:'number_0_decimals'}]}]);
let nodes=n.addGroup(imported,{id:'bl:grp1234',label:'  Eigene Gruppe '});
nodes=n.addField(nodes,{id:'bl:fld1234',parentId:'bl:grp1234',label:'Behandlung',input:'select'});
nodes=n.addOption(nodes,{id:'bl:opt1234',parentId:'bl:fld1234',label:'Oxalsäure'});
eq(imported.length,2);eq(nodes.length,5);
eq(nodes.find(x=>x.id==='bl:grp1234').label,'Eigene Gruppe');
eq(nodes.find(x=>x.id==='bl:fld1234').children,['bl:opt1234']);
eq(n.validateValues(nodes,['bl:fld1234'],{'bl:fld1234':'bl:opt1234'}).errors,[]);
eq(n.validateValues(nodes,['bl:fld1234'],{'bl:fld1234':'falsch'}).errors.length,1);
const newer=n.renameOwnNode(nodes,'bl:opt1234','Oxalsäure 3,5 %');
eq(nodes.find(x=>x.id==='bl:opt1234').label,'Oxalsäure');
eq(newer.find(x=>x.id==='bl:opt1234').label,'Oxalsäure 3,5 %');
eq(n.validateValues(newer,['bl:fld1234'],{'bl:fld1234':'bl:opt1234'}).errors,[]);
const exp=n.exportCatalog(newer,[{id:'my-checklist',name:'Meine Liste',category_ids:['102','bl:fld1234']}]);
const restored=n.prepare(exp),lists=n.checklistNormalize(exp,restored);
eq(restored.length,5);eq(lists[0].category_ids,['102','bl:fld1234']);
eq(restored.find(x=>x.id==='bl:opt1234').parent,'bl:fld1234');
eq(exp.categories.some(x=>x.id==='101'&&x.parent==='#'),true);
for(const f of [
()=>n.renameOwnNode(nodes,'102','Änderung importierter BEEP-IDs'),
()=>n.addField(nodes,{id:'bl:bad00',parentId:'bl:fld1234',label:'Fehler',input:'text'}),
()=>n.addField(nodes,{id:'bl:bad00',parentId:'bl:grp1234',label:'Fehler',input:'unsupported'}),
()=>n.addOption(nodes,{id:'bl:bad00',parentId:'102',label:'Fehler'}),
()=>n.addOption(nodes,{id:'bl:opt1234',parentId:'bl:fld1234',label:'Doppelte ID'}),
()=>n.addGroup(nodes,{id:'bl:grp2222',label:' '})
]){assert.throws(f);checks++;}
console.log('Bienenlogger eigene Katalogverwaltung:',checks,'Tests PASS');
