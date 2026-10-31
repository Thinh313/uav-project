// Controlled reproduction of alternative causes for a shared observer error.
// This does not fix or prove the cause of the historical runtime failure.
import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';
import {Observations42} from '../flightsafety42/observe.mjs';
import {encodeFull} from '../apstream40/wire.mjs';
import {BINARY} from './contract.mjs';
const m={scope:'OWNED_REAL_SITL_FLIGHT_TEST_ONLY',binarySha256:BINARY,containerId:'a'.repeat(64),pid:1,startedAt:'mock',system:42,component:1,session:'closure-mock'};
const hb=seq=>encodeFull(0,{type:2,autopilot:3,base_mode:89,custom_mode:9,system_status:3},{system:42,component:1,seq});
const rows=[];
{
 const o=new Observations42(m);o.receive(hb(0),0,0);const retained=hb(1);
 o.loss('SOCKET_CLOSED');assert.throws(()=>o.receive(retained,1,1),/LOST_OR_STALE_RECEIPT/);
 rows.push({id:'closed-before-queued-rx-decode',pass:true,error:'LOST_OR_STALE_RECEIPT',causeKnownInFixture:'observer already dead'});
}
{
 const o=new Observations42(m);assert.throws(()=>o.receive(hb(0),0,1601),/LOST_OR_STALE_RECEIPT/);
 rows.push({id:'actual-age-too-old-same-error',pass:true,error:'LOST_OR_STALE_RECEIPT',causeKnownInFixture:'processing age >1500ms'});
}
{
 const o=new Observations42(m);o.receive(hb(0),0,0);o.receive(hb(1),1,1);assert.equal(o.frames.length,2);o.loss('SOCKET_CLOSED');
 rows.push({id:'decode-drained-before-close',pass:true,decodedFrames:2});
}
await writeFile('evidence/simdrop77/closure-mock.json',JSON.stringify({status:'PASS_SCOPED_CAUSE_DISAMBIGUATION_MOCK',passed:rows.length,total:rows.length,rows,
 historicalRootCause:'NOT_PROVEN; shared error cannot distinguish hypotheses',operationalSourceChanged:false},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({passed:rows.length,total:rows.length}));
