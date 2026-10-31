import {VERSION_SCHEMA as S} from './version-schema.mjs';
import {crc,encode,Decoder,unhex,hex} from '../mavflight37/wire.mjs';
import {int} from '../apflight36/types.mjs';
export{unhex,hex};
const sizes={uint64_t:8,uint32_t:4,uint16_t:2,uint8_t:1},methods={uint64_t:'BigUint64',uint32_t:'Uint32',uint16_t:'Uint16',uint8_t:'Uint8'};
export function packVersion(fields,meta={system:1,component:1,seq:0}){for(const k of ['system','component'])int(meta[k],1,255,k);int(meta.seq,0,255,'seq');if(Object.keys(fields).some(k=>!S.fields.some(f=>f.name===k)))throw Error('unknown version field');const p=new Uint8Array(S.max),v=new DataView(p.buffer);
 for(const f of S.fields){const val=fields[f.name]??0;if(f.array&&val!==0&&(!Array.isArray(val)||val.length!==f.array))throw Error('array');for(let i=0;i<(f.array||1);i++){let n=f.array?(val===0?0:val[i]):val;if(f.type==='uint64_t'){if(typeof n==='number'&&!Number.isSafeInteger(n)||typeof n==='string'&&!/^\d{1,20}$/.test(n))throw Error('unsafe uint64');n=BigInt(n);if(n<0n||n>(1n<<64n)-1n)throw Error('uint64 range')}else int(n,0,2**(sizes[f.type]*8)-1,'version value');v['set'+methods[f.type]](f.offset+i*sizes[f.type],n,true)}}
 let len=p.length;while(len>1&&!p[len-1])len--;const b=new Uint8Array(10+len+2);b.set([253,len,0,0,meta.seq,meta.system,meta.component,148,0,0]);b.set(p.subarray(0,len),10);const c=crc(b.subarray(1,-2),S.crc);b[b.length-2]=c&255;b[b.length-1]=c>>8;return b;
}
export function versionFrame(bytes){if(!(bytes instanceof Uint8Array)||bytes.length<13||bytes[0]!==253||bytes[2]!==0||bytes[7]!==148||bytes[8]!==0||bytes[9]!==0||bytes[1]<1||bytes[1]>S.max||bytes.length!==12+bytes[1]||!bytes[5]||!bytes[6]||crc(bytes.subarray(1,-2),S.crc)!==(bytes.at(-2)+bytes.at(-1)*256))throw Error('version packet outside unsigned v2 subset');const p=new Uint8Array(S.max);p.set(bytes.subarray(10,-2));const v=new DataView(p.buffer),fields={};
 for(const f of S.fields){const a=[];for(let i=0;i<(f.array||1);i++){const n=v['get'+methods[f.type]](f.offset+i*sizes[f.type],true);a.push(typeof n==='bigint'?n.toString():n)}fields[f.name]=f.array?a:a[0]}
 return{fields,system:bytes[5],component:bytes[6],sequence:bytes[4],rawHex:hex(bytes),authenticated:false};
}
export function parameterFrame(bytes){const fs=new Decoder().push(bytes);if(fs.length!==1||fs[0].id!==22||fs[0].rawHex!==hex(bytes)||fs[0].invalidText.length)throw Error('one valid PARAM_VALUE required');const f=fs[0],h=f.version===2?10:6;return{...f,valueBytes:bytes.slice(h,h+4)}}
const integerTypes={1:[1,false],2:[1,true],3:[2,false],4:[2,true],5:[4,false],6:[4,true]};
export function decodeParameter(raw,type,encoding){if(!(raw instanceof Uint8Array)||raw.length!==4||!['C_CAST','BYTEWISE'].includes(encoding))throw Error('parameter encoding unknown');if([7,8,10].includes(type)||!integerTypes[type]&&type!==9)throw Error('classic64/unknown type unsupported');const v=new DataView(raw.buffer,raw.byteOffset,4);
 if(type===9){const n=v.getFloat32(0,true);if(!Number.isFinite(n))throw Error('nonfinite REAL32');return n}
 const[bytes,signed]=integerTypes[type],lo=signed?-(2**(bytes*8-1)):0,hi=signed?2**(bytes*8-1)-1:2**(bytes*8)-1;
 const n=encoding==='BYTEWISE'?v['get'+(signed?'Int':'Uint')+(bytes*8)](0,true):v.getFloat32(0,true);
 if(!Number.isInteger(n)||n<lo||n>hi||encoding==='C_CAST'&&bytes===4&&Math.abs(n)>=2**24)throw Error('out of range/fractional/ambiguous C-cast integer');return n;
}
/** Only mock PARAM_VALUE fixtures are packed here, never PARAM_SET or transport. */
export function packParameter(name,value,type,encoding,{seq=0,system=1,component=1,index=65535,count=500}={}){const b=encode(22,{param_id:name,param_value:0,param_type:type,param_index:index,param_count:count},{seq,system,component});const raw=new Uint8Array(4),v=new DataView(raw.buffer);
 if(type===9||encoding==='C_CAST'){if(!Number.isFinite(value)||!Number.isFinite(Math.fround(value)))throw Error('mock float');v.setFloat32(0,value,true)}else{const info=integerTypes[type];if(!info)throw Error('unsupported fixture type');const[sz,sign]=info;int(value,sign?-(2**(sz*8-1)):0,sign?2**(sz*8-1)-1:2**(sz*8)-1,'fixture integer');v['set'+(sign?'Int':'Uint')+(sz*8)](0,value,true)}
 b.set(raw,10);const c=crc(b.subarray(1,-2),220);b[b.length-2]=c&255;b[b.length-1]=c>>8;return b;
}
