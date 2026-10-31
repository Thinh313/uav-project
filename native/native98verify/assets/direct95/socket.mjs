// Acceptance patch: preserve first observed JS transport failure before closing.
// Existing native generation, fsync, freshness and authority gates remain authoritative.
import{EventEmitter}from'./events.mjs';import{storage82}from'../transport82.mjs';
const hex=b=>Array.from(b,x=>x.toString(16).padStart(2,'0')).join(''),unhex=s=>Uint8Array.from(s.match(/../g)??[],x=>parseInt(x,16));let active=null;
export const now95=()=>Math.floor(globalThis.Native82Bridge?.elapsedRealtime?.()??performance.now());globalThis.nativeNow95=now95;
export async function native95(action,body={}){const r=await storage82('direct95:'+action,'ROOT',JSON.stringify(body));if(!r.ok)throw Error(r.error??'DIRECT95_OUTCOME_UNKNOWN');return r;}
const code98=e=>String(e?.message??e??'UNKNOWN').replace(/[^a-zA-Z0-9_ .:\-]/g,'_').slice(0,120);
export class Socket95 extends EventEmitter{
 constructor(){super();this.writable=false;this.closed=false;this.generation=null;this.queue=[];this.tx=Promise.resolve();this.txCount=0;this.firstFailure98=null;active=this;
  queueMicrotask(async()=>{try{const c=window.direct95Connecting;if(!c)throw Error('EXPLICIT_COMMITTED_CONNECT_CONTEXT_REQUIRED');const r=await native95('open',c);this.generation=r.generation;if(this.closed){await native95('close',{generation:this.generation,reason:'CLOSED_DURING_OPEN_NO_RESTORE'});return;}this.writable=true;this.emit('connect');setTimeout(()=>{if(this.closed)return;this.ready=true;const queued=this.queue;this.queue=[];for(const e of queued){if(this.closed)break;this.receive95(e);}},0);}catch(e){this.fail98(e,'OPEN');}});
 }
 setNoDelay(){}
 fail98(error,stage,detail={},closeNative=true){
  if(this.closed)return;
  if(!this.firstFailure98){
   this.firstFailure98={format:'aeris-js-transport-failure98',version:1,stage,code:code98(error),atMs:now95(),generation:this.generation,queuedRX:this.queue.length,queuedTX:this.txCount,...detail,observedFailureOnly:true,rootCause:'UNKNOWN'};
   try{const result=JSON.parse(window.Native82Bridge.record95('JS_TRANSPORT_FAILURE98',JSON.stringify(this.firstFailure98)));if(!result.ok)this.firstFailure98.diagnosticJournalUnavailable=true;}catch(_){this.firstFailure98.diagnosticJournalUnavailable=true;}
  }
  try{this.emit('error',error instanceof Error?error:Error(code98(error)));}catch(_){/* Error listeners cannot bypass closure. */}
  finally{this.destroy(closeNative,'JS_TRANSPORT_FAULT98:'+this.firstFailure98.stage+':'+this.firstFailure98.code);}
 }
 write(bytes,callback){
  if(!this.writable||this.closed){callback?.(Error('NATIVE_SOCKET_CLOSED'));return false;}
  if(++this.txCount>32){this.txCount--;this.fail98(Error('NATIVE_TX_QUEUE_BOUND'),'TX_QUEUE');callback?.(Error('NATIVE_TX_QUEUE_BOUND'));return false;}
  const work=this.tx.then(()=>{if(this.closed||!this.writable)throw Error('NATIVE_CLOSED_BEFORE_QUEUED_WRITE');return native95('write',{generation:this.generation,hex:hex(bytes)});});this.tx=work;
  work.then(()=>{this.txCount--;try{callback?.();}catch(e){this.fail98(e,'TX_CALLBACK');}},e=>{this.txCount--;this.fail98(e,'TX_WRITE');try{callback?.(e);}catch(_){}});return true;
 }
 receive95(e){
  if(this.closed)return;
  if(!this.ready||!this.generation){if(this.queue.length>=64){this.fail98(Error('NATIVE_RX_QUEUE_BOUND'),'RX_QUEUE');return;}this.queue.push(e);return;}
  if(e?.generation!==this.generation)return;
  if(e.kind==='DATA'){
   if(!Number.isSafeInteger(e.receiptMs)||!Number.isSafeInteger(e.sequence)||e.sequence<1||typeof e.hex!=='string'||!e.hex.length||e.hex.length>8192||e.hex.length%2||!/^[0-9a-f]+$/.test(e.hex)){this.fail98(Error('NATIVE_DATA_ENVELOPE'),'RX_ENVELOPE');return;}
   const lag=now95()-e.receiptMs;
   if(lag<0||lag>1500){this.fail98(Error('NATIVE_DELIVERY_STALE'),'RX_DELIVERY',{receiptMs:e.receiptMs,sequence:e.sequence,lagMs:lag,nativeTiming98:e.timing98??null,mainReadyMs:e.mainReadyMs??null});return;}
   this.receivedAt95=e.receiptMs;
   try{this.emit('data',unhex(e.hex));}catch(x){this.fail98(x,'RX_CONSUMER',{sequence:e.sequence});return;}
   try{const ack=JSON.parse(window.Native82Bridge.ack95(this.generation,e.sequence));if(!ack.ok)throw Error(ack.error??'NATIVE_ACK_REFUSED');}catch(x){this.fail98(x,'RX_ACK',{sequence:e.sequence});}
  }else if(e.kind==='CLOSED'){this.fail98(Error(e.reason??'NATIVE_TRANSPORT_CLOSED'),'NATIVE_CLOSE',{},false);}
  else this.fail98(Error('NATIVE_EVENT_KIND'),'RX_ENVELOPE');
 }
 destroy(closeNative=true,reason='EXPLICIT_SOCKET_CLOSE'){
  if(this.closed)return;this.closed=true;this.writable=false;this.queue=[];
  if(closeNative)native95('close',{generation:this.generation,reason}).catch(()=>{});
  try{this.emit('close');}catch(_){/* Native close has already been requested. */}
 }
}
window.native95Event=raw=>{try{active?.receive95(typeof raw==='string'?JSON.parse(raw):raw);}catch(e){active?.fail98(e,'RX_EVENT_JSON');}};
export default{createConnection:options=>{if(options.host!=='127.0.0.1'||options.port!==5937)throw Error('FIXED_OWNED_SITL_ENDPOINT');return new Socket95();}};
