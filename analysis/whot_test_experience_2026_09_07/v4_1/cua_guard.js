// Load in the CUA JavaScript session; supply its bound Chrome target.
// Does not recognize cards. A calibrated observer must supply fresh state.
function makeGuardedInput(target, clock, record) {
  let pending = null;
  const used = new Set();
  return {
    async submit(state, decision) {
      const now = clock();
      const stale = !Number.isFinite(state.captured_at_ms) || now < state.captured_at_ms || now-state.captured_at_ms>750;
      const key = `${state.match_id}:${state.state_seq}`;
      const identity = typeof state.match_id==='string' && state.match_id.length>0 &&
        decision.match_id===state.match_id && Number.isInteger(state.state_seq) &&
        decision.state_seq===state.state_seq && typeof decision.action_id==='string' && decision.action_id.length>0;
      const scope = state.origin==='https://test-h5.wajetan.com' && state.route==='/game/6001-whot' &&
        String(state.client_game_id)==='6001' && state.bet===1 && state.action_owner==='self' &&
        state.cards_verified===true && state.coordinates_verified===true &&
        decision.transform_version===state.transform_version && state.transform_version!=null;
      if (!identity || !scope || pending || used.has(key) || stale || !Number.isFinite(decision.expires_at_ms) || now>=decision.expires_at_ms || state.autoplay!==false || state.binding_verified!==true) {
        record({kind:'action_rejected',reason:'pending_stale_or_unverified',at_ms:now}); return false;
      }
      if (!Array.isArray(decision.point) || decision.point.length!==2 || !decision.point.every(Number.isFinite)) throw Error('invalid_point');
      used.add(key);pending=decision.action_id;
      record({kind:'action_submitted',action_id:pending,at_ms:now,state_seq:state.state_seq});
      try {await target.click(decision.point);await target.getAXState({emit:false});}
      catch(e) {record({kind:'action_unknown',action_id:pending,reason:'transport_error'});return false;}
      record({kind:'input_returned',action_id:pending,at_ms:clock(),accepted:null});return true;
    },
    resolve(actionId,accepted) {
      if (!pending || actionId!==pending) throw Error('action_id_mismatch');
      record({kind:'action_terminal',action_id:pending,accepted,at_ms:clock()});pending=null;
    }
  };
}
if (typeof module!=='undefined') module.exports={makeGuardedInput};
