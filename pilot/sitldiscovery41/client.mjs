import net from 'node:net';
import {open,statfs} from 'node:fs/promises';
import {hex,unhex,FullFramer} from '../apstream40/wire.mjs';
import {Observer41,NAMES} from './observer.mjs';
/** Only loopback5794, source-bound readonly packet whitelist, bounded fsynced raw capture. */
export async function connect41(manifest,path){
 const file=await open(path,'wx'),observer=new Observer41(manifest),origin=process.hrtime.bigint();let bytes=0,rows=0,chain=Promise.resolve(),error=null,closed=false;
 const now=()=>Number((process.hrtime.bigint()-origin)/1000000n);
 const persist=async data=>{const s=await statfs('.');if(s.bavail*s.bsize<20*2**30)throw Error('DISK_FLOOR');const line=JSON.stringify({n:++rows,utc:new Date().toISOString(),...data})+'\n';bytes+=Buffer.byteLength(line);if(bytes>8*2**20)throw Error('CAPTURE_BOUND');await file.write(line);await file.sync();};
 const socket=net.createConnection({host:'127.0.0.1',port:5794});socket.on('error',e=>{error=e;observer.loss('SOCKET_ERROR:'+e.code);});
 await new Promise((resolve,reject)=>{socket.once('connect',resolve);socket.once('error',reject);});await persist({kind:'CONNECT',context:manifest,clockOriginHrNs:origin.toString(),hostMs:now()});
 socket.on('data',b=>{const raw=new Uint8Array(b),at=now();socket.pause();chain=chain.then(async()=>{await persist({kind:'RX',rawHex:hex(raw),hostMs:at});observer.frames(raw,{origin:'OBSERVED_OWNED_SITL',context:manifest,receivedAtMs:at},now());}).catch(e=>{error=e;observer.loss(e.message);socket.destroy();}).finally(()=>{if(!closed)socket.resume();});});
 socket.on('close',()=>{closed=true;observer.loss('SOCKET_CLOSED');chain=chain.then(()=>persist({kind:'SOCKET_CLOSE',hostMs:now()})).catch(e=>{error??=e;});});
 const send=async raw=>{if(closed||observer.snapshot(now()).phase==='INVALIDATED')throw Error('SEND_AFTER_LOSS');const f=new FullFramer().push(raw,0,0)[0];if(!f||f.system!==255||f.component!==190||![0,20,76].includes(f.id)||f.id===76&&(f.fields.command!==512||f.fields.param1!==148||[2,3,4,5,6,7].some(k=>f.fields['param'+k]!==0))||f.id===20&&(!NAMES.includes(f.fields.param_id)||f.fields.param_index!==-1)||f.id!==0&&(f.fields.target_system!==42||f.fields.target_component!==1))throw Error('LIVE_OUTPUT_WHITELIST');await persist({kind:'TX_INTENT',rawHex:hex(raw),hostMs:now()});await new Promise((resolve,reject)=>socket.write(raw,e=>e?reject(e):resolve()));await persist({kind:'TX_WRITE_RETURN',rawHex:hex(raw),hostMs:now()});};
 const wait=async(predicate,ms=10000)=>{const deadline=now()+ms;while(now()<deadline){await chain;if(error)throw error;if(predicate(observer.snapshot(now())))return;await new Promise(r=>setTimeout(r,25));}throw Error('BOUNDED_WAIT_TIMEOUT');};
 const close=async()=>{socket.destroy();await new Promise(r=>setTimeout(r,25));await chain;await file.close();};
 return {observer,now,send,wait,close,isClosed:()=>closed,persist,flush:()=>chain,rawFile:path};
}
