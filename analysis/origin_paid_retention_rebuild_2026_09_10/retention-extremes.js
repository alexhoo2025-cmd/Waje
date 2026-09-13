// Same native table, value-based extrema. __REVIEWED_RATES__ is bound to the saved aggregate snapshot at packaging.
(() => {
  const reviewed=__REVIEWED_RATES__;
  const fields=['第2日','第7日','第15日','第30日'];let pending=false;
  function paint(){
    pending=false;
    for(const table of document.querySelectorAll('section[data-artifact-id="new-paid"] table')){
      const headers=[...table.querySelectorAll('thead th')].map(c=>c.textContent.trim());
      const rows=[...table.querySelectorAll('tbody tr')];
      let usesReviewed=true;
      const values=rows.map(row=>Object.fromEntries(fields.map(field=>{
        const index=headers.indexOf(field),cell=row.cells[index],name=row.cells[0]?.textContent.trim();
        const text=cell?.textContent.trim(),reference=reviewed[name]?.[field];
        const match=text?.match(/^(\d+(?:\.\d+)?)%$/);
        if(!reference||reference.display!==text)usesReviewed=false;
        return [field,reference&&reference.display===text?reference.value:match?Number(match[1]):null];
      })));
      for(const field of fields){
        const index=headers.indexOf(field);if(index<0)continue;
        const numeric=values.map(v=>v[field]).filter(v=>v!==null&&Number.isFinite(v));
        const max=Math.max(...numeric),min=Math.min(...numeric);
        rows.forEach((row,i)=>{const cell=row.cells[index];if(!cell)return;delete cell.dataset.retentionExtreme;const v=values[i][field];if(v===null||max===min)return;if(v===max)cell.dataset.retentionExtreme='max';else if(v===min)cell.dataset.retentionExtreme='min';});
      }
      let caption=table.querySelector('caption[data-retention-legend]');
      if(!caption){caption=document.createElement('caption');caption.dataset.retentionLegend='true';table.prepend(caption);}
      const label='同列比较：蓝色为最高留存率，橙色为最低留存率。'+(usesReviewed?'显示值相同时，按原始精度判定。':'当前表格有显示值变更，请核对来源。');
      if(caption.textContent!==label)caption.textContent=label;
    }
  }
  new MutationObserver(()=>{if(!pending){pending=true;requestAnimationFrame(paint);}}).observe(document.body,{childList:true,subtree:true,characterData:true});paint();
})();
