import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url)),base=path.resolve(dir,'../..');
const a=JSON.parse(fs.readFileSync(path.join(base,'artifact.json'))),block=a.manifest.blocks.find(b=>b.id==='share');
const old=block.body.split('\n\n')[1];
const next='**统计期：2026年8月1日—9月7日，共38个完整业务日，采用拉各斯时间。** 以下按行为当天的注册时长分组，不按充值状态分组；金额沿用报表单位。\n\n**新用户（注册0—29天）：** Tada下注额为APP **59.96亿**、H5 **16.52亿**；同组平台活跃人数分别为**89.94万／45.82万**，Tada下注渗透率为**6.75%／4.51%**。\n\n**老用户（注册30天及以上）：** Tada下注额为APP **325.37亿**、H5 **73.97亿**；同组平台活跃人数分别为**40.28万／7.55万**，Tada下注渗透率为**22.27%／22.50%**，两渠道接近。\n\n**全体用户（参考）：** Tada下注额为APP **386.02亿**、H5 **90.59亿**；平台活跃人数分别为**126.77万／52.81万**，Tada下注渗透率为**11.43%／6.94%**。全体包含注册日期未知者；用户可在期内由新转老，新老去重人数不能直接相加。\n\n**全体平均不能代替分组判断。** Tada在APP的新用户渗透率较高，老用户则两渠道接近；不能仅凭全体差异认定APP体验更好。';
const oldChart=block.body.split('\n\n')[2],newChart=oldChart.replace('下图以各端**全部Waje游戏下注额**为分母。','下图展示上述统计期的**全体用户（新老合计，含注册日期未知者）**，以各渠道全部Waje游戏下注额为分母，不是新用户或老用户单独的结果。');
assert(newChart!==oldChart);
let patch='*** Begin Patch\n';
for(const name of ['artifact.json','报告.md','build_report.py']){
 const file=path.join(base,name),text=fs.readFileSync(file,'utf8');assert(!fs.existsSync(path.join(dir,name+'.before')));fs.copyFileSync(file,path.join(dir,name+'.before'));
 patch+='*** Update File: '+file+'\n';
 if(name==='artifact.json'){const replacement=block.body.replace(old,next).replace(oldChart,newChart);const line=text.split('\n').find(l=>l.includes(JSON.stringify(block.body)));assert(line);patch+='@@\n-'+line+'\n+'+line.replace(JSON.stringify(block.body),JSON.stringify(replacement))+'\n';}
 else {const line=text.split('\n').find(l=>l.startsWith('APP渠道Tada下注额为'));assert(line);patch+='@@\n-'+line+'\n+'+next.split('\n').join('\n+')+'\n';const c=text.split('\n').find(l=>l.startsWith('下图以各端**全部Waje游戏下注额**'));assert(c);patch+='@@\n-'+c+'\n+'+c.replace(oldChart,newChart)+'\n';}
}
fs.copyFileSync(path.resolve(base,'../../output/html/Tada与PP-APP-H5下注与回访对比-2026-09-08.html'),path.join(dir,'report.before.html'));
fs.writeFileSync(path.join(dir,'text.json'),JSON.stringify({old,next,oldChart,newChart},null,2));
console.log(patch+'*** End Patch');
