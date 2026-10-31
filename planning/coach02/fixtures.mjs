import{Journal,makePackage}from'../../pilot/coach02/journal.mjs';import{EXERCISES,PROFILES,CONTRACT,targetAt,scriptedAxes,zero}from'../../pilot/coach02/contract.mjs';
let serial=0;
export function fixture(root,{exerciseId='hover',profileId='unloaded',sourceKind='SCRIPTED_MOCK'}={}){
 let source=500,host=1000;const context={sessionId:'m'+(++serial).toString(16).padStart(32,'0'),hostBoot:'fixture-host-clock',sourceClockId:'fixture-source-clock',operatorId:'scripted-reference-not-human',sourceKind,exerciseId,profileId};const j=new Journal(root,context,{nonce:'fixture-challenge',t1:1000,t2:1000},1000);
 function action(kind,data={},delta=1){source+=delta;host+=delta;return j.action({...context,kind,seq:j.state.nextSeq,sourceTimeMs:source,...data},host);}
 action('sync',{nonce:'fixture-challenge',t0:500,t3:500});action('neutral',{axes:zero()});action('grant');
 function run(policy='reference'){const count=Math.round(EXERCISES[exerciseId].durationS/CONTRACT.dtS);for(let i=0;i<count;i++){const axes=policy==='zero'?zero():scriptedAxes(j.state.model,targetAt(exerciseId,(i+1)*CONTRACT.dtS),PROFILES[profileId]);const r=action('tick',{leaseId:j.state.lease?.id,axes,keyEvents:[]},50);if(!r.accepted)throw Error('FIXTURE_TICK '+r.code);}return j.state;}
 return{j,context,action,run,get host(){return host;},get source(){return source;},package(){return makePackage(root,context.sessionId);}};
}
