import {DEFINITIONS,Decoder,crc,hex} from '../mavflight37/wire.mjs';
import {VERSION_SCHEMA} from '../firmware38/version-schema.mjs';
import {versionFrame} from '../firmware38/wire.mjs';
import {int} from '../apflight36/types.mjs';

/** Bounded, fail-closed union framing. No IO or sender authentication. */
export class UnionFramer {
  #bytes=new Uint8Array(); #times=[]; #closed=false; #reason=null;
  #last=null; #noise=0; #accepted=0;
  close(reason){this.#closed=true;this.#reason=reason;this.#bytes=new Uint8Array();this.#times=[];}
  #fail(reason){this.close(reason);throw Error(reason);}
  snapshot(){return {closed:this.#closed,reason:this.#reason,pendingBytes:this.#bytes.length,
    firstPendingAtMs:this.#times[0]??null,noiseBytes:this.#noise,acceptedFrames:this.#accepted};}
  tick(nowMs){int(nowMs,0,1e12,'framer clock');if(this.#closed)return false;
    if(this.#last!==null&&nowMs<this.#last)this.#fail('FRAMER_CLOCK_REGRESSION');
    if(this.#times.length&&nowMs-this.#times[0]>1500)this.#fail('PARTIAL_FRAME_STALE');
    return true;
  }
  push(chunk,atMs,nowMs=atMs){
    if(this.#closed)throw Error('FRAMER_CLOSED:'+this.#reason);
    try{int(atMs,0,1e12,'byte receipt');int(nowMs,0,1e12,'now');
      if(!(chunk instanceof Uint8Array)||!chunk.length||chunk.length>4096)this.#fail('CHUNK_BOUND');
      if(atMs>nowMs||nowMs-atMs>1500||this.#last!==null&&atMs<this.#last)this.#fail('BYTE_RECEIPT_CLOCK');
      this.tick(nowMs);this.#last=atMs;
      const bytes=new Uint8Array(this.#bytes.length+chunk.length);bytes.set(this.#bytes);bytes.set(chunk,this.#bytes.length);
      this.#bytes=bytes;this.#times.push(...Array(chunk.length).fill(atMs));const out=[];
      const drop=n=>{this.#bytes=this.#bytes.slice(n);this.#times=this.#times.slice(n);};
      while(this.#bytes.length){
        const b=this.#bytes;
        if(![253,254].includes(b[0])){if(++this.#noise>64)this.#fail('NOISE_BOUND');drop(1);continue;}
        const v2=b[0]===253,h=v2?10:6;if(b.length<h)break;
        if(v2&&b[2]!==0)this.#fail('SIGNED_OR_INCOMPATIBLE_FRAME');
        const id=v2?b[7]+b[8]*256+b[9]*65536:b[5];
        const d=id===148&&v2?VERSION_SCHEMA:DEFINITIONS[id];
        if(!d||id===148&&!v2)this.#fail('MESSAGE_OUTSIDE_REVIEWED_SUBSET');
        const len=b[1],n=h+len+2;
        if(!len||len>d.max||!v2&&len!==d.min)this.#fail('PAYLOAD_LENGTH');
        if(!b[v2?5:3]||!b[v2?6:4])this.#fail('FRAME_SENDER_ZERO');
        if(b.length<n)break;
        if(nowMs-this.#times[0]>1500)this.#fail('FRAME_FIRST_BYTE_STALE');
        if(crc(b.subarray(1,h+len),d.crc)!==(b[h+len]+256*b[h+len+1]))this.#fail('FRAME_CRC');
        const raw=b.slice(0,n),firstByteAtMs=this.#times[0],lastByteAtMs=this.#times[n-1];
        const frame=id===148?{...versionFrame(raw),id:148,seq:raw[4],version:2,name:'AUTOPILOT_VERSION'}:new Decoder().push(raw,firstByteAtMs)[0];
        if(!frame)this.#fail('FRAME_DECODE');
        out.push({...frame,rawHex:hex(raw),firstByteAtMs,lastByteAtMs,
          authentication:'UNSIGNED_NOT_AUTHENTICATED',origin:'MOCK_REPLAY'});
        if(out.length>64)this.#fail('BATCH_FRAME_BOUND');
        this.#accepted++;drop(n);
      }
      if(this.#bytes.length>267)this.#fail('PENDING_FRAME_BOUND');
      return out;
    }catch(e){if(!this.#closed)this.close(e.message);throw e;}
  }
}
