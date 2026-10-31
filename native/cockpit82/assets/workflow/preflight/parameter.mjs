import{FullFramer,hex}from'./wire.mjs';
export function parameterFrame(bytes){const d=new FullFramer(),fs=d.push(bytes,0,0);if(fs.length!==1||fs[0].id!==22||fs[0].rawHex!==hex(bytes)||fs[0].signed||fs[0].invalidText.length||d.snapshot().pendingBytes)throw Error('one valid PARAM_VALUE required');const f=fs[0],h=f.version===2?10:6;return{...f,valueBytes:bytes.slice(h,h+4)}}
const integerTypes={1:[1,false],2:[1,true],3:[2,false],4:[2,true],5:[4,false],6:[4,true]};
export function decodeParameter(raw,type,encoding){if(!(raw instanceof Uint8Array)||raw.length!==4||!['C_CAST','BYTEWISE'].includes(encoding))throw Error('parameter encoding unknown');if([7,8,10].includes(type)||!integerTypes[type]&&type!==9)throw Error('classic64/unknown type unsupported');const v=new DataView(raw.buffer,raw.byteOffset,4);
 if(type===9){const n=v.getFloat32(0,true);if(!Number.isFinite(n))throw Error('nonfinite REAL32');return n}
 const[bytes,signed]=integerTypes[type],lo=signed?-(2**(bytes*8-1)):0,hi=signed?2**(bytes*8-1)-1:2**(bytes*8)-1;
 const n=encoding==='BYTEWISE'?v['get'+(signed?'Int':'Uint')+(bytes*8)](0,true):v.getFloat32(0,true);
 if(!Number.isInteger(n)||n<lo||n>hi||encoding==='C_CAST'&&bytes===4&&Math.abs(n)>=2**24)throw Error('out of range/fractional/ambiguous C-cast integer');return n;
}
