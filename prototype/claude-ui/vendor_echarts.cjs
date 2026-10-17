// SPDX-License-Identifier: GPL-3.0-or-later
'use strict';
const fs=require('node:fs'),path=require('node:path');
const root=__dirname;
const packageRoot=path.dirname(require.resolve('echarts/package.json'));
if(require('echarts/package.json').version!=='5.6.0')throw Error('Expected locked ECharts 5.6.0');
fs.mkdirSync(path.join(root,'vendor'),{recursive:true});
for(const [source,target] of [['dist/echarts.min.js','echarts.min.js'],['LICENSE','echarts-LICENSE.txt'],['NOTICE','echarts-NOTICE.txt']]){
 fs.copyFileSync(path.join(packageRoot,source),path.join(root,'vendor',target));
}
fs.copyFileSync(path.join(path.dirname(require.resolve('zrender/package.json')),'LICENSE'),path.join(root,'vendor','zrender-LICENSE.txt'));
console.log('Vendored Apache ECharts 5.6.0 with LICENSE and NOTICE');
