import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {randomUUID} from 'node:crypto';
import {createMediaServer} from '../../pilot/field01/media/server.mjs';
import {PublisherTransport,clockValidityWindow} from '../../pilot/field01/media/client.mjs';
import {encodePacket} from '../../media/big02/relay-core.mjs';
const root=path.resolve('evidence/field01'),out=path.join(root,'media-clock-test-'+Date.now());
await fs.mkdir(root,{recursive:true});const app=await createMediaServer({port:0,out,schedule:false});await app.listen();const origin=app.origin;
const publisher=await fetch(origin+'/api/bootstrap?role=publisher').then(r=>r.json());
const checks=[],renewals=[],accepted=[];let configId=randomUUID(),frameId=0;
const session={run:'s'+randomUUID().replaceAll('-','').slice(0,20),boot:randomUUID(),feed:'rgb',configId,profileId:'H264-720P30-V1',viewerId:publisher.viewerId};
async function json(route,value,binary=false){const response=await fetch(origin+'/api/'+route,{method:'POST',headers:{Origin:origin,Authorization:'Bearer '+publisher.bearer,'X-Media-Nonce':publisher.nonce,'Content-Type':binary?'application/octet-stream':'application/json'},body:binary?value:JSON.stringify(value)});const result=await response.json();if(!response.ok)throw Error(result.error);return result;}
async function calibrate(){const samples=[];for(let i=0;i<5;i++){const start=performance.now(),q=await json('clock',{browserSendMs:start}),end=performance.now();const result={lowerMs:q.serverSentMs-end,upperMs:q.serverReceivedMs-start,...clockValidityWindow(end),roundtripMs:end-start};if(result.roundtripMs<=20&&result.upperMs>=result.lowerMs)samples.push(result);}assert.ok(samples.length,'CALIBRATION_UNKNOWN');return samples.sort((a,b)=>a.roundtripMs-b.roundtripMs)[0];}
let clock=await calibrate();const transport=new PublisherTransport({session,postChunk:b=>json('chunk',b,true),json,calibrate,packet:encodePacket});
const item=(type='key',age=0)=>({frameId:++frameId,timestampUs:Math.round((performance.now()-age)*1000),type,bytes:new Uint8Array([0,0,1,101,3])});
const test=async(name,fn)=>{await fn();checks.push({name,status:'PASS'});console.log(name+' PASS');};
try{
 await test('clock marker lifetime stays exact at every60second boundary',async()=>{for(let i=0;i<100000;i++){const q=clockValidityWindow(55000+i*.117);assert.equal(q.validUntilBrowserMs-q.sampledBrowserMs,60000);}});
 await json('configure',{session,clock});
 await test('stalled encoded item discarded before network; sequence preserved',async()=>{const before=app.state().metrics.requests,result=await transport.publish(item('key',1100));assert.equal(result.reason,'STALE_ENCODED_ITEM_DROPPED');assert.equal(transport.sequence,0);assert.equal(app.state().metrics.requests,before);assert.equal((await transport.publish(item('delta'))).reason,'WAIT_FRESH_SOURCE_KEYFRAME');assert.equal((await transport.publish(item())).accepted,true);assert.equal(transport.sequence,1);});
 await test('clock rejection drops item without retry then recovers with fresh keyframe',async()=>{await json('source-clock',{configId,clock:{...clock,lowerMs:clock.lowerMs-2200,upperMs:clock.upperMs-2200}});const previous=transport.sequence;assert.equal((await transport.publish(item())).reason,'SOURCE_CLOCK_RECALIBRATED_ITEM_DROPPED');assert.equal(transport.sequence,previous);assert.equal((await transport.publish(item('delta'))).reason,'WAIT_FRESH_SOURCE_KEYFRAME');assert.equal((await transport.publish(item())).accepted,true);assert.equal(transport.sequence,previous+1);});
 await test('second clock recovery bounded and third failure closes without retry',async()=>{for(let i=0;i<2;i++){clock=await calibrate();await json('source-clock',{configId,clock:{...clock,lowerMs:clock.lowerMs+2200,upperMs:clock.upperMs+2200}});if(i===0)assert.equal((await transport.publish(item())).reason,'SOURCE_CLOCK_RECALIBRATED_ITEM_DROPPED');else await assert.rejects(()=>transport.publish(item()),/SOURCE_CLOCK_RECOVERY_BOUND/);}assert.equal(transport.clockRecoveries,2);});
 clock=await calibrate();await json('source-clock',{configId,clock});const started=performance.now();let nextRenewal=started+30000;
 const durationMs=Number(process.argv[2]??95000);
 while(performance.now()-started<durationMs){if(performance.now()>=nextRenewal){clock=await calibrate();await json('source-clock',{configId,clock});renewals.push({atElapsedMs:performance.now()-started,clock});nextRenewal+=30000;console.log('renewed source clock '+renewals.length+' at '+Math.round(performance.now()-started)+'ms');}const result=await transport.publish(item());if(result.accepted)accepted.push({atElapsedMs:performance.now()-started,sequence:transport.sequence});await new Promise(r=>setTimeout(r,100));}
 await test('95-second real HTTP stream survives three source-clock renewals',async()=>{assert.ok(performance.now()-started>=95000);assert.equal(renewals.length,3);assert.ok(accepted.length>=900);assert.ok(accepted.at(-1).atElapsedMs>=94000);});
}catch(error){checks.push({name:'UNEXPECTED_FAILURE',status:'FAIL',error:error.stack});process.exitCode=1;}finally{await app.close();await fs.writeFile(path.join(root,'media-clock-recovery-test-result.json'),JSON.stringify({at:new Date().toISOString(),checks,renewals,acceptedCount:accepted.length,first:accepted[0],last:accepted.at(-1),scope:'ACTUAL_LOCALHOST_HTTP_TRANSPORT_AND_CLOCK_RENEWAL_TEST_SYNTHETIC_NON_CODEC_BYTES_NOT_BROWSER_720P_PERFORMANCE',evidenceDirectory:out},null,2)+'\n');console.log(JSON.stringify(checks));}
