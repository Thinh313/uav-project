import {DEFINITIONS} from './definitions.mjs';
export {DEFINITIONS};
const size={char:1,uint8_t:1,int8_t:1,uint16_t:2,int16_t:2,uint32_t:4,int32_t:4,uint64_t:8,int64_t:8,float:4,double:8};
const method={uint8_t:'Uint8',int8_t:'Int8',uint16_t:'Uint16',int16_t:'Int16',uint32_t:'Uint32',int32_t:'Int32',uint64_t:'BigUint64',int64_t:'BigInt64',float:'Float32',double:'Float64'};
const integer=(x,lo,hi)=>Number.isInteger(x)&&x>=lo&&x<=hi;
export const hex=b=>[...b].map(n=>n.toString(16).padStart(2,'0')).join('');
export function unhex(s){if(typeof s!=='string'||s.length>2048||s.length%2||!/^[0-9a-f]*$/i.test(s))throw Error('Invalid bounded frame hex');return Uint8Array.from(s.match(/../g)||[],x=>parseInt(x,16));}
export function crc(bytes,extra){let c=65535;for(const b of [...bytes,...(extra===undefined?[]:[extra])]){let t=b^(c&255);t^=(t<<4)&255;c=((c>>8)^(t<<8)^(t<<3)^(t>>4))&65535;}return c;}
export function encode(mid,fields={},meta={}) {
 const d=DEFINITIONS[mid];if(!d)throw Error('Message outside pinned dialect');
 const {system=255,component=190,seq=0,version=2}=meta;if(!integer(system,1,255)||!integer(component,1,255)||!integer(seq,0,255)||![1,2].includes(version)||version===1&&mid>255)throw Error('Frame identity/version invalid');
 if(Object.keys(fields).some(k=>!d.fields.some(f=>f.name===k)))throw Error('Unknown message field');
 const p=new Uint8Array(d.max),v=new DataView(p.buffer);
 for(const f of d.fields){const x=mid===0&&f.name==='mavlink_version'?3:fields[f.name]??0;
  if(f.type==='char'){const b=new TextEncoder().encode(x===0?'':x);if(b.length>f.array)throw Error('Character field too long');p.set(b,f.offset);continue;}
  if(f.array&&x!==0&&(!Array.isArray(x)||x.length!==f.array))throw Error('Array field size invalid');
  for(let i=0;i<(f.array||1);i++){let n=f.array?(x===0?0:x[i]):x;const bits=size[f.type]*8;
   if(f.type.includes('64_t')){if(typeof n==='number'&&!Number.isSafeInteger(n))throw Error('Unsafe64-bit value');n=BigInt(n);if(n<0n||n>18446744073709551615n)throw Error('64-bit range');}
   else if(f.type.endsWith('_t')&&!integer(n,f.type[0]==='u'?0:-(2**(bits-1)),f.type[0]==='u'?2**bits-1:2**(bits-1)-1))throw Error('Integer field range');
   else if(['float','double'].includes(f.type)&&typeof n!=='number')throw Error('Float field type');
   v['set'+method[f.type]](f.offset+i*size[f.type],n,true);
  }
 }
 let len=version===1?d.min:d.max;if(version===2)while(len>1&&p[len-1]===0)len--;
 const h=version===2?Uint8Array.of(253,len,0,0,seq,system,component,mid&255,mid>>8&255,mid>>16&255):Uint8Array.of(254,len,seq,system,component,mid),b=new Uint8Array(h.length+len+2);b.set(h);b.set(p.subarray(0,len),h.length);const c=crc(b.subarray(1,-2),d.crc);b[b.length-2]=c&255;b[b.length-1]=c>>8;return b;
}
export class Decoder {
 buffer=new Uint8Array();stats={accepted:0,corrupt:0,unknown:0,unsupported:0,noise:0};
 push(chunk){if(!(chunk instanceof Uint8Array)||chunk.length>4096){this.buffer=new Uint8Array();throw Error('Decoder chunk bound/type');}const data=new Uint8Array(this.buffer.length+chunk.length);data.set(this.buffer);data.set(chunk,this.buffer.length);this.buffer=data;const messages=[];
  while(this.buffer.length){const b=this.buffer;if(![253,254].includes(b[0])){this.buffer=b.subarray(1);this.stats.noise++;continue;}const h=b[0]===253?10:6;if(b.length<h)break;const len=b[1],n=h+len+2+(b[0]===253&&(b[2]&1)?13:0);if(b.length<n)break;
   const raw=b.slice(0,n);this.buffer=b.subarray(n);if(b[0]===253&&b[2]!==0){this.stats.unsupported++;continue;}
   const mid=b[0]===253?b[7]+b[8]*256+b[9]*65536:b[5],d=DEFINITIONS[mid];if(!d){this.stats.unknown++;continue;}
   if(len<1||len>d.max||b[0]===254&&len!==d.min||crc(raw.subarray(1,h+len),d.crc)!==(raw[h+len]+raw[h+len+1]*256)){this.stats.corrupt++;continue;}
   const payload=new Uint8Array(d.max);payload.set(raw.subarray(h,h+len));const view=new DataView(payload.buffer),fields={},present=[];
   for(const f of d.fields){if(!f.extension||f.offset<len)present.push(f.name);if(f.type==='char'){fields[f.name]=new TextDecoder().decode(payload.subarray(f.offset,f.offset+f.array)).split('\0')[0];continue;}let a=[];for(let i=0;i<(f.array||1);i++){const v=view['get'+method[f.type]](f.offset+i*size[f.type],true);a.push(typeof v==='bigint'?v.toString():v);}fields[f.name]=f.array?a:a[0];}
   this.stats.accepted++;messages.push({id:mid,name:d.name,system:raw[b[0]===253?5:3],component:raw[b[0]===253?6:4],seq:raw[b[0]===253?4:2],version:b[0]===253?2:1,payloadLength:len,fields,present,rawHex:hex(raw),origin:'SYNTHETIC_PROTOCOL_CORPUS'});
  }
  if(this.buffer.length>280)throw Error('Decoder pending bound');return messages;
 }
}
