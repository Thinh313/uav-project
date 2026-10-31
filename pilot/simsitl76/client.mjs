import net from 'node:net';
import {open,statfs} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {Observations42} from '../flightsafety42/observe.mjs';
import {manifest,packet,PORT,PROFILE,sensorGuard,rays} from './contract.mjs';
export async function connect76(m,path){
 manifest(m);const obs=new Observations42({scope:'OWNED_REAL_SITL_FLIGHT_TEST_ONLY',binarySha256:m.binarySha256,containerId:m.containerId,pid:m.pid,startedAt:m.startedAt,system:42,component:1,session:m.session});
 const file=await open(path,'wx'),origin=process.hrtime.bigint(),now=()=>Number((process.hrtime.bigint()-origin)/1000000n);
 let tail=Promise.resolve(),tx=Promise.resolve(),socket,failure=null,closed=false,n=0,prev='0'.repeat(64),bytes=0,queue=0,seq=0,rc=null,sensors=true,timer=null,busy=false,lastHB=-1000,lastSensor=-100,lastRC=-100,ended=false;
 function fail(e){failure??=e;obs.loss(e.message);if(timer)clearInterval(timer);socket?.destroy();}
 function log(v){if(++queue>64){fail(Error('JOURNAL_QUEUE'));return Promise.reject(failure);}const job=tail.then(async()=>{if(failure)throw failure;const fs=await statfs('.');if(fs.bavail*fs.bsize<20.5*2**30)throw Error('DISK_RESERVE_LOST');const p={n:++n,prev,utc:new Date().toISOString(),...v},sha256=createHash('sha256').update(JSON.stringify(p)).digest('hex'),b=Buffer.from(JSON.stringify({...p,sha256})+'\n');bytes+=b.length;if(bytes>32*2**20||n>30000)throw Error('RAW_QUOTA');let k=0;while(k<b.length){const w=await file.write(b,k,b.length-k);if(!w.bytesWritten)throw Error('ZERO_WRITE');k+=w.bytesWritten;}await file.sync();prev=sha256;});tail=job.catch(fail).finally(()=>queue--);return job;}
 socket=net.createConnection({host:'127.0.0.1',port:PORT});socket.setNoDelay(true);socket.on('error',fail);
 await new Promise((resolve,reject)=>{socket.once('connect',resolve);socket.once('error',reject);});
 await log({kind:'CONNECT',manifest:m,originHrNs:origin.toString(),at:now()});
 socket.on('data',b=>{socket.pause();const at=now(),raw=new Uint8Array(b);log({kind:'RX',rawHex:Buffer.from(raw).toString('hex'),at}).then(()=>{obs.receive(raw,at,now());if(!failure&&!closed)socket.resume();}).catch(fail);});
 socket.on('close',()=>{closed=true;if(timer)clearInterval(timer);obs.loss('SOCKET_CLOSED');});
 async function emitBatch(specs,reason,metadata={}){const raws=specs.map(([id,p])=>packet(id,p,seq++%256));const raw=Buffer.concat(raws.map(x=>Buffer.from(x)));const job=tx.then(async()=>{if(failure)throw failure;if(closed)throw Error('CLOSED');if(specs.some(([id,p])=>id!==0&&!(id===76&&p.command===512&&p.param1===148))&&!obs.fresh(now()))throw Error('FRESH_FIRMWARE_HEARTBEAT_REQUIRED');await log({kind:'TX_INTENT',rawHex:raw.toString('hex'),reason,metadata,at:now()});await new Promise((resolve,reject)=>socket.write(raw,e=>e?reject(e):resolve()));await log({kind:'TX_WRITE_RETURN',rawHex:raw.toString('hex'),reason,at:now()});});tx=job.catch(fail);return job;}
 const emit=(id,p,reason)=>emitBatch([[id,p]],reason);
 const heartbeat=()=>emit(0,{type:6,autopilot:8,custom_mode:0,base_mode:0,system_status:4},'HEARTBEAT');
 async function tick(){if(busy||closed||failure)return;busy=true;try{let t=now();if(t-lastHB>=1000){lastHB=t;await heartbeat();}if(!obs.fresh(now()))return;
  const a=obs.latest[30],p=obs.latest[32];t=now();
  if(sensors&&t-lastSensor>=100&&a&&p&&t-a.at<=200&&t-p.at<=200){lastSensor=t;const s={target:m.target,session:m.session,boot:m.boot,frame:'BODY_FRD_METRES',clock:'HOST_MONOTONIC_MS',at:t,bootMs:p.fields.time_boot_ms,ranges:rays(p.fields,a.fields)};sensorGuard(s,m,now());await emitBatch(s.ranges.map((v,i)=>[132,{time_boot_ms:s.bootMs,min_distance:20,max_distance:2000,current_distance:Math.min(2001,Math.round(v*100)),type:0,id:i,orientation:i,covariance:255}]),'VIRTUAL_RAYS',s);}
  if(rc&&now()-lastRC>=100){lastRC=now();await emit(70,{target_system:42,target_component:1,...Object.fromEntries(rc.map((v,i)=>['chan'+(i+1)+'_raw',v]))},'HELD_RC_INPUT');}
 }catch(e){fail(e);}finally{busy=false;}}
 const wait=async(predicate,ms=10000)=>{const deadline=now()+ms;while(now()<deadline){await tail;if(failure)throw failure;if(predicate(obs))return;await new Promise(r=>setTimeout(r,25));}throw Error('WAIT_TIMEOUT:'+predicate.toString());};
 const mark=(name,data={})=>log({kind:'MARK',name,data,at:now()});
 async function command(command,params={},reason='SCOPED_COMMAND'){const start=obs.frames.length;await emit(76,{target_system:42,target_component:1,command,...params},reason);await wait(o=>o.frames.slice(start).some(f=>f.id===77&&f.label==='ACCEPTED'&&f.fields.command===command&&f.fields.target_system===255&&f.fields.target_component===190),4000);const ack=obs.frames.slice(start).find(f=>f.id===77&&f.label==='ACCEPTED'&&f.fields.command===command);if(ack.fields.result!==0)throw Error('COMMAND_REJECTED:'+command+':'+ack.fields.result);return ack;}
 async function read(name){if(!PROFILE[name])throw Error('NAMED_PROFILE');const start=obs.frames.length;await emit(20,{target_system:42,target_component:1,param_id:name,param_index:-1},'READ:'+name);await wait(o=>o.frames.slice(start).some(f=>f.id===22&&f.label==='ACCEPTED'&&f.fields.param_id===name),4000);const v=obs.parameters[name];if(v.type!==PROFILE[name][0]||!PROFILE[name][1].includes(v.value))throw Error('TYPED_VALUE:'+name+':'+JSON.stringify(v));return v;}
 async function setAvoid(value){const start=obs.frames.length;await emit(23,{target_system:42,target_component:1,param_id:'AVOID_ENABLE',param_type:2,param_value:value},'SET_AVOID:'+value);await wait(o=>o.frames.slice(start).some(f=>f.id===22&&f.label==='ACCEPTED'&&f.fields.param_id==='AVOID_ENABLE'&&f.fields.param_value===value),4000);const v=await read('AVOID_ENABLE');if(v.value!==value)throw Error('SET_READBACK');}
 function axes(pitch=1500,yaw=1500){if(!obs.fresh(now())||obs.latest[0].fields.custom_mode!==5||!(obs.latest[0].fields.base_mode&128))throw Error('LOITER_AUTHORITY_REQUIRED');rc=[1500,pitch,1500,yaw,65535,65535,65535,65535];packet(70,{target_system:42,target_component:1,...Object.fromEntries(rc.map((v,i)=>['chan'+(i+1)+'_raw',v]))});}
 async function release(){rc=null;await emit(70,{target_system:42,target_component:1,chan1_raw:0,chan2_raw:0,chan3_raw:0,chan4_raw:0,chan5_raw:65535,chan6_raw:65535,chan7_raw:65535,chan8_raw:65535},'EXPLICIT_RC_RELEASE');}
 async function close(){if(ended)return;ended=true;rc=null;sensors=false;if(timer)clearInterval(timer);await tx;socket.destroy();await new Promise(r=>setTimeout(r,30));await tail;await file.sync();await file.close();if(failure)throw failure;}
 await heartbeat();timer=setInterval(()=>tick(),50);
 return {obs,now,wait,mark,command,read,setAvoid,axes,release,emit,close,sensors:v=>{sensors=v;},alive:()=>!failure&&!closed};
}
