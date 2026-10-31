import {DEFINITIONS} from './definitions.mjs';
import {crc,hex,int,decodeHex} from './bytes.mjs';

export {DEFINITIONS,hex};
export function unhex(s){if(typeof s!=='string'||s.length>32768||s.length%2||!/^[a-f0-9]*$/i.test(s))throw Error('bounded hex');return decodeHex(s);}
const SIZE={char:1,uint8_t:1,int8_t:1,uint16_t:2,int16_t:2,uint32_t:4,int32_t:4,uint64_t:8,int64_t:8,float:4,double:8};
const METHOD={uint8_t:'Uint8',int8_t:'Int8',uint16_t:'Uint16',int16_t:'Int16',uint32_t:'Uint32',int32_t:'Int32',uint64_t:'BigUint64',int64_t:'BigInt64',float:'Float32',double:'Float64'};
/** Raw fixture serializer, no command authority/IO. Adapter exposes a strict outbound whitelist. */
export function encodeFull(id,fields={},meta={}){
 const d=DEFINITIONS[id];if(!d)throw Error('outside pinned dialect');const {system=1,component=1,seq=0,version=2}=meta;
 int(system,1,255,'system');int(component,1,255,'component');int(seq,0,255,'sequence');if(![1,2].includes(version)||version===1&&id>255)throw Error('wire version/id');
 if(Object.keys(fields).some(k=>!d.fields.some(f=>f.name===k)))throw Error('unknown fixture field');
 const p=new Uint8Array(d.max),v=new DataView(p.buffer);
 for(const f of d.fields){let x=fields[f.name]??0;if(id===0&&f.name==='mavlink_version')x=3;
  if(version===1&&f.extension){if(fields[f.name]!==undefined)throw Error('v1 extension unsupported');continue;}
  if(f.type==='char'){if(x===0)x='';if(typeof x!=='string'||x.length>f.array||!/^[\x20-\x7e]*$/.test(x))throw Error('ASCII fixture');p.set(new TextEncoder().encode(x),f.offset);continue;}
  if(f.array&&x!==0&&(!Array.isArray(x)||x.length!==f.array))throw Error('array bound');
  for(let i=0;i<(f.array||1);i++){let n=f.array?(x===0?0:x[i]):x;const bits=SIZE[f.type]*8;
   if(f.type.includes('64_t')){if(typeof n==='number'&&!Number.isSafeInteger(n)||typeof n==='string'&&!/^-?\d{1,20}$/.test(n))throw Error('wide integer');n=BigInt(n);const unsigned=f.type[0]==='u';if(n<(unsigned?0n:-(1n<<63n))||n>(unsigned?(1n<<64n)-1n:(1n<<63n)-1n))throw Error('wide range');}
   else if(f.type.endsWith('_t'))int(n,f.type[0]==='u'?0:-(2**(bits-1)),f.type[0]==='u'?2**bits-1:2**(bits-1)-1,'integer field');
   else if(typeof n!=='number'||!Number.isFinite(n)||f.type==='float'&&!Number.isFinite(Math.fround(n)))throw Error('finite fixture float');
   v['set'+METHOD[f.type]](f.offset+i*SIZE[f.type],n,true);
  }
 }
 let len=version===1?d.min:d.max;if(version===2)while(len>1&&p[len-1]===0)len--;
 const header=version===2?Uint8Array.of(253,len,0,0,seq,system,component,id&255,id>>8&255,id>>16&255):Uint8Array.of(254,len,seq,system,component,id);
 const out=new Uint8Array(header.length+len+2);out.set(header);out.set(p.slice(0,len),header.length);const c=crc(out.subarray(1,-2),d.crc);out[out.length-2]=c&255;out[out.length-1]=c>>8;return out;
}
export class FullFramer {
 #bytes=new Uint8Array();#times=[];#last=null;#closed=false;#reason=null;
 #counts={known:0,opaque:0,signed:0,noise:0};
 close(reason){this.#closed=true;this.#reason=reason;this.#bytes=new Uint8Array();this.#times=[];}
 #fail(r){this.close(r);throw Error(r);}
 snapshot(){return {closed:this.#closed,reason:this.#reason,pendingBytes:this.#bytes.length,firstPendingAtMs:this.#times[0]??null,...this.#counts};}
 tick(t){int(t,0,1e12,'clock');if(this.#closed)return false;if(this.#last!==null&&t<this.#last)this.#fail('FRAMER_CLOCK_REGRESSION');if(this.#times.length&&t-this.#times[0]>1500)this.#fail('PARTIAL_FRAME_STALE');return true;}
 push(chunk,atMs,nowMs=atMs){
  if(this.#closed)throw Error('FRAMER_CLOSED');try{
   int(atMs,0,1e12,'receipt');int(nowMs,0,1e12,'now');if(!(chunk instanceof Uint8Array)||!chunk.length||chunk.length>16384)this.#fail('CHUNK_BOUND');
   if(atMs>nowMs||nowMs-atMs>1500||this.#last!==null&&atMs<this.#last)this.#fail('BYTE_RECEIPT_CLOCK');this.tick(nowMs);this.#last=atMs;
   const bytes=new Uint8Array(this.#bytes.length+chunk.length);bytes.set(this.#bytes);bytes.set(chunk,this.#bytes.length);this.#bytes=bytes;this.#times.push(...Array(chunk.length).fill(atMs));const frames=[];
   const drop=n=>{this.#bytes=this.#bytes.slice(n);this.#times=this.#times.slice(n);};
   while(this.#bytes.length){const q=this.#bytes;if(![253,254].includes(q[0])){if(++this.#counts.noise>64)this.#fail('NOISE_BOUND');drop(1);continue;}
    const v2=q[0]===253,h=v2?10:6;if(q.length<h)break;
    if(v2&&(q[2]&254))this.#fail('UNKNOWN_INCOMPATIBLE_FLAGS');
    const signed=v2&&!!(q[2]&1),len=q[1],n=h+len+2+(signed?13:0),id=v2?q[7]+256*q[8]+65536*q[9]:q[5],d=DEFINITIONS[id];
    if(!len||d&&(len>d.max||!v2&&len!==d.min))this.#fail('PAYLOAD_LENGTH');if(!q[v2?5:3]||!q[v2?6:4])this.#fail('SENDER_ZERO');if(q.length<n)break;
    if(nowMs-this.#times[0]>1500)this.#fail('FIRST_BYTE_STALE');
    if(d&&crc(q.subarray(1,h+len),d.crc)!==(q[h+len]+256*q[h+len+1]))this.#fail('FRAME_CRC');
    const raw=q.slice(0,n),fields={},present=[],invalidText=[];
    if(d){const p=new Uint8Array(d.max);p.set(raw.subarray(h,h+len));const v=new DataView(p.buffer);
     for(const f of d.fields){if(!f.extension||f.offset<len)present.push(f.name);
      if(f.type==='char'){const a=p.subarray(f.offset,f.offset+f.array),end=a.indexOf(0),part=a.subarray(0,end<0?a.length:end);if(part.some(x=>x<32||x>126)||end>=0&&a.subarray(end).some(x=>x!==0))invalidText.push(f.name);fields[f.name]=new TextDecoder().decode(part);continue;}
      const values=[];for(let i=0;i<(f.array||1);i++){const x=v['get'+METHOD[f.type]](f.offset+i*SIZE[f.type],true);values.push(typeof x==='bigint'?x.toString():x);}fields[f.name]=f.array?values:values[0];
     }
    }
    frames.push({id,name:d?.name??null,version:v2?2:1,seq:raw[v2?4:2],system:raw[v2?5:3],component:raw[v2?6:4],fields,present,invalidText,payloadLength:len,
     known:!!d,crcVerified:!!d,signed,signatureHex:signed?hex(raw.slice(-13)):null,rawHex:hex(raw),firstByteAtMs:this.#times[0],lastByteAtMs:this.#times[n-1],
     authentication:signed?'SIGNED_UNVERIFIED':'UNSIGNED_NOT_AUTHENTICATED',origin:'MOCK_REPLAY'});
    if(frames.length>64)this.#fail('BATCH_FRAME_BOUND');this.#counts[d?'known':'opaque']++;if(signed)this.#counts.signed++;drop(n);
   }
   if(this.#bytes.length>280)this.#fail('PENDING_BOUND');return frames;
  }catch(e){if(!this.#closed)this.close(e.message);throw e;}
 }
}
