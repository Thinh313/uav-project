import assert from 'node:assert/strict';
import {once} from 'node:events';
import {writeFile} from 'node:fs/promises';
import {ClockClient} from './clock_client.mjs';
const checks=[];
for(const test of ['unknown-nonce','malformed','capture-failure']){
 const rows=[],c=new ClockClient('test','epoch','host-python-monotonic',(k,d)=>{if(test==='capture-failure')throw Error('capture bound');rows.push({k,d});});
 await once(c.socket,'listening');
 const bytes=Buffer.from(test==='malformed'?'invalid':JSON.stringify({run:'test',epoch:'epoch',nonce:'unknown',backendClockDomain:'host-python-monotonic',backendReceiveNs:'1',backendSendNs:'2'}));
 assert.doesNotThrow(()=>c.socket.emit('message',bytes,{address:'127.0.0.1',port:9005}));assert.ok(c.error);assert.equal(c.matches,0);
 if(test!=='capture-failure')assert.equal(rows[0].d.rawHex,bytes.toString('hex'));
 await assert.rejects(c.sample());c.close();checks.push({name:test,pass:true,rawRetained:test!=='capture-failure',incompleteOnCaptureFailure:true});
}
await writeFile('evidence/sim32-pipe03/clock-client-tests.json',JSON.stringify({status:'PASS',checks,scope:'Node listener fail-closed handling; simulated packets, no flight'},null,2)+'\n',{flag:'wx'});
console.log('CLOCK_CLIENT_FAIL_CLOSED',checks.length);
