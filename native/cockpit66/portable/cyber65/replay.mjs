async function readFile(url){const r=await fetch(url);if(!r.ok)throw Error('BUNDLED_CORPUS_UNAVAILABLE');return r.text();}
import {CustomerMockSession,SYNTHETIC_PROFILES} from './session.mjs';
import {sha,clone,exact} from './contracts.mjs';
import {unhex} from '../protocol22/wire.mjs';
export async function loadCorpus(){const c=JSON.parse(await readFile(new URL('./corpus.json',import.meta.url),'utf8'));exact(c,['body','sha256']);if(sha(c.body)!==c.sha256||c.body.format!=='aeris-cyber65-corpus'||c.body.version!==1||c.body.cases.length>64)throw Error('CORPUS_INTEGRITY');return c;}
export async function replay(c,s){
 if(sha(c.body)!==c.sha256||!c.body.cases.some(x=>sha(x)===sha(s)))throw Error('SCENARIO_NOT_BOUND_TO_CORPUS');
 let time=0,transfer=null,oldContext=null;const session=new CustomerMockSession({now:()=>time,corpusSha256:c.sha256,...s.unknownProfile?{}:{profiles:SYNTHETIC_PROFILES}}),actors={'pilot-a':session.credential('pilot-a'),'payload-b':session.credential('payload-b')};const outcomes=[],wireExpectations=[];
 for(let i=0;i<s.steps.length;i++){
  const step=s.steps[i],ctx=step.oldContext?oldContext:session.context(),actor=actors[step.actor]??{};let error=null,result;
  try{switch(step.kind){
   case'connect':result=await session.connect();oldContext??=clone(result);break;
   case'raw':session.deliver(unhex(step.hex),step.oldContext?{context:{sessionId:oldContext.sessionId,generation:oldContext.generation,configSha256:oldContext.configSha256}}:undefined);break;
   case'advance':time+=step.ms;session.snapshot();break;
   case'heartbeat':session.authority.heartbeat(actor,ctx);break;
   case'claim':session.authority.claim(actor,step.scope,ctx,'ACCEPT_EXCLUSIVE_MOCK_SCOPE');break;
   case'transfer':transfer=session.authority.transfer(actor,step.scope,step.to,ctx);break;
   case'accept':session.authority.accept(actor,transfer.id,ctx);break;
   case'decline':session.authority.decline(actor,transfer.id,ctx);break;
   case'release':session.authority.release(actor,step.scope,ctx);break;
   case'operator-loss':session.authority.lose(actor,ctx);break;
   case'link-down':session.loseLink();break;
   case'fail-next':session.failNext(step.mode);break;
   case'select':session.select(step.bindingId);break;
   case'declare-file':session.declareSyntheticFile({intentId:'intent-1',sha256:sha('synthetic declaration only'),bytes:16,origin:'SYNTHETIC_DECLARATION_NO_PHYSICAL_FILE'});break;
   case'request':{
    const input={bindingId:step.bindingId,operation:step.operation,value:step.value,context:ctx,...step.extra?{extra:step.extra}:{}};
    result=session.request(actor,input);if(step.wire)wireExpectations.push({step:i,...clone(step.wire)});break;
   }
   default:throw Error('UNKNOWN_CORPUS_STEP');
  }}catch(e){error=e.message;}
  const pass=step.expectError?error!==null&&new RegExp(step.expectError).test(error):error===null;
  outcomes.push({step:i,kind:step.kind,error,expectedError:step.expectError??null,pass});
 }
 const review=session.review(),r=review.body,out=r.transport.transport.outbound;
 const assertions=[{name:'all scripted outcomes',pass:outcomes.every(x=>x.pass)},{name:'send count',pass:out.length===s.expect.sendCount},{name:'no physical evidence or retry/flight',pass:r.actualImages===0&&r.automaticRetries===0&&r.flightCommandsEncoded===0}];
 if(s.expect.states)assertions.push({name:'transaction states',pass:JSON.stringify(r.transactions.map(x=>x.state))===JSON.stringify(s.expect.states)});
 if(s.expect.owner)for(const [scope,owner]of Object.entries(s.expect.owner))assertions.push({name:'owner '+scope,pass:r.authority.grants.find(x=>x.scope===scope)?.owner===owner});
 if(s.expect.absentScopes)for(const scope of s.expect.absentScopes)assertions.push({name:'no grant '+scope,pass:!r.authority.grants.some(x=>x.scope===scope)});
 if(s.expect.grantCount!==undefined)assertions.push({name:'grant count',pass:r.authority.grants.length===s.expect.grantCount});
 if(s.expect.declarations!==undefined)assertions.push({name:'synthetic declarations',pass:r.syntheticFileDeclarations.length===s.expect.declarations});
 if(s.expect.selection)assertions.push({name:'view only',pass:r.transport.viewSelection===s.expect.selection});
 return {scenarioId:s.id,pass:assertions.every(x=>x.pass),outcomes,assertions,wireExpectations,review};
}
