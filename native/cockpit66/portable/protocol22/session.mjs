import {Decoder,encode,hex} from './wire.mjs';
const clone=x=>structuredClone(x),finite=x=>typeof x==='number'&&Number.isFinite(x),uint=(v,lo=1,hi=255)=>Number.isInteger(v)&&v>=lo&&v<=hi;
const end=new Set(['REJECTED','TIMED_OUT_UNCERTAIN','INVALIDATED','OBSERVATION_CONSISTENT_UNATTRIBUTED','DISCOVERY_INFORMATION_OBSERVED']);
const endpoint=m=>`${m.system}/${m.component}`;
export const POLICY=Object.freeze({heartbeatMs:3000,authorityMs:1500,commandMs:2000,maxComponents:32,maxCameras:8,maxGimbals:8,history:256});
export class ProtocolSession {
 #now;#last=-1;#decoder=new Decoder();#n=0;#epoch=1;#session;#components=new Map();#cameras=new Map();#gimbals=new Map();#transactions=[];#events=[];#quarantine=new Set();#dropped=0;
 constructor({sessionId='corpus-01',now=()=>performance.now()}={}){if(!/^[A-Za-z0-9_-]{1,64}$/.test(sessionId))throw Error('Session ID');this.#session=sessionId;this.#now=now;}
 #time(){const t=this.#now();if(!finite(t)||t<0||t<this.#last)throw Error('Monotonic clock');this.#last=t;return t;}
 context(){return {sessionId:this.#session,epoch:this.#epoch};}
 #event(type,detail={}){this.#events.push({n:++this.#n,atMs:this.#time(),...this.context(),type,...clone(detail)});if(this.#events.length>POLICY.history){this.#events.shift();this.#dropped++;}}
 #invalidate(key,reason){const c=this.#components.get(key);if(c)c.ready=false;const affected=[];for(const p of this.#cameras.values())if(p.endpoint===key)p.valid=false;for(const g of this.#gimbals.values())if(g.endpoint===key||g.system===c?.system&&g.device===c?.component&&g.device>6){g.valid=false;g.authority=null;affected.push(g.key);}for(const t of this.#transactions)if((t.endpoint===key||affected.includes(t.targetKey))&&!end.has(t.state)){t.state='INVALIDATED';this.#quarantine.add(t.ackKey);}this.#event('COMPONENT_INVALIDATED',{endpoint:key,reason});}
 reconnect(){for(const key of this.#components.keys())this.#invalidate(key,'explicit new transport generation');this.#epoch++;this.#components.clear();this.#cameras.clear();this.#gimbals.clear();this.#decoder=new Decoder();this.#quarantine.clear();this.#event('RECONNECTED_NO_RESUME');}
 tick(){const now=this.#time();for(const [key,c]of this.#components)if(c.ready&&now-c.heartbeatAt>POLICY.heartbeatMs)this.#invalidate(key,'heartbeat expired');for(const t of this.#transactions)if(!end.has(t.state)&&now>=t.deadlineMs){t.state='TIMED_OUT_UNCERTAIN';this.#quarantine.add(t.ackKey);this.#event('TIMEOUT_NO_RETRY',{transactionId:t.id});}}
 ingest(bytes,context=this.context()){
  this.tick();if(context.sessionId!==this.#session||context.epoch!==this.#epoch){this.#event('FOREIGN_CONTEXT_IGNORED');return 0;}
  let messages;try{messages=this.#decoder.push(bytes);}catch(e){this.#event('DECODE_BOUND_REFUSED');throw e;}
  for(const m of messages)this.#message(m);return messages.length;
 }
 #message(m){
  const now=this.#time(),key=endpoint(m);if(!uint(m.system)||!uint(m.component)){this.#event('IDENTITY_IGNORED');return;}
  let c=this.#components.get(key);
  if(m.id===0){const role=m.fields.type===30?'camera':m.fields.type===26?'gimbal':m.component===1&&m.fields.autopilot!==8&&[1,2,3,4,13,14,15].includes(m.fields.type)?'autopilot':null;if(!role){this.#event('UNSUPPORTED_COMPONENT_TYPE');return;}
   if(!c){if(this.#components.size>=POLICY.maxComponents)throw Error('Component capacity');c={key,system:m.system,component:m.component,type:m.fields.type,role,generation:++this.#n,ready:true,heartbeatAt:now,boot:null,seq:null};this.#components.set(key,c);}
   else if(!c.ready){c.generation=++this.#n;c.ready=true;c.boot=null;c.seq=null;}
   if(c.type!==m.fields.type){this.#invalidate(key,'component type changed');return;}
  }
  if(!c?.ready){this.#event('NO_FRESH_HEARTBEAT',{endpoint:key,id:m.id});return;}
  const boot=m.fields.time_boot_ms;
  if(boot!==undefined&&c.boot!==null&&boot<c.boot&&!(c.boot>0xf0000000&&boot<0x0fffffff)){this.#invalidate(key,'boot regression or reordered old boot');return;}
  if(c.seq!==null){const delta=(m.seq-c.seq+256)%256;if(delta===0||delta>127){this.#event('REPLAY_OR_REORDER_IGNORED',{endpoint:key,seq:m.seq});return;}}
  c.seq=m.seq;if(boot!==undefined)c.boot=boot;if(m.id===0)c.heartbeatAt=now;
  this.#event('FRAME_ACCEPTED',{endpoint:key,id:m.id,seq:m.seq,rawHex:m.rawHex});
  if(m.id===0)return;
  if(m.id===77){this.#ack(m,c);return;}
  if(m.id===280){const f=m.fields;if(!uint(f.gimbal_device_id)||![f.pitch_min,f.pitch_max,f.yaw_min,f.yaw_max].every(finite)||f.pitch_min>=f.pitch_max||f.yaw_min>=f.yaw_max){this.#event('GIMBAL_INFORMATION_REFUSED');return;}
   const k=key+'/'+f.gimbal_device_id;if(!this.#gimbals.has(k)&&this.#gimbals.size>=POLICY.maxGimbals)throw Error('Gimbal capacity');const g={key:k,endpoint:key,system:m.system,manager:m.component,device:f.gimbal_device_id,generation:c.generation,valid:true,capabilities:f.cap_flags,pitchRad:[f.pitch_min,f.pitch_max],yawRad:[f.yaw_min,f.yaw_max],authority:null,attitude:null,failure:0,origin:m.origin};this.#gimbals.set(k,g);this.#event('GIMBAL_DISCOVERED',{key:k});this.#discoveryObserved(m,c);return;
  }
  if(m.id===281){const g=this.#gimbals.get(key+'/'+m.fields.gimbal_device_id);if(!g?.valid||g.generation!==c.generation)return;g.authority={primary:[m.fields.primary_control_sysid,m.fields.primary_control_compid],secondary:[m.fields.secondary_control_sysid,m.fields.secondary_control_compid],atMs:now};for(const t of this.#transactions)if(t.targetKey===g.key&&t.operation==='gimbal'&&!end.has(t.state)&&!this.#hasAuthority(g)){t.state='INVALIDATED';this.#quarantine.add(t.ackKey);}this.#observe(g.key,m);return;}
  if(m.id===285){const f=m.fields;if(f.target_system&&f.target_system!==255||f.target_component&&f.target_component!==190)return;let candidates=[...this.#gimbals.values()].filter(g=>g.valid&&g.system===m.system&&(m.component===g.manager&&f.gimbal_device_id===g.device||m.component===g.device&&(f.gimbal_device_id===0||f.gimbal_device_id===g.device)));
   if(candidates.length===1){candidates[0].failure=f.failure_flags;if(f.failure_flags)for(const t of this.#transactions)if(t.targetKey===candidates[0].key&&!end.has(t.state)){t.state='INVALIDATED';this.#quarantine.add(t.ackKey);}}
   if(candidates.length!==1||f.failure_flags||!(f.flags&32)||f.flags&64||!Array.isArray(f.q)||!f.q.every(finite)||Math.abs(f.q.reduce((s,n)=>s+n*n,0)-1)>.01){if(candidates.length===1)candidates[0].attitude=null;this.#event('ATTITUDE_REFUSED',{reason:'unknown route/frame, failure or quaternion'});return;}
   const g=candidates[0],[w,x,y,z]=f.q,pitch=Math.asin(Math.max(-1,Math.min(1,2*(w*y-z*x)))),yaw=Math.atan2(2*(w*z+x*y),1-2*(y*y+z*z));g.attitude={pitchRad:pitch,yawRad:yaw,atMs:now,flags:f.flags,bootMs:f.time_boot_ms};this.#observe(g.key,m);return;
  }
  if(![259,260,262,263,269,270].includes(m.id))return;
  const f=m.fields,device=m.id===263?f.camera_id:f.camera_device_id??0;
  if(c.role==='camera'&&device!==0||c.role==='autopilot'&&!uint(device,1,6)||!['autopilot','camera'].includes(c.role)){this.#event('CAMERA_ID_IGNORED',{endpoint:key,device});return;}
  const k=key+'/'+device;let p=this.#cameras.get(k);
  if(m.id===259){if(!this.#cameras.has(k)&&this.#cameras.size>=POLICY.maxCameras)throw Error('Camera capacity');p={key:k,endpoint:key,system:m.system,component:m.component,device,generation:c.generation,valid:true,flags:f.flags,capabilities:{capture:!!(f.flags&2),zoom:!!(f.flags&64),focus:!!(f.flags&128),stream:!!(f.flags&256)},gimbalDevice:f.gimbal_device_id||null,definitionURI:f.cam_definition_uri||null,settings:null,lastImage:null,streams:{},captureStatus:null,origin:m.origin};this.#cameras.set(k,p);this.#event('CAMERA_DISCOVERED',{key:k,definitionFetched:false});this.#discoveryObserved(m,c);}
  if(!p?.valid||p.generation!==c.generation){this.#event('CAMERA_INFORMATION_REQUIRED');return;}
  if(m.id===260)p.settings={zoomPercent:m.present.includes('zoomLevel')&&finite(f.zoomLevel)?f.zoomLevel:null,focusPercent:m.present.includes('focusLevel')&&finite(f.focusLevel)?f.focusLevel:null,atMs:now,bootMs:f.time_boot_ms};
  if(m.id===263&&f.capture_result===1){if(p.lastImage&&f.image_index<=p.lastImage.index){this.#event('OLD_IMAGE_INDEX_IGNORED');return;}p.lastImage={index:f.image_index,utcUs:f.time_utc,atMs:now,bootMs:f.time_boot_ms,url:f.file_url,physicalMediaVerified:false,origin:m.origin};}
  if(m.id===262)p.captureStatus={imageCount:m.present.includes('image_count')?f.image_count:null,videoStatus:f.video_status,atMs:now};
  if([269,270].includes(m.id)&&uint(f.stream_id,1,255)){const prev=p.streams[f.stream_id]||{};p.streams[f.stream_id]={...prev,...(m.id===269?{name:f.name,uri:f.uri}:{}),reportedRunning:!!(f.flags&1),atMs:now,framesObserved:false};}
  this.#observe(k,m);
 }
 #hasAuthority(g){return g.authority?.primary[0]===255&&g.authority.primary[1]===190&&this.#time()-g.authority.atMs<=POLICY.authorityMs;}
 #discoveryObserved(m,c){for(const t of this.#transactions)if(t.operation==='discovery'&&t.state==='ACK_ACCEPTED'&&t.endpoint===c.key&&t.expectedMessage===m.id&&t.generation===c.generation&&this.#time()>t.requestedAtMs){t.state='DISCOVERY_INFORMATION_OBSERVED';t.observation={rawHex:m.rawHex,id:m.id,allDevicesEnumerated:false};}}
 requestDiscovery({system,component,legacy=false,messageId=259}){this.tick();const c=this.#components.get(`${system}/${component}`);if(!c?.ready)throw Error('Heartbeat required');if(![259,280].includes(messageId)||legacy&&messageId!==259)throw Error('Selected discovery message only');return this.#request({endpoint:c.key,targetKey:c.key,operation:'discovery',command:legacy?521:512,params:legacy?{param1:1}:{param1:messageId},expectedMessage:messageId,device:0,generation:c.generation});}
 requestCamera(key,operation,value){this.tick();const p=this.#cameras.get(key),c=p&&this.#components.get(p.endpoint);if(!p?.valid||!c?.ready||!p.capabilities[operation])throw Error('Fresh camera capability required');if(!['zoom','focus','capture'].includes(operation))throw Error('Camera operation unsupported');
  if(operation!=='capture'&&(!finite(value)||value<0||value>100))throw Error('Camera range uses0..100 percent, not zoom factor');
  if(operation==='capture'&&(!p.lastImage||this.#time()-p.lastImage.atMs>POLICY.heartbeatMs||BigInt(p.lastImage.utcUs)===0n))throw Error('Fresh capture index/time baseline required');
  const command=operation==='zoom'?531:operation==='focus'?532:2000,params=operation==='capture'?{param1:p.device,param2:0,param3:1,param4:++this.#n,param7:NaN}:{param1:2,param2:value,param3:p.device,param4:NaN};
  return this.#request({endpoint:p.endpoint,targetKey:key,operation,command,params,value,device:p.device,generation:p.generation,baseline:clone(p.lastImage),baselineSettings:clone(p.settings)});
 }
 requestGimbal(key,{pitchDeg,yawDeg}){this.tick();const g=this.#gimbals.get(key),c=g&&this.#components.get(g.endpoint);if(!g?.valid||g.failure||!c?.ready||!this.#hasAuthority(g)||(g.capabilities&288)!==288)throw Error('Fresh gimbal axes/primary authority required');if(![pitchDeg,yawDeg].every(finite)||pitchDeg*Math.PI/180<g.pitchRad[0]||pitchDeg*Math.PI/180>g.pitchRad[1]||yawDeg*Math.PI/180<g.yawRad[0]||yawDeg*Math.PI/180>g.yawRad[1])throw Error('Gimbal limits');
  return this.#request({endpoint:g.endpoint,targetKey:key,operation:'gimbal',command:1000,params:{param1:pitchDeg,param2:yawDeg,param3:NaN,param4:NaN,param5:0,param7:g.device},value:{pitchDeg,yawDeg},device:0,generation:g.generation});}
 requestAuthority(key){this.tick();const g=this.#gimbals.get(key);if(!g?.valid)throw Error('Manager discovery required');return this.#request({endpoint:g.endpoint,targetKey:key,operation:'authority',command:1001,params:{param1:255,param2:190,param3:0,param4:0,param7:g.device},device:0,generation:g.generation});}
 #request(spec){this.tick();const ackKey=spec.endpoint+'/'+spec.command;if(this.#quarantine.has(ackKey))throw Error('Ambiguous ACK key quarantined; explicit new generation required');if(this.#transactions.some(t=>t.ackKey===ackKey&&!end.has(t.state)))throw Error('ACK key already pending');if(this.#transactions.length===POLICY.history){const i=this.#transactions.findIndex(t=>end.has(t.state));if(i<0)throw Error('Transaction capacity');this.#transactions.splice(i,1);this.#dropped++;}
  const [system,component]=spec.endpoint.split('/').map(Number),n=this.#time(),t={...clone(spec),id:'tx-'+(++this.#n),...this.context(),ackKey,state:'REQUESTED',requestedAtMs:n,deadlineMs:n+POLICY.commandMs,ack:null,observation:null,physicalMediaVerified:false,causalExecutionProven:false};t.rawCommandHex=hex(encode(76,{target_system:system,target_component:component,command:spec.command,confirmation:0,...spec.params},{seq:this.#n%256}));this.#transactions.push(t);this.#event('REQUEST_QUEUED_OFFLINE',{id:t.id,rawCommandHex:t.rawCommandHex});return clone(t);}
 #ack(m,c){const f=m.fields;if(f.target_system&&f.target_system!==255||f.target_component&&f.target_component!==190){this.#event('ACK_OTHER_RECIPIENT');return;}const t=this.#transactions.find(t=>t.ackKey===endpoint(m)+'/'+f.command&&!end.has(t.state));if(!t||t.generation!==c.generation||t.device>0&&(!m.present.includes('result_param2')||f.result_param2!==t.device)){this.#event('ACK_UNMATCHED_OR_PROXY_UNKNOWN');return;}
  if(![0,1,2,3,4,5,6].includes(f.result)){this.#event('ACK_RESULT_UNKNOWN');return;}t.ack={result:f.result,atMs:this.#time(),recipientKnown:!!(f.target_system&&f.target_component),causalityProven:false};
  if(f.result===0){t.state='ACK_ACCEPTED';this.#event('ACK_ACCEPTED_NOT_EXECUTION',{id:t.id});}
  else if(f.result===5){t.state='ACK_IN_PROGRESS';this.#event('ACK_IN_PROGRESS',{id:t.id,deadlineExtended:false});}
  else{t.state='REJECTED';this.#event('ACK_REJECTED',{id:t.id});}
 }
 #observe(key,m){for(const t of this.#transactions){if(end.has(t.state)||t.state!=='ACK_ACCEPTED'||t.targetKey!==key||this.#time()<=t.requestedAtMs)continue;let match=false;const p=this.#cameras.get(key),g=this.#gimbals.get(key);
   if(t.operation==='zoom'&&m.id===260&&p?.settings?.zoomPercent!==null)match=Math.abs(p.settings.zoomPercent-t.value)<.1;
   if(t.operation==='focus'&&m.id===260&&p?.settings?.focusPercent!==null)match=Math.abs(p.settings.focusPercent-t.value)<.1;
   if(t.operation==='capture'&&m.id===263&&p?.lastImage&&p.lastImage.atMs>t.requestedAtMs)match=p.lastImage.index>t.baseline.index&&p.lastImage.bootMs>t.baseline.bootMs&&BigInt(p.lastImage.utcUs)>BigInt(t.baseline.utcUs);
   if(t.operation==='gimbal'&&m.id===285&&g?.attitude&&this.#hasAuthority(g))match=Math.abs(g.attitude.pitchRad*180/Math.PI-t.value.pitchDeg)<.5&&Math.abs(g.attitude.yawRad*180/Math.PI-t.value.yawDeg)<.5;
   if(t.operation==='authority'&&m.id===281&&g)match=this.#hasAuthority(g);
   if(match){t.state='OBSERVATION_CONSISTENT_UNATTRIBUTED';t.observation={id:m.id,atMs:this.#time(),rawHex:m.rawHex,origin:m.origin,causalExecutionProven:false};this.#event('OBSERVATION_CONSISTENT_NOT_CAUSAL',{id:t.id});}
  }}
 snapshot(){this.tick();return {format:'aeris-protocol22-review',version:1,...this.context(),origin:'SYNTHETIC_PROTOCOL_CORPUS',scope:'Offline protocol consistency, not aircraft execution or physical media',components:clone([...this.#components.values()]),cameras:clone([...this.#cameras.values()]),gimbals:clone([...this.#gimbals.values()]),transactions:clone(this.#transactions),events:clone(this.#events),decoderStats:clone(this.#decoder.stats),quarantined:[...this.#quarantine],historyComplete:this.#dropped===0,dropped:this.#dropped,physicalMedia:[],physicalMediaVerified:false};}
}
