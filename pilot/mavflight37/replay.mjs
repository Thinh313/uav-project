import {readFile,writeFile} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {makeCorpus,replayCorpus,replayCase} from './scenarios.mjs';
import {digest} from '../apflight36/types.mjs';
const out='evidence/mavflight37';let n=1;while(existsSync(`${out}/replay${n}.json`))n++;
const corpus=await makeCorpus();await writeFile(`${out}/corpus${n}.json`,JSON.stringify(corpus,null,2)+'\n',{flag:'wx'});
const replay=await replayCorpus(corpus),bites=[];
async function bite(name,fn){let rejected=false;try{const r=await fn();rejected=r.matched===false}catch{rejected=true}bites.push({name,rejected})}
await bite('bad case SHA',()=>replayCase({...corpus.cases[0],sha256:'0'.repeat(64)}));
for(const[id,field,fake]of[['ack-not-proof','phase','WIRE_READBACK_MATCHED'],['wire-only-unknown','state','READY_MOCK'],['parameter-encoding-not-guessed','phase','WIRE_READBACK_MATCHED'],['reboot-invalidates','proofAvailable',true]])await bite('rehashed false '+id,async()=>{const c=structuredClone(corpus.cases.find(c=>c.id===id));c.expected[field]=fake;const{sha256,...body}=c;return replayCase({...body,sha256:await digest(body)})});
await bite('forbidden operation ARM',async()=>{const c=structuredClone(corpus.cases[0]);c.input.steps.push({op:'ARM',t:19030});const{sha256,...body}=c;const r=await replayCase({...body,sha256:await digest(body)});return{matched:!r.errors.some(x=>x.includes('forbidden replay operation'))}});
const sourceHashes={};for(const name of ['wire.mjs','session.mjs','fence.mjs','telemetry.mjs','scenarios.mjs','replay.mjs','definitions.mjs'])sourceHashes['pilot/mavflight37/'+name]=createHash('sha256').update(await readFile('pilot/mavflight37/'+name)).digest('hex');
const report={at:new Date().toISOString(),status:replay.status==='MOCK_PASS'&&bites.every(x=>x.rejected)?'MOCK_PASS':'FAIL',replay,bites,sourceHashes,realAP_SITL:'NOT_CHECKED',physicalExecutionProven:false,operationalAllowed:false};
await writeFile(`${out}/replay${n}.json`,JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({receipt:`replay${n}`,status:report.status,caseCount:replay.caseCount,failures:replay.results.filter(r=>!r.matched),bites}));if(report.status==='FAIL')process.exitCode=1;
