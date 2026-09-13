// Bounded retries for local, read-only browser probes only. Never retries data defects.
export async function deliverWithBoundedRetry(run,isUnchanged=()=>true){
 const attempts=[];
 for(let i=0;i<2;i++){
  if(!isUnchanged())return {ok:false,stage:'input',code:'input_changed',error:'Input changed after report preflight; review the new version.',attempts};
  let result;
  try{result=await run();}catch(error){result=error.deliveryResult||{ok:false,stage:'package',code:'delivery_failed',error:String(error.message)};}
  attempts.push({attempt:i+1,ok:result.ok===true,stage:result.stage||'complete',code:result.code||null,error:result.error||null,screenshot:result.screenshot||null});
  if(!isUnchanged())return {ok:false,stage:'input',code:'input_changed',error:'Input changed during rendering; output is not certified against the new source.',attempts};
  if(result.ok||!['reader_timeout','browser_timeout','probe_timeout'].includes(result.code)||!['static_charts','verification'].includes(result.stage))return {...result,attempts};
  if(i===1)return {...result,attempts};
 }
}
