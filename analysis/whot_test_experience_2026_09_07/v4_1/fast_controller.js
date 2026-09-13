// Dependency-injected fast loop. No browser, native input, or model is created here.
// Actual calibrated observer and authorized input adapter must be supplied.
function makeFastController({clock,decide,input,record}) {
  let busy=false,halted=false,last=null;
  return {
    async frame(state,rules) {
      if(halted)return {status:'halted'};
      if(busy)return {status:'dropped_busy'};
      const key=`${state.match_id}:${state.state_seq}`;
      if(key===last)return {status:'duplicate'};
      const now=clock();
      if(!Number.isFinite(state.captured_at_ms)||now-state.captured_at_ms<0||now-state.captured_at_ms>750)
        return {status:'stale'};
      if(state.autoplay===true){halted=true;record({kind:'autoplay_stop',match_id:state.match_id});return {status:'halted'};}
      if(state.action_owner!=='self')return {status:'waiting'};
      busy=true;
      try {
        // Calibration always uses the simplest fixed arm. No shadow computation.
        const started=clock();
        const decision=decide(state,rules,'first_legal_play',started);
        if(decision.action==='wait')return {status:'rejected',reason:decision.reason};
        if(clock()>=decision.expires_at_ms)return {status:'expired_during_decision'};
        last=key;
        const submitted=await input.submit(state,decision);
        record({kind:'fast_attempt',match_id:state.match_id,state_seq:state.state_seq,
          submitted,frame_to_input_return_ms:clock()-state.captured_at_ms,
          turn_onset_to_click_ms:null});
        return {status:submitted?'pending_confirmation':'not_submitted'};
      } finally {busy=false;}
    },
    stop(){halted=true;},
    get halted(){return halted;}
  };
}
if(typeof module!=='undefined')module.exports={makeFastController};
