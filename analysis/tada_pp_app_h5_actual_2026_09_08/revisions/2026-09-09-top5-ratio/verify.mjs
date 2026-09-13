import fs from 'node:fs';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const out=path.dirname(fileURLToPath(import.meta.url));
const base=path.resolve(out,'../..');
const read=p=>JSON.parse(fs.readFileSync(path.join(base,p),'utf8'));
const rawGames=read('queries/17_full_games.result.json');
const rawCore=read('queries/14_full_core.result.json');
const corrections=read('queries/21_targeted_duplicate_corrections.result.json');
const computed=read('analysis-results.json');
const close=(a,b)=>assert(Math.abs(a-b)<Math.max(1e-5,Math.abs(b)*1e-12),`${a} != ${b}`);
const results=[];
for(const platform of ['APP','H5']) for(const provider of ['Tada','PP']){
  const raw=rawCore.find(r=>r.product_mode==='Waje'&&r.time_grain==='period'&&r.segment_grain==='platform'&&r.platform_group===platform&&r.provider_group===provider&&r.age_segment==='all_ages');
  assert(raw);
  const cc=corrections.filter(c=>c.correction_grain==='core_correction'&&c.product_mode==='Waje'&&c.platform===platform&&c.provider===provider);
  const total=(Number(raw.effective_stake_source_units)-cc.reduce((s,c)=>s+Number(c.duplicate_stake_source_units),0))/100;
  const rows=rawGames.filter(r=>r.platform_group===platform&&r.provider===provider).map(r=>{
    const gc=corrections.filter(c=>c.correction_grain==='game_correction'&&c.product_mode==='Waje'&&c.platform===platform&&c.provider===provider&&c.play_id===r.play_id);
    return {play_id:r.play_id,stake:(Number(r.effective_stake_source_units)-gc.reduce((s,c)=>s+Number(c.duplicate_stake_source_units),0))/100};
  }).sort((a,b)=>b.stake-a.stake);
  assert.equal(new Set(rows.map(r=>r.play_id)).size,rows.length);
  const top5=rows.slice(0,5),head=top5.reduce((s,r)=>s+r.stake,0),remaining=total-head;
  const existing=computed.heads.find(r=>r.platform===platform&&r.provider===provider);
  close(total,existing.total_stake);close(head,existing.top5_stake);close(remaining,existing.excluding_top5_stake);
  results.push({platform,provider,total,top5,top5_stake:head,top5_share:head/total,remaining,listed_games:rows.length,unlisted_stake:total-rows.reduce((s,r)=>s+r.stake,0)});
}
const comparisons=['APP','H5'].map(platform=>{
  const t=results.find(r=>r.platform===platform&&r.provider==='Tada'),p=results.find(r=>r.platform===platform&&r.provider==='PP');
  return {platform,total_ratio:t.total/p.total,remaining_ratio:t.remaining/p.remaining,retained_share_factor:(1-t.top5_share)/(1-p.top5_share)};
});
const ov=provider=>computed.overview.find(r=>r.platform==='APP'&&r.provider===provider&&r.age==='all_ages');
const t=ov('Tada'),p=ov('PP');
const decomposition={scope:'APP全量游戏；不能作为剔除前5后人群的分解',bettors_ratio:t.bettors/p.bettors,rounds_per_bettor_ratio:t.avg_rounds_per_bettor/p.avg_rounds_per_bettor,stake_per_round_ratio:t.avg_stake_per_round/p.avg_stake_per_round};
close(decomposition.bettors_ratio*decomposition.rounds_per_bettor_ratio*decomposition.stake_per_round_ratio,comparisons[0].total_ratio);
const receipt={status:'passed',verification_scope:'从已保存原始聚合查询及去重修正独立复算；本次未重新查询线上数据',period:'2026-08-01/2026-09-07',ranking:'各渠道、各厂商分别按本期有效下注额排序；不是APP与H5合并榜',results,comparisons,decomposition,limitations:['剩余总额保留原总量中未展示的隐私抑制游戏金额','比较的是不同游戏组合的总额，并非同款游戏或单款平均表现','人数、频次、局均金额分解适用于APP全量游戏，不是剩余游戏人群']};
fs.writeFileSync(path.join(out,'calculation-receipt.json'),JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify(receipt,null,2));
