// Add value-aware classes to the existing native table; works after sorting/re-rendering.
(() => {
  const selector='section[data-artifact-id="decay-detail"] table';
  let scheduled=false;
  function paint(){
    scheduled=false;
    for(const table of document.querySelectorAll(selector)){
      const rows=[...table.querySelectorAll('tbody tr')];
      const values=rows.map(row=>[...row.cells].slice(1).map(cell=>{
        const match=cell.textContent.trim().match(/^(-?\d+(?:\.\d+)?)%$/);
        return match?Number(match[1]):null;
      }));
      const peaks=[0,1,2].map(col=>Math.max(...values.map(row=>row[col]).filter(v=>v!==null&&Number.isFinite(v))));
      table.classList.add('waje-decay-heatmap');
      if(!table.querySelector('caption[data-decay-legend]')){
        const caption=document.createElement('caption');caption.dataset.decayLegend='true';
        caption.textContent='衰减越大，暖色色阶越深；描边标出各列峰值。蓝色负值表示回访率回升。';
        table.prepend(caption);
      }
      rows.forEach((row,i)=>[...row.cells].slice(1).forEach((cell,j)=>{
        const value=values[i][j];
        if(value===null||!Number.isFinite(value)){delete cell.dataset.decayBand;delete cell.dataset.decayPeak;return;}
        cell.dataset.decayBand=value<0?'rebound':value>=30?'top':value>=15?'high':value>=8?'mid':'low';
        if(value===peaks[j])cell.dataset.decayPeak='true';else delete cell.dataset.decayPeak;
      }));
    }
  }
  const observer=new MutationObserver(()=>{if(!scheduled){scheduled=true;requestAnimationFrame(paint);}});
  observer.observe(document.body,{childList:true,subtree:true,characterData:true});
  paint();
})();
