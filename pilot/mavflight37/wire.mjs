import {DEFINITIONS} from './definitions.mjs';
export {DEFINITIONS};
const SIZE={char:1,uint8_t:1,int8_t:1,uint16_t:2,int16_t:2,uint32_t:4,int32_t:4,uint64_t:8,int64_t:8,float:4,double:8};
const METHOD={uint8_t:'Uint8',int8_t:'Int8',uint16_t:'Uint16',int16_t:'Int16',uint32_t:'Uint32',int32_t:'Int32',uint64_t:'BigUint64',int64_t:'BigInt64',float:'Float32',double:'Float64'};
const integer=(x,lo,hi)=>Number.isSafeInteger(x)&&x>=lo&&x<=hi;
export const hex=b=>Buffer.from(b).toString('hex');
export function unhex(s){if(typeof s!=='string'||s.length>8192||s.length%2||!/^[a-f0-9]*$/i.test(s))throw Error('bounded hex');return new Uint8Array(Buffer.from(s,'hex'))}
export function crc(bytes,extra){let c=65535;for(const b of [...bytes,...(extra===undefined?[]:[extra])]){let t=b^(c&255);t^=(t<<4)&255;c=((c>>8)^(t<<8)^(t<<3)^(t>>4))&65535}return c}
/** Serializer has no transport. Only MOCK_BUFFER capability wrappers may expose outgoing frames. */
export function encode(id,fields={},meta={}){
 const d=DEFINITIONS[id];if(!d)throw Error('message outside subset');const{system=255,component=190,seq=0,version=2}=meta;
 if(!integer(system,1,255)||!integer(component,1,255)||!integer(seq,0,255)||![1,2].includes(version))throw Error('header bounds');
 if(!fields||typeof fields!=='object'||Array.isArray(fields)||Object.keys(fields).some(k=>!d.fields.some(f=>f.name===k)))throw Error('unknown fields');
 const p=new Uint8Array(d.max),view=new DataView(p.buffer);
 for(const f of d.fields){let x=fields[f.name]??0;if(id===0&&f.name==='mavlink_version')x=3;
  if(version===1&&f.extension&&fields[f.name]!==undefined&&fields[f.name]!==0)throw Error('v1 extension discarded');
  if(f.type==='char'){if(x===0)x='';if(typeof x!=='string'||x.length>f.array||!/^[\x20-\x7e]*$/.test(x))throw Error('ASCII field');p.set(new TextEncoder().encode(x),f.offset);continue}
  if(f.array&&x!==0&&(!Array.isArray(x)||x.length!==f.array))throw Error('array bound');
  for(let i=0;i<(f.array||1);i++){let n=f.array?(x===0?0:x[i]):x;const bits=SIZE[f.type]*8;
   if(f.type.includes('64_t')){if(typeof n==='number'&&!Number.isSafeInteger(n)||!['number','bigint','string'].includes(typeof n)||typeof n==='string'&&!/^-?\d{1,20}$/.test(n))throw Error('wide integer');n=BigInt(n);const unsigned=f.type[0]==='u',lo=unsigned?0n:-(1n<<63n),hi=unsigned?(1n<<64n)-1n:(1n<<63n)-1n;if(n<lo||n>hi)throw Error('wide range')}
   else if(f.type.endsWith('_t')){if(!integer(n,f.type[0]==='u'?0:-(2**(bits-1)),f.type[0]==='u'?2**bits-1:2**(bits-1)-1))throw Error('integer range')}
   else if(typeof n!=='number'||!Number.isFinite(n)&&!(Number.isNaN(n)&&f.invalid==='[NaN]')||f.type==='float'&&Number.isFinite(n)&&!Number.isFinite(Math.fround(n)))throw Error('finite float range');
   view['set'+METHOD[f.type]](f.offset+i*SIZE[f.type],n,true);
  }
 }
 let len=version===1?d.min:d.max;if(version===2)while(len>1&&p[len-1]===0)len--;
 const header=version===2?Uint8Array.of(253,len,0,0,seq,system,component,id&255,id>>8&255,id>>16&255):Uint8Array.of(254,len,seq,system,component,id);
 const bytes=new Uint8Array(header.length+len+2);bytes.set(header);bytes.set(p.subarray(0,len),header.length);const checksum=crc(bytes.subarray(1,-2),d.crc);bytes[bytes.length-2]=checksum&255;bytes[bytes.length-1]=checksum>>8;return bytes;
}
export class Decoder{
 buffer=new Uint8Array();times=new Float64Array();stats={accepted:0,corrupt:0,unknown:0,unsupported:0,noise:0,invalidIdentity:0};
 reset(){this.buffer=new Uint8Array();this.times=new Float64Array()}
 drop(n){this.buffer=this.buffer.subarray(n);this.times=this.times.subarray(n)}
 push(chunk,atMs=null){if(!(chunk instanceof Uint8Array)||chunk.length>4096||atMs!==null&&!integer(atMs,0,1e12)){this.reset();throw Error('chunk type/bound/time')}
  const b=new Uint8Array(this.buffer.length+chunk.length),times=new Float64Array(b.length);b.set(this.buffer);b.set(chunk,this.buffer.length);times.set(this.times);times.fill(atMs??NaN,this.buffer.length);this.buffer=b;this.times=times;const out=[];
  while(this.buffer.length){const q=this.buffer;if(![253,254].includes(q[0])){this.drop(1);this.stats.noise++;continue}const v2=q[0]===253,h=v2?10:6;if(q.length<h)break;
   const len=q[1],n=h+len+2+(v2&&(q[2]&1)?13:0);if(q.length<n)break;
   if(v2&&q[2]!==0){this.stats.unsupported++;this.drop(n);continue}
   const id=v2?q[7]+q[8]*256+q[9]*65536:q[5],d=DEFINITIONS[id];if(!d){this.stats.unknown++;this.drop(n);continue}
   if(!len||len>d.max||!v2&&len!==d.min||crc(q.subarray(1,h+len),d.crc)!==(q[h+len]+q[h+len+1]*256)){this.stats.corrupt++;this.drop(1);continue}
   const firstByteAtMs=this.times[0],lastByteAtMs=this.times[n-1],raw=q.slice(0,n);this.drop(n);const system=raw[v2?5:3],component=raw[v2?6:4];if(!system||!component){this.stats.invalidIdentity++;continue}
   const payload=new Uint8Array(d.max);payload.set(raw.subarray(h,h+len));const view=new DataView(payload.buffer),fields={},present=[],invalidText=[];
   for(const f of d.fields){if(!f.extension||f.offset<len)present.push(f.name);
    if(f.type==='char'){const chars=payload.subarray(f.offset,f.offset+f.array),end=chars.indexOf(0),part=chars.subarray(0,end<0?chars.length:end);if(part.some(x=>x<32||x>126)||end>=0&&chars.subarray(end).some(x=>x!==0))invalidText.push(f.name);fields[f.name]=new TextDecoder().decode(part);continue}
    const values=[];for(let i=0;i<(f.array||1);i++){const x=view['get'+METHOD[f.type]](f.offset+i*SIZE[f.type],true);values.push(typeof x==='bigint'?x.toString():x)}fields[f.name]=f.array?values:values[0];
   }
   this.stats.accepted++;out.push({id,name:d.name,version:v2?2:1,system,component,seq:raw[v2?4:2],payloadLength:len,fields,present,invalidText,rawHex:hex(raw),firstByteAtMs:Number.isFinite(firstByteAtMs)?firstByteAtMs:null,lastByteAtMs:Number.isFinite(lastByteAtMs)?lastByteAtMs:null,authentication:'UNSIGNED_NOT_AUTHENTICATED',origin:'MOCK_MAVLINK_REPLAY'});
  }if(this.buffer.length>280){this.reset();throw Error('pending frame bound')}return out;
 }
}
