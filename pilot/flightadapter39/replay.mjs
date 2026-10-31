import {makeCorpus,replayCorpus,replayCase} from './corpus.mjs';
import {sourceHashes,append} from './evidence.mjs';
import {digest} from '../apflight36/types.mjs';
const corpus=await makeCorpus(),corpusPath=await append('corpus',corpus),replay=await replayCorpus(corpus),bites=[];
async function bite(name,fn){let rejected=false;try{rejected=(await fn()).matched===false;}catch{rejected=true;}bites.push({name,rejected});}
await bite('case SHA',()=>replayCase({...corpus.cases[0],sha256:'0'.repeat(64)}));
for(const[id,key,value]of [['disconnect-revokes-all','inspectionAvailable',true],['stale-session','phase','MOCK_READBACK_READY'],
 ['parameter-wrong-type','paramCount',28],['missing-AP-state','failsafeStatus','MODELED_MOCK'],
 ['typed-read-wire-only-preflight-unknown','preflightState','READY_MOCK'],['typed-read-wire-only-preflight-unknown','executionProven',true],
 ['same-version-not-freshness-renewal','inspectionAvailable',true],['bytewise-protocol-without-Copter-policy','policyStatus','MAPPED_MOCK']])
 await bite('semantic rehash '+id+'/'+key,async()=>{const c=structuredClone(corpus.cases.find(c=>c.id===id));c.expected[key]=value;const{sha256,...body}=c;return replayCase({...body,sha256:await digest(body)});});
const report={at:new Date().toISOString(),status:replay.status==='MOCK_PASS'&&bites.every(x=>x.rejected)?'MOCK_PASS':'FAIL',corpusPath,replay,bites,
 sourceHashes:await sourceHashes(),networkSent:false,SITL_Android_Hera:'NOT_CHECKED'};
const path=await append('replay',report);console.log(JSON.stringify({path,status:report.status,cases:replay.caseCount,bites:bites.length,failures:replay.results.filter(x=>!x.matched)}));if(report.status==='FAIL')process.exitCode=1;
