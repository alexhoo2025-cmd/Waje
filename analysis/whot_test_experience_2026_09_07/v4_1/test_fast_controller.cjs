const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
function load(name){const context={module:{exports:{}}};vm.runInNewContext(fs.readFileSync(path.join(__dirname,name),'utf8'),context);return context.module.exports;}
const {makeGuardedInput}=load('cua_guard.js');
const {makeFastController}=load('fast_controller.js');
(async()=>{
 let now=100,clicks=0;
 const records=[];
 const target={click:async()=>{clicks++;},getAXState:async()=>{}};
 const input=makeGuardedInput(target,()=>now,x=>records.push(x));
 const state={match_id:'m1',state_seq:1,captured_at_ms:100,origin:'https://test-h5.wajetan.com',route:'/game/6001-whot',client_game_id:6001,bet:1,action_owner:'self',cards_verified:true,coordinates_verified:true,transform_version:'v1',autoplay:false,binding_verified:true};
 const decision={match_id:'m1',state_seq:1,action_id:'a1',transform_version:'v1',action:'play',point:[10,20],expires_at_ms:500};
 for(const patch of [{bet:500},{autoplay:true},{action_owner:'opponent'},{origin:'https://example.com'},{coordinates_verified:false}])
   assert.equal(await input.submit({...state,...patch},decision),false);
 assert.equal(clicks,0);
 assert.equal(await input.submit(state,{...decision,state_seq:9}),false);
 assert.equal(await input.submit(state,decision),true);
 assert.equal(await input.submit({...state,state_seq:2},{...decision,state_seq:2}),false);
 input.resolve('a1',null);
 assert.equal(await input.submit(state,decision),false);
 assert.equal(clicks,1);
 let calls=0;
 const loop=makeFastController({clock:()=>now,record:x=>records.push(x),input:{submit:async()=>true},decide:(s,r,arm)=>{calls++;assert.equal(arm,'first_legal_play');return {...decision,state_seq:s.state_seq};}});
 assert.equal((await loop.frame({...state,captured_at_ms:-900},{})).status,'stale');
 assert.equal((await loop.frame({...state,action_owner:'opponent'},{})).status,'waiting');
 assert.equal((await loop.frame(state,{})).status,'pending_confirmation');
 assert.equal((await loop.frame(state,{})).status,'duplicate');
 assert.equal(calls,1);
 assert.equal((await loop.frame({...state,state_seq:2,autoplay:true},{})).status,'halted');
 assert.equal((await loop.frame({...state,state_seq:3},{})).status,'halted');
 console.log(JSON.stringify({status:'passed',test_type:'mock_adapters_only',real_clicks:0,live_latency_verified:false}));
})().catch(e=>{console.error(e);process.exitCode=1;});
