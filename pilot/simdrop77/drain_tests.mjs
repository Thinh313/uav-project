import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';
import {RxDrain} from './rx_drain.mjs';
const rows=[];
{
 const d=new RxDrain();let finish,decoded=false;const job=new Promise(r=>finish=r).then(()=>{decoded=true;});d.track(job);let closed=false;const closing=d.drain().then(()=>closed=true);await Promise.resolve();assert.equal(closed,false);finish();await closing;assert.ok(decoded&&closed);rows.push({id:'queued-rx-before-close',pass:true});
}
{
 const d=new RxDrain();await d.drain();assert.throws(()=>d.track(Promise.resolve()),/RX_AFTER_CUTOFF/);rows.push({id:'no-new-admission-after-cutoff',pass:true});
}
{
 const d=new RxDrain();d.track(Promise.reject(Error('RECEIPT_STALE')));await Promise.resolve();await assert.rejects(()=>d.drain(),/RECEIPT_STALE/);rows.push({id:'already-settled-error-retained',pass:true});
}
{
 const d=new RxDrain();let reject;d.track(new Promise((_,r)=>reject=r));const closing=d.drain();reject(Error('DECODE_FAILED'));await assert.rejects(()=>closing,/DECODE_FAILED/);rows.push({id:'inflight-error-retained',pass:true});
}
{
 const d=new RxDrain(),resolvers=[];for(let i=0;i<64;i++)d.track(new Promise(r=>resolvers.push(r)));assert.throws(()=>d.track(Promise.resolve()),/RX_DRAIN_BOUND/);const closing=d.drain();resolvers.forEach(r=>r());await closing;rows.push({id:'bounded-and-lossless64',pass:true});
}
await writeFile('evidence/simdrop77/drain-mock.json',JSON.stringify({status:'PASS_SCOPED_RX_DRAIN',passed:rows.length,total:rows.length,rows,freshnessThresholdsChanged:false},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:rows.length,total:rows.length}));
