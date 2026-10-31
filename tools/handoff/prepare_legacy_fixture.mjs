// Explicitly reconstruct the original synthetic test record in ignored runtime/.
// Does not start a server, link, device or aircraft and never replaces other data.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import {validateHandoff} from '../../app/core/handoff.mjs';
import {validateExecutionRecord} from '../../app/core/execution-record.mjs';
const b=await validateHandoff(await fs.readFile('evidence/handoff09/completed.aeris-handoff.json','utf8'));
if(b.record.simulation!==true)throw Error('SYNTHETIC_FIXTURE_ONLY');
const spool=Buffer.from(b.spoolBase64,'base64');
if(crypto.createHash('sha256').update(spool).digest('hex')!==b.record.storage.spoolSha256)throw Error('SPOOL_SHA256');
await fs.mkdir('runtime/executions',{recursive:true});
const writes=[[`runtime/executions/${b.record.id}.json`,Buffer.from(JSON.stringify(b.record)+'\n')],[`runtime/executions/${b.record.id}.jsonl`,spool]];
for(const file of b.files){const raw=Buffer.from(file.base64,'base64');if(crypto.createHash('sha256').update(raw).digest('hex')!==file.sha256)throw Error('SYNTHETIC_MEDIA_SHA256');writes.push([`runtime/executions/media-${file.sha256}.bin`,raw]);}
for(const [p,raw]of writes){
 try{await fs.writeFile(p,raw,{flag:'wx'});}
 catch(e){if(e.code!=='EEXIST')throw e;const old=await fs.readFile(p);if(p.endsWith('.json')){if((await validateExecutionRecord(old.toString())).sha256!==b.record.sha256)throw Error('EXISTING_RECORD_DIFFERENT');}else if(!old.equals(raw))throw Error('EXISTING_SPOOL_DIFFERENT');}
}
console.log(JSON.stringify({status:'SYNTHETIC_FIXTURE_READY',id:b.record.id,sha256:b.record.sha256,flightOrDeviceStarted:false}));
