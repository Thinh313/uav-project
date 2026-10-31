import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {parseRaw,evaluateActual} from './replay.mjs';
import {Observations42} from './observe.mjs';
import {unhex,hex,encodeFull} from '../apstream40/wire.mjs';
const run=process.argv[2]??'run03';const paths=['session01','session02'].map(n=>'evidence/flightsafety42/'+run+'/'+n+'-raw.jsonl'),contents=await Promise.all(paths.map(p=>readFile(p,'utf8'))),base=contents.map(parseRaw),results=[];
function rechained(rows){let prev='0'.repeat(64);return rows.map((r,k)=>{const {sha256,...p}=r;delete p.prev;delete p.n;const data={n:k+1,utc:p.utc,prev,...Object.fromEntries(Object.entries(p).filter(([x])=>x!=='utc'))};const out={...data,sha256:createHash('sha256').update(JSON.stringify(data)).digest('hex')};prev=out.sha256;return JSON.stringify(out)+'\n';}).join('');}
function bite(name,fn){assert.throws(fn,undefined,name+' must reject');results.push({name,rejected:true,scope:'OFFLINE_MUTATION_NO_NETWORK_NO_OLD_OUTPUT_WRITE'});}
function alterFrames(rows,change){const obs=new Observations42(rows[0].manifest);return rows.map(r=>{if(r.kind!=='RX')return r;const initial=!obs.started;const out=obs.receive(unhex(r.rawHex),r.hostMs),prefix=initial&&obs.started?obs.snapshot().preambleHex:'';const frames=out.flatMap(f=>{const replacement=change(f,r);if(replacement===false)return[];return [typeof replacement==='string'?replacement:f.rawHex];});const rawHex=prefix+frames.join('');return rawHex?{...r,rawHex}:null;}).filter(Boolean);}
const rows=base.map(x=>structuredClone(x.rows));
bite('byte tamper breaks hash without rechain',()=>{const r=structuredClone(rows[0]);const rx=r.find(x=>x.kind==='RX');rx.rawHex=rx.rawHex.replace(/^../,'00');parseRaw(r.map(x=>JSON.stringify(x)+'\n').join(''));});
bite('missing final newline',()=>parseRaw(contents[0].slice(0,-1)));
bite('incomplete writer close notaccepted',()=>parseRaw(rechained(rows[0].slice(0,-1))));
bite('dropped frame-capture row chain rejects',()=>parseRaw(rows[0].filter((_,i)=>i!==10).map(x=>JSON.stringify(x)+'\n').join('')));
bite('ACK-only/removed actual airborne telemetry cannotPASS',()=>evaluateActual([parseRaw(rechained(alterFrames(rows[0],f=>f.id===33&&f.fields.relative_alt>9000?false:undefined))),base[1]]));
bite('no observed circle breach cannotPASS despite RTL',()=>evaluateActual([parseRaw(rechained(alterFrames(rows[0],f=>f.id===162&&f.fields.breach_status===1?false:undefined))),base[1]]));
bite('foreign circle breach cannotPASS',()=>evaluateActual([parseRaw(rechained(alterFrames(rows[0],f=>f.id===162&&f.fields.breach_status===1?hex(encodeFull(f.id,f.fields,{system:43,component:1,seq:f.seq})):undefined))),base[1]]));
bite('missing failsafe text cannotPASS from RTL alone',()=>evaluateActual([parseRaw(rechained(alterFrames(rows[0],f=>f.id===253&&/GCS Failsafe/.test(f.fields.text)?false:undefined))),base[1]]));
bite('resuming Guided cannotbeaccepted as retained RTL',()=>{const t=base[0].marks.find(x=>x.name==='GCS_HEARTBEAT_RESTORED').hostMs;evaluateActual([parseRaw(rechained(alterFrames(rows[0],(f,r)=>f.id===0&&r.hostMs>=t?hex(encodeFull(0,{...f.fields,custom_mode:4},{system:42,component:1,seq:f.seq})):undefined))),base[1]]);});
bite('missing finaldisarm cannotPASS',()=>evaluateActual([base[0],parseRaw(rechained(alterFrames(rows[1],f=>f.id===0?hex(encodeFull(0,{...f.fields,base_mode:f.fields.base_mode|128},{system:42,component:1,seq:f.seq})):undefined)))]));
bite('old process metadata cannotrebind reconnect',()=>{const b=structuredClone(rows[1]);b[0].manifest.pid++;evaluateActual([base[0],parseRaw(rechained(b))]);});
bite('bad arming-check mapping cannotPASS',()=>evaluateActual([parseRaw(rechained(alterFrames(rows[0],f=>f.id===22&&f.fields.param_id==='ARMING_SKIPCHK'?hex(encodeFull(22,{...f.fields,param_value:1},{system:42,component:1,seq:f.seq})):undefined))),base[1]]));
bite('no complete TX write receipt cannotPASS',()=>parseRaw(rechained(rows[0].filter((r,i)=>!(r.kind==='TX_WRITE_RETURN'&&i===rows[0].findIndex(x=>x.kind==='TX_WRITE_RETURN'))))));
bite('no new post-restoration heartbeat cannotPASS',()=>{const t=base[0].marks.find(x=>x.name==='GCS_HEARTBEAT_RESTORED').hostMs;evaluateActual([parseRaw(rechained(alterFrames(rows[0],(f,r)=>f.id===0&&r.hostMs>=t?false:undefined))),base[1]]);});
const out={run,status:'PASS_ALL_REQUIRED_MUTATIONS_REJECTED',passed:results.length,total:results.length,results,baselineRawSha256:base.map(s=>s.rawSha256),scope:'Semantic mutations have recomputed journal chains; no cryptographic authenticity or independent review claim'};let n=1;const {existsSync}=await import('node:fs');while(existsSync(`evidence/flightsafety42/bites${n}.json`))n++;await writeFile(`evidence/flightsafety42/bites${n}.json`,JSON.stringify(out,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:out.status,bites:results.length}));
