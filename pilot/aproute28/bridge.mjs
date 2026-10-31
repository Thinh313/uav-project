import net from 'node:net';
import {createHash} from 'node:crypto';
import {Decoder,encode,hex,unhex} from '../protocol22/wire.mjs';
import {MockTransport} from '../transport25/mock.mjs';
import {TransportBroker} from '../transport25/broker.mjs';
import {NETWORK_CONFIG,validateCommand} from '../transport26/bridge.mjs';
export const PORTS=Object.freeze({gcs:5774,busA:5775,busB:5776});
export const TARGET_BUS=Object.freeze({100:'busA',154:'busA',102:'busB',101:'busB'});
const sha=b=>createHash('sha256').update(b).digest('hex');
export class Journal{
 rows=[];bytes=0;failure=null;
 constructor({maxRows=4096,maxBytes=2*1024*1024}={}){if(!Number.isSafeInteger(maxRows)||maxRows<1||maxRows>4096||!Number.isSafeInteger(maxBytes)||maxBytes<1||maxBytes>2*1024*1024)throw Error('Evidence limits');this.maxRows=maxRows;this.maxBytes=maxBytes;}
 add(kind,detail={}){const row={n:this.rows.length+1,at:new Date().toISOString(),atMs:performance.now(),kind,...structuredClone(detail)};const b=JSON.stringify(row).length;if(this.rows.length>=this.maxRows||this.bytes+b>this.maxBytes){this.failure??='RAW_EVIDENCE_BOUND';throw Error(this.failure);}this.bytes+=b;this.rows.push(row);return row;}
}
export function validateGcs(bytes,record,context){const f=validateCommand(bytes,record,context),p=f.fields;
 const zero=names=>names.every(k=>p[k]===0),nan=k=>Number.isNaN(p[k]);
 if(p.command===512&&!zero(['param2','param3','param4','param5','param6','param7']))throw Error('Exact discovery profile');
 if([531,532].includes(p.command)&&(!nan('param4')||!zero(['param5','param6','param7'])))throw Error('Exact camera percent profile');
 if(p.command===2000&&(!nan('param7')||!zero(['param5','param6'])))throw Error('Exact single capture profile');
 if(p.command===1000&&(!nan('param3')||!nan('param4')||!zero(['param5','param6'])))throw Error('Exact gimbal angle profile');
 if(p.command===1001&&!zero(['param5','param6']))throw Error('Exact authority profile');return f;
}
// Only SERIAL0 is reachable here. Peers have no reference to the broker/GCS socket.
export class ArduPilotBridge{
 mock=new MockTransport();broker=new TransportBroker({transport:this.mock,sessionId:'aproute28'});
 journal;#socket=null;#decoder=new Decoder();#context=null;#phase='CLOSED';#epoch=0;#hb=null;#seen=new Map();#sent=new Set();#timer=null;#opened=0;#gcsSeq=0;#pauseHB=false;#reason=null;
 constructor(limits){this.journal=new Journal(limits);}
 #log(k,d={}){try{return this.journal.add(k,{epoch:this.#epoch,...d});}catch(e){this.#revoke(e.message);return null;}}
 #revoke(reason){if(this.#phase==='CLOSED'||this.#phase==='LINK_DOWN_RECONNECT_REQUIRED')return;this.#reason=reason;this.#phase='LINK_DOWN_RECONNECT_REQUIRED';this.mock.down('mock-a');this.#socket?.destroy();clearInterval(this.#timer);}
 #poll(){if(this.#phase!=='CONNECTED')return;const now=performance.now();if((!this.#hb&&now-this.#opened>6000)||(this.#hb&&now-this.#hb.observedAtMs>3000))return this.#revoke('ACTUAL_AP_HEARTBEAT_STALE');for(const[c,t]of this.#seen)if(now-t>3000)return this.#revoke('PAYLOAD_HEARTBEAT_STALE_'+c);const s=this.broker.snapshot();if(s.protocol.events.some(e=>e.type==='COMPONENT_INVALIDATED'&&e.reason==='boot regression or reordered old boot'))this.#revoke('PAYLOAD_BOOT_REGRESSION_RECONNECT_REQUIRED');}
 async connect(){if(this.#phase!=='CLOSED')throw Error('Explicit close required');this.#phase='CONNECTING';const epoch=++this.#epoch;this.#context=await this.broker.connect(NETWORK_CONFIG);this.#decoder=new Decoder();this.#seen.clear();this.#sent.clear();this.#hb=null;this.#pauseHB=false;this.#reason=null;this.#opened=performance.now();const s=net.createConnection({host:'127.0.0.1',port:PORTS.gcs});this.#socket=s;s.setNoDelay(true);
 s.on('data',chunk=>{if(epoch!==this.#epoch||this.#phase!=='CONNECTED')return;try{for(let i=0;i<chunk.length;i+=4096){const part=new Uint8Array(chunk.subarray(i,i+4096));if(!this.#log('GCS_RX_CHUNK',{rawHex:hex(part)}))return;for(const f of this.#decoder.push(part)){if(!this.#log('GCS_RX_FRAME',{rawHex:f.rawHex,sha256:sha(unhex(f.rawHex)),system:f.system,component:f.component,id:f.id}))return;if(f.system===42&&f.component===1){if(f.id!==0)continue;if(f.fields.base_mode&128){this.#revoke('UNEXPECTED_ARMED');return;}if(this.#pauseHB)continue;this.#hb={...f,origin:'ACTUAL_ARDUCOPTER_SERIAL0_HEARTBEAT',observedAtMs:performance.now()};}else if(f.system===42&&Object.hasOwn(TARGET_BUS,f.component)){if(f.id===0)this.#seen.set(f.component,performance.now());}
 this.mock.deliver(unhex(f.rawHex),{context:this.#context});if(!this.#log('BROKER_DELIVERY',{rawHex:f.rawHex,origin:f.component===1?'ACTUAL_AP_HEARTBEAT':'SYNTHETIC_PAYLOAD_VIA_ACTUAL_AP'}))return;
 } }this.#poll();}catch(e){this.#log('RECEIVE_FAILURE',{error:e.message});this.#revoke(e.message);}});
 s.on('error',e=>{if(epoch!==this.#epoch)return;this.#log('GCS_SOCKET_ERROR',{error:e.code??e.message});this.#revoke('GCS_SOCKET_ERROR');});s.on('close',()=>{if(epoch===this.#epoch)this.#revoke('GCS_SOCKET_CLOSE');});
 try{await new Promise((resolve,reject)=>{const timer=setTimeout(()=>{s.destroy();reject(Error('Connect deadline'));},3000);s.once('connect',()=>{clearTimeout(timer);resolve();});s.once('error',e=>{clearTimeout(timer);reject(e);});});this.#phase='CONNECTED';this.#log('GCS_CONNECTED',{port:PORTS.gcs,host:s.remoteAddress});this.#heartbeat();this.#timer=setInterval(()=>{try{this.#poll();if(this.#phase==='CONNECTED')this.#heartbeat();}catch(e){this.#revoke(e.message);}},500);return structuredClone(this.#context);}catch(e){this.close();throw e;}
 }
 #heartbeat(){const b=encode(0,{type:6,autopilot:8,mavlink_version:3},{system:255,component:190,seq:this.#gcsSeq++%256});this.#write(b,'GCS_HEARTBEAT_TX');}
 #write(bytes,kind,detail={}){const s=this.#socket;if(this.#phase!=='CONNECTED'||!s||s.destroyed||s.writableLength>4096){this.#revoke('WRITE_UNCERTAIN');throw Error('WRITE_UNCERTAIN_NO_RETRY');}if(!this.#log(kind,{rawHex:hex(bytes),sha256:sha(bytes),...detail}))throw Error('RAW_EVIDENCE_BOUND');s.write(bytes,e=>{if(e){this.#log('LOCAL_WRITE_UNCERTAIN',{error:e.code??e.message});this.#revoke('WRITE_UNCERTAIN');}});}
 dispatch(intent){this.#poll();if(this.#phase!=='CONNECTED'||!this.#hb)throw Error('Current disarmed AP link required');const context=structuredClone(this.#context);if(JSON.stringify(intent.context)!==JSON.stringify(context))throw Error('Reviewed current context required');const r=this.broker.request(structuredClone(intent));if(r.override)throw Error('Uncertain admission');const bytes=unhex(r.protocol.rawCommandHex),f=new Decoder().push(bytes)[0],p=f.fields;const review={context,rawHex:hex(bytes),targetSystem:p.target_system,targetComponent:p.target_component,command:p.command};validateGcs(bytes,review,this.#context);if(this.#sent.has(r.id))throw Error('No resend');this.#sent.add(r.id);this.#write(bytes,'GCS_COMMAND_TX',{transactionId:r.id,bindingId:r.bindingId,expectedBus:TARGET_BUS[p.target_component],...review});return r;}
 pauseHeartbeatDelivery(){this.#pauseHB=true;this.#log('FAULT_HEARTBEAT_DELIVERY_PAUSED');}
 cut(){this.#socket?.destroy();}
 snapshot(){this.#poll();return{format:'aeris-aproute28-actual-router-review',version:1,phase:this.#phase,reason:this.#reason,epoch:this.#epoch,context:structuredClone(this.#context),aircraft:structuredClone(this.#hb),broker:this.broker.snapshot(),network:structuredClone(this.journal.rows),networkEvidenceComplete:this.journal.failure===null,evidenceFailure:this.journal.failure,decoderStats:structuredClone(this.#decoder.stats),automaticRetries:0,automaticReconnects:0,commandConnection:'ONLY_ACTUAL_AP_SERIAL0',physicalMedia:[],physicalMediaVerified:false,causalExecutionProven:false};}
 close(){this.#phase='CLOSED';++this.#epoch;clearInterval(this.#timer);this.#socket?.destroy();this.broker.disconnect();}
}
