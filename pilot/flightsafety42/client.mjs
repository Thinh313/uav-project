import net from 'node:net';
import {open,statfs} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {hex} from '../apstream40/wire.mjs';
import {Observations42} from './observe.mjs';
import {assertManifest,packet,validateTX,PROFILE,target} from './contract.mjs';
const LEASES=new WeakMap();
export function liveLease(p,t){const l=LEASES.get(p);return !!l&&l.obs.fresh(t)&&JSON.stringify(p)===l.canonical;}
export async function connect42(manifest,path){
 assertManifest(manifest);const obs=new Observations42(manifest),file=await open(path,'wx'),origin=process.hrtime.bigint(),now=()=>Number((process.hrtime.bigint()-origin)/1000000n);
 let tail=Promise.resolve(),failure=null,n=0,bytes=0,prev='0'.repeat(64),pending=0,pendingBytes=0,closed=false,ended=false,seq=0,hbEnabled=true,hbTimer=null,txTail=Promise.resolve(),socket;
 function fail(e){failure??=e;obs.loss(e.message);hbEnabled=false;if(hbTimer)clearInterval(hbTimer);socket?.destroy();}
 function log(data){const copy=structuredClone(data),sz=Buffer.byteLength(JSON.stringify(copy));if(++pending>64||(pendingBytes+=sz)>1024*1024){const e=Error('JOURNAL_QUEUE_BOUND');fail(e);return Promise.reject(e);}
  const job=tail.then(async()=>{if(failure)throw failure;const fs=await statfs('.');if(fs.bavail*fs.bsize<20*2**30+65536)throw Error('DISK_FLOOR');const payload={n:++n,utc:new Date().toISOString(),prev,...copy};const sha256=createHash('sha256').update(JSON.stringify(payload)).digest('hex'),buf=Buffer.from(JSON.stringify({...payload,sha256})+'\n');if((bytes+=buf.length)>20*2**20||n>30000)throw Error('RAW_CAPTURE_BOUND');let k=0;while(k<buf.length){const r=await file.write(buf,k,buf.length-k);if(!r.bytesWritten)throw Error('ZERO_WRITE');k+=r.bytesWritten;}await file.sync();prev=sha256;});
  tail=job.catch(e=>{fail(e);}).finally(()=>{pending--;pendingBytes-=sz;});return job;
 }
 socket=net.createConnection({host:'127.0.0.1',port:5797});socket.setNoDelay(true);socket.on('error',e=>fail(e));
 await new Promise((resolve,reject)=>{socket.once('connect',resolve);socket.once('error',reject);});await log({kind:'CONNECT',manifest,clockOriginHrNs:origin.toString(),hostMs:now()});
 socket.on('data',b=>{socket.pause();const raw=new Uint8Array(b),at=now();log({kind:'RX',rawHex:hex(raw),hostMs:at}).then(()=>{obs.receive(raw,at,now());if(!closed&&!failure)socket.resume();}).catch(fail);});
 socket.on('close',()=>{closed=true;obs.loss('SOCKET_CLOSED');if(hbTimer)clearInterval(hbTimer);if(!failure)log({kind:'SOCKET_CLOSE',hostMs:now()}).catch(fail);});
 const mark=async(name,details={})=>{await log({kind:'MARK',name,details,hostMs:now()});console.log(JSON.stringify({mark:name,hostMs:now()}));};
 function send(raw,reason){const f=validateTX(raw);const work=txTail.then(async()=>{if(failure)throw failure;if(closed||obs.dead)throw Error('NO_TX_AFTER_LOSS');if(f.id!==0&&!(f.id===76&&f.fields.command===512&&f.fields.param1===148)&&!obs.fresh(now()))throw Error('FRESH_VERSION_HEARTBEAT_REQUIRED');await log({kind:'TX_INTENT',rawHex:hex(raw),reason,hostMs:now()});await new Promise((resolve,reject)=>socket.write(raw,e=>e?reject(e):resolve()));await log({kind:'TX_WRITE_RETURN',rawHex:hex(raw),reason,hostMs:now()});});txTail=work.catch(fail);return work;}
 const emit=(id,p,reason)=>send(packet(id,p,seq++%256),reason);
 const heartbeat=()=>emit(0,{type:6,autopilot:8,base_mode:0,custom_mode:0,system_status:4},'GCS_HEARTBEAT');
 const wait=async(predicate,ms=10000)=>{const stop=now()+ms;while(now()<stop){await tail;if(failure)throw failure;if(predicate(obs))return;await new Promise(r=>setTimeout(r,25));}throw Error('WAIT_TIMEOUT:'+predicate.toString());};
 const command=async(cmd,params={},label='SCOPED_TEST_COMMAND')=>{const at=now(),index=obs.frames.length;await emit(76,{...target,command:cmd,...params},label);await wait(o=>o.frames.slice(index).some(f=>f.label==='ACCEPTED'&&f.id===77&&f.at>=at&&f.fields.command===cmd&&f.fields.target_system===255&&f.fields.target_component===190),3000);return obs.frames.slice(index).find(f=>f.label==='ACCEPTED'&&f.id===77&&f.at>=at&&f.fields.command===cmd&&f.fields.target_system===255&&f.fields.target_component===190);};
 const read=async(name)=>{if(!PROFILE[name])throw Error('PARAMETER_NAME');const at=now(),index=obs.frames.length;await emit(20,{...target,param_id:name,param_index:-1},'READ:'+name);await wait(o=>o.frames.slice(index).some(f=>f.label==='ACCEPTED'&&f.id===22&&f.fields.param_id===name&&f.at>=at),3000);const p=obs.parameters[name];if(p.type!==PROFILE[name][0]||!p.count||p.index!==65535&&p.index>=p.count||!Number.isFinite(p.value))throw Error('TYPED_READBACK:'+name);return p;};
 const set=async(name,value)=>{const at=now(),index=obs.frames.length;await emit(23,{...target,param_id:name,param_type:PROFILE[name]?.[0],param_value:value},'SET_SIMULATOR_ONLY:'+name);await wait(o=>o.frames.slice(index).some(f=>f.label==='ACCEPTED'&&f.id===22&&f.fields.param_id===name&&f.at>=at&&f.fields.param_value===value),3000);const p=await read(name);if(p.value!==value)throw Error('SET_NOT_VERIFIED');return p;};
 const lease=()=>{if(!obs.fresh(now()))throw Error('NO_FRESH_LOCAL_LEASE');const p={format:'owned-simulation42-only',manifest:structuredClone(manifest),restorable:false,physicalAuthority:false};LEASES.set(p,{obs,canonical:JSON.stringify(p)});return p;};
 const close=async()=>{if(ended)return;ended=true;hbEnabled=false;if(hbTimer)clearInterval(hbTimer);await txTail;socket.destroy();await new Promise(r=>setTimeout(r,30));await tail;await file.sync();await file.close();if(failure)throw failure;};
 const enableHB=async on=>{hbEnabled=on;await txTail;await mark(on?'GCS_HEARTBEAT_RESTORED':'GCS_HEARTBEAT_BLACKOUT');if(on)await heartbeat();};
 await heartbeat();hbTimer=setInterval(()=>{if(hbEnabled&&!closed&&!failure)heartbeat().catch(fail);},1000);
 return {obs,now,wait,mark,emit,command,read,set,lease,close,enableHB,flush:()=>tail,alive:()=>!failure&&!closed};
}
