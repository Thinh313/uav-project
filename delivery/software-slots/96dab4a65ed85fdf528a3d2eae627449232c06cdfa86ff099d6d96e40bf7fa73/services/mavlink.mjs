import {DEFINITIONS} from './mavlink-definitions.mjs';
export {DEFINITIONS};
const sizes={char:1,uint8_t:1,int8_t:1,uint16_t:2,int16_t:2,uint32_t:4,int32_t:4,uint64_t:8,int64_t:8,float:4,double:8};
const methods={uint8_t:'UInt8',int8_t:'Int8',uint16_t:'UInt16LE',int16_t:'Int16LE',uint32_t:'UInt32LE',int32_t:'Int32LE',uint64_t:'BigUInt64LE',int64_t:'BigInt64LE',float:'FloatLE',double:'DoubleLE'};
export function crc(bytes,extra){let c=0xffff;for(const b of [...bytes,...(extra===undefined?[]:[extra])]){let t=b^(c&255);t^=(t<<4)&255;c=((c>>8)^(t<<8)^(t<<3)^(t>>4))&65535;}return c;}
export function encode(id,fields={}, {seq=0,system=255,component=190,version=2}={}){
 const d=DEFINITIONS[id];if(!d)throw Error('Unsupported MAVLink message');const p=Buffer.alloc(d.max);
 for(const f of d.fields){let v=fields[f.name]??0;if(f.type==='char'){Buffer.from(String(v===0?'':v)).copy(p,f.offset,0,f.array);continue;}
  for(let i=0;i<(f.array||1);i++){const x=f.array?(Array.isArray(v)?v[i]??0:0):v;p['write'+methods[f.type]](f.type.includes('64_t')?BigInt(x):x,f.offset+i*sizes[f.type]);}}
 let length=version===1?d.min:p.length;if(version===2)while(length>1&&p[length-1]===0)length--;
 const h=version===1?Buffer.from([0xfe,length,seq&255,system,component,id]):Buffer.from([0xfd,length,0,0,seq&255,system,component,id&255,(id>>8)&255,(id>>16)&255]);
 const frame=Buffer.concat([h,p.subarray(0,length),Buffer.alloc(2)]);frame.writeUInt16LE(crc(frame.subarray(1,-2),d.crc),frame.length-2);return frame;
}
export class Decoder{
 constructor(){this.buffer=Buffer.alloc(0);this.stats={accepted:0,unknown:0,corrupt:0,unsupported:0};}
 push(chunk){this.buffer=Buffer.concat([this.buffer,chunk]);const messages=[];
  while(this.buffer.length){const magic=this.buffer[0];if(![0xfe,0xfd].includes(magic)){this.buffer=this.buffer.subarray(1);continue;}
   const h=magic===0xfd?10:6;if(this.buffer.length<h)break;const signed=magic===0xfd&&(this.buffer[2]&1),n=h+this.buffer[1]+2+(signed?13:0);if(this.buffer.length<n)break;
   const frame=this.buffer.subarray(0,n);this.buffer=this.buffer.subarray(n);const id=magic===0xfd?frame.readUIntLE(7,3):frame[5],d=DEFINITIONS[id];
   if(magic===0xfd&&frame[2]!==0){this.stats.unsupported++;continue;}// Signing verification is not implemented in this SITL-only adapter.
   if(!d){this.stats.unknown++;continue;}if(frame[1]>d.max||magic===0xfe&&frame[1]!==d.min||crc(frame.subarray(1,h+frame[1]),d.crc)!==frame.readUInt16LE(h+frame[1])){this.stats.corrupt++;continue;}
   const p=Buffer.alloc(d.max);frame.copy(p,0,h,h+frame[1]);const fields={};
   for(const f of d.fields){if(f.type==='char'){fields[f.name]=p.subarray(f.offset,f.offset+f.array).toString().split('\0')[0];continue;}
    const values=[];for(let i=0;i<(f.array||1);i++){const x=p['read'+methods[f.type]](f.offset+i*sizes[f.type]);values.push(typeof x==='bigint'?Number(x):x);}fields[f.name]=f.array?values:values[0];}
   this.stats.accepted++;messages.push({id,name:d.name,system:frame[magic===0xfd?5:3],component:frame[magic===0xfd?6:4],seq:frame[magic===0xfd?4:2],fields});
  }return messages;
 }
}
