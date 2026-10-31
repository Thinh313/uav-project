import {Decoder,encode,hex} from './wire.mjs';
import {identity,same,exact,int,str} from '../apflight36/types.mjs';
/** Current-context scope is supplied by the mock harness, not encoded/authenticated on wire. */
export class ReplayLink{
 constructor(target,epoch){identity(target);str(epoch);this.target=structuredClone(target);this.epoch=epoch;this.decoder=new Decoder();this.lastAt=null;this.lastSeq=null;this.bootTimes=new Map();this.closed=false;this.reason=null;this.sequence=0}
 close(reason){this.closed=true;this.reason=reason;this.decoder.reset()}
 check(meta,nowMs){exact(meta,['origin','target','epoch','receivedAtMs']);int(nowMs,0,1e12,'now');int(meta.receivedAtMs,0,1e12,'receipt');
  if(this.closed)throw Error('new replay instance required: '+this.reason);
  if(meta.origin!=='MOCK_REPLAY'||!same(meta.target,this.target)||meta.epoch!==this.epoch)throw Error('wrong replay context');
  if(meta.receivedAtMs>nowMs||nowMs-meta.receivedAtMs>1500||this.lastAt!==null&&(meta.receivedAtMs<this.lastAt||meta.receivedAtMs-this.lastAt>5000)){this.close('STALE_SUSPENSION_OR_CLOCK');throw Error(this.reason)}
  this.lastAt=meta.receivedAtMs;
 }
 receive(bytes,meta,nowMs){this.check(meta,nowMs);const frames=[];for(const f of this.decoder.push(bytes,meta.receivedAtMs)){
   if(f.system!==this.target.system||f.component!==this.target.component)continue;
   if(nowMs-f.firstByteAtMs>1500){this.close('FRAME_ASSEMBLY_STALE');throw Error(this.reason)}
   if(this.lastSeq!==null){const delta=(f.seq-this.lastSeq+256)%256;if(delta===0||delta>=128)continue}
   if('time_boot_ms' in f.fields){const prev=this.bootTimes.get(f.id),t=f.fields.time_boot_ms;if(prev!==undefined&&((t-prev+2**32)%2**32)>=2**31){this.close('BOOT_CLOCK_REGRESSION');throw Error(this.reason)}this.bootTimes.set(f.id,t)}
   this.lastSeq=f.seq;frames.push({...f,receiptMs:f.firstByteAtMs,epoch:this.epoch,target:structuredClone(this.target),sourceSequence:++this.sequence});
  }return frames;
 }
 tick(nowMs){int(nowMs,0,1e12,'now');if(this.closed)return false;if(this.lastAt===null||nowMs<this.lastAt||nowMs-this.lastAt>1500){this.close('HEARTBEAT_OR_RECEIPT_STALE');return false}return true}
}
const TX_IDS=new Set([20,43,44,47,51,73]);
export class MockBuffer{
 constructor(target,gcs={system:255,component:190}){identity(target);int(gcs.system,1,255,'GCS system');int(gcs.component,1,255,'GCS component');this.target=structuredClone(target);this.gcs=structuredClone(gcs);this.sequence=0}
 packet(id,fields){if(!TX_IDS.has(id))throw Error('outbound message forbidden');if(fields.target_system!==this.target.system||fields.target_component!==this.target.component)throw Error('outbound target');if(id!==20&&fields.mission_type!==1)throw Error('only fence mission outbound');if(id===44)int(fields.count,1,64,'no clear/count bound');if(id===51||id===73)int(fields.seq,0,63,'item sequence');if(id===47&&fields.type!==0)throw Error('download completion ACK only');if(id===20&&(!/^[A-Z][A-Z0-9_]{0,15}$/.test(fields.param_id)||fields.param_index!==-1))throw Error('named readonly parameter only');if(id===73&&(![5001,5002,5003,5004].includes(fields.command)||fields.frame!==0||!(fields.param1>0)))throw Error('only fence commands');
  const raw=encode(id,fields,{...this.gcs,seq:this.sequence++%256});return{channel:'MOCK_BUFFER_ONLY',rawHex:hex(raw),id,operationalAllowed:false,networkSent:false};
 }
}
