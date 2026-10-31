import net from 'node:net';
import {createHash} from 'node:crypto';
import {Decoder,unhex,hex} from '../protocol22/wire.mjs';
import {MockTransport} from '../transport25/mock.mjs';
import {TransportBroker} from '../transport25/broker.mjs';
import {validateConfig} from '../transport25/config.mjs';
import {CONFIG} from '../transport25/fixtures.mjs';

const c=structuredClone(CONFIG);c.bindings[1].cameraKey='42/102/0';export const NETWORK_CONFIG=validateConfig(c);
export const ENDPOINTS=Object.freeze({aircraft:5772,payload:5773});
export function decodeChunkHex(s){if(typeof s!=='string'||s.length>8192||s.length%2||!/^[a-f0-9]*$/i.test(s))throw Error('Bounded TCP chunk hex');return Uint8Array.from(s.match(/../g)||[],x=>parseInt(x,16));}
export function validateCommand(bytes,record,context){
 if(!(bytes instanceof Uint8Array)||bytes.length>280)throw Error('Bounded command bytes');
 const d=new Decoder(),frames=d.push(bytes),f=frames[0];
 if(frames.length!==1||d.buffer.length||d.stats.corrupt||!f||f.id!==76||f.system!==255||f.component!==190)throw Error('Single unsigned COMMAND_LONG only');
 if(JSON.stringify(record.context)!==JSON.stringify(context)||record.rawHex!==hex(bytes))throw Error('Exact reviewed context and bytes');
 const p=f.fields;
 if(p.target_system!==42||![100,101,102,154].includes(p.target_component)||![512,531,532,2000,1000,1001].includes(p.command)||p.confirmation!==0)throw Error('Payload command allowlist; no flight/broadcast');
 if(p.command===512&&![259,280].includes(p.param1)||p.target_component===154&&![512,1000,1001].includes(p.command)||p.target_component!==154&&[1000,1001].includes(p.command))throw Error('Endpoint operation mismatch');
 if(record.targetSystem!==p.target_system||record.targetComponent!==p.target_component||record.command!==p.command)throw Error('Reviewed target mismatch');
 if([531,532].includes(p.command)&&(p.param1!==2||!Number.isFinite(p.param2)||p.param2<0||p.param2>100||p.param3!==0))throw Error('Camera percent/direct device bounds');
 if(p.command===2000&&(p.param1!==0||p.param2!==0||p.param3!==1||!Number.isInteger(p.param4)||p.param4<1))throw Error('Single synthetic direct-camera capture');
 if([1000,1001].includes(p.command)&&![1,2].includes(p.param7))throw Error('Configured manager device only');
 if(p.command===1000&&(!Number.isFinite(p.param1)||!Number.isFinite(p.param2)||p.param1 < -90||p.param1>30||Math.abs(p.param2)>180))throw Error('Gimbal degree bounds');
 if(p.command===1001&&(p.param1!==255||p.param2!==190||p.param3!==0||p.param4!==0))throw Error('Fixture primary authority only');
 if(p.command===512&&p.param1!==(p.target_component===154?280:259))throw Error('Discovery target message mismatch');
 return f;
}
// Harness seam only. Mock-origin state is never relabeled as physical/SITL payload evidence.
export class LoopbackBridge{
 mock=new MockTransport();broker;#sockets=new Map();#decoders=new Map();#epoch=0;#context=null;#rows=[];#bytes=0;#phase='CLOSED';#closed=new Set();#sent=new Set();#apWrites=0;#lastHb=null;#heartbeatPaused=false;#evidenceStop=null;
 constructor(){this.broker=new TransportBroker({transport:this.mock,sessionId:'transport26'});}
 #log(kind,detail={}){if(this.#rows.length>=2048){this.#evidenceStop??={reason:'NETWORK_RECEIPT_BOUND',at:new Date().toISOString()};this.#revoke('payload',this.#epoch,'network-evidence-bound');return false;}this.#rows.push({n:this.#rows.length+1,at:new Date().toISOString(),atMs:performance.now(),epoch:this.#epoch,kind,...structuredClone(detail)});}
 async connect(){if(this.#phase!=='CLOSED')throw Error('Explicit close before reconnect');this.#phase='CONNECTING';const epoch=++this.#epoch;this.#context=await this.broker.connect(NETWORK_CONFIG);this.#closed.clear();this.#sent.clear();this.#lastHb=null;this.#heartbeatPaused=false;
 try{for(const role of ['aircraft','payload']){
  const s=net.createConnection({host:'127.0.0.1',port:ENDPOINTS[role]});s.setNoDelay(true);if(role==='aircraft'){s.write=()=>{this.#apWrites++;throw Error('Aircraft transport is receive-only');};}this.#sockets.set(role,s);const d=new Decoder();this.#decoders.set(role,d);
  s.on('data',chunk=>{try{this.#ingest(role,epoch,chunk);}catch(e){this.#evidenceStop??={reason:e.message,at:new Date().toISOString()};this.#log('RECEIVE_FAILURE',{role,error:e.message});this.#revoke(role,epoch,'receive-bound-or-parse');}});
  s.on('error',e=>{if(epoch!==this.#epoch)return;this.#log('SOCKET_ERROR',{role,error:e.code??e.message});this.#revoke(role,epoch,'error');});s.on('close',()=>this.#revoke(role,epoch,'close'));
  await new Promise((resolve,reject)=>{const timer=setTimeout(()=>{s.destroy();reject(Error('Loopback connect timeout'));},3000);s.once('connect',()=>{clearTimeout(timer);this.#log('SOCKET_CONNECTED',{role,host:s.remoteAddress,port:s.remotePort});resolve();});s.once('error',e=>{clearTimeout(timer);reject(e);});});
 }this.#phase='CONNECTED';return structuredClone(this.#context);}catch(e){this.close();throw e;}}
 #revoke(role,epoch,reason){if(epoch!==this.#epoch||this.#closed.has(role)||this.#phase==='CLOSED')return;this.#closed.add(role);this.#phase='LINK_DOWN_RECONNECT_REQUIRED';this.mock.down('mock-a');for(const s of this.#sockets.values())s.destroy();this.#log('NO_AUTOMATIC_RECONNECT_OR_RESEND',{role,reason});}
 #ingest(role,epoch,chunk){if(epoch!==this.#epoch||this.#closed.has(role)||this.#phase==='CLOSED')return;this.#bytes+=chunk.length;if(this.#bytes>1048576)throw Error('1MiB network evidence bound');
  for(let start=0;start<chunk.length;start+=4096){const part=new Uint8Array(chunk.subarray(start,start+4096));if(!this.#log('TCP_RX',{role,rawHex:hex(part)})&&this.#evidenceStop)return;for(const f of this.#decoders.get(role).push(part)){if(this.#evidenceStop)return;
   if(role==='aircraft'){if(f.id!==0||f.system!==42||f.component!==1){this.#log('AIRCRAFT_OTHER_FRAME_FILTERED',{id:f.id,system:f.system,component:f.component});continue;}this.#lastHb={...f,observedAtMs:performance.now(),origin:'ACTUAL_LOOPBACK_ARDUCOPTER_HEARTBEAT'};if(f.fields.base_mode&128){this.#revoke(role,epoch,'unexpected-armed');throw Error('Dedicated SITL must remain disarmed');}if(this.#heartbeatPaused)continue;
   }else if(f.component===1){this.#log('FIXTURE_CANNOT_IMPERSONATE_AUTOPILOT_COMPONENT');continue;}
   this.mock.deliver(unhex(f.rawHex),{context:this.#context});this.#log('BROKER_DELIVERY',{role,rawHex:f.rawHex,origin:role==='aircraft'?'ACTUAL_SITL_HEARTBEAT':'SYNTHETIC_NETWORK_PAYLOAD'});
  }}
 }
 dispatch(intent){if(this.#phase!=='CONNECTED')throw Error('Explicit current live sockets required');const captured=structuredClone(this.#context);if(JSON.stringify(intent.context)!==JSON.stringify(captured))throw Error('Explicit reviewed current intent context');const r=this.broker.request(structuredClone(intent));if(r.override)throw Error('Mock admission refused or uncertain');const bytes=unhex(r.protocol.rawCommandHex),f=new Decoder().push(bytes)[0],p=f.fields;
 const review={context:captured,rawHex:hex(bytes),targetSystem:p.target_system,targetComponent:p.target_component,command:p.command};validateCommand(bytes,review,this.#context);
 if(this.#sent.has(r.id))throw Error('No repeated transaction dispatch');this.#sent.add(r.id);const s=this.#sockets.get('payload');if(!s||s.destroyed||s.writableLength>4096){this.#revoke('payload',this.#epoch,'admission-refused');throw Error('SEND_UNCERTAIN_NO_RETRY');}
 this.#log('TCP_TX_ATTEMPT',{role:'payload',transactionId:r.id,bindingId:r.bindingId,...review,sha256:createHash('sha256').update(bytes).digest('hex')});
 try{s.write(bytes,e=>{if(e){this.#log('TCP_WRITE_UNCERTAIN',{transactionId:r.id,error:e.code??e.message});this.#revoke('payload',this.#epoch,'write-error');}else this.#log('TCP_LOCAL_WRITE_CALLBACK_NOT_PEER_ACK',{transactionId:r.id});});}catch(e){this.#revoke('payload',this.#epoch,'write-throw');throw e;}return r;
 }
 pauseAircraftDelivery(){this.#heartbeatPaused=true;this.#log('FAULT_AIRCRAFT_HEARTBEAT_DELIVERY_SILENT');}
 cut(role){if(!ENDPOINTS[role])throw Error('Fixed endpoint role');this.#sockets.get(role)?.destroy();}
 snapshot(){const broker=this.broker.snapshot();return{format:'aeris-transport26-network-review',version:1,phase:this.#phase,epoch:this.#epoch,context:structuredClone(this.#context),aircraft:this.#lastHb,aircraftWrites:this.#apWrites,automaticRetries:0,automaticReconnects:0,networkBytes:this.#bytes,networkEvidenceComplete:this.#evidenceStop===null,evidenceStop:structuredClone(this.#evidenceStop),network:structuredClone(this.#rows),broker,payloadResponseOrigin:'SYNTHETIC_TCP_RESPONDER_NOT_ARDUPILOT_PAYLOAD',physicalMedia:[],physicalMediaVerified:false,causalExecutionProven:false};}
 close(){this.#phase='CLOSED';++this.#epoch;for(const s of this.#sockets.values())s.destroy();this.#sockets.clear();this.broker.disconnect();this.#log('EXPLICIT_CLOSE_NO_RESUME');}
}
