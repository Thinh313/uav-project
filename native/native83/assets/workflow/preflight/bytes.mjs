export const hex=b=>Array.from(b,x=>x.toString(16).padStart(2,'0')).join('');
export const decodeHex=s=>Uint8Array.from({length:s.length/2},(_,i)=>parseInt(s.slice(i*2,i*2+2),16));
export function int(v,lo,hi,label){if(typeof v!=='number'||!Number.isFinite(v)||v<lo||v>hi)throw Error(label+' range');if(!Number.isSafeInteger(v))throw Error(label+' integer');return v;}
export function crc(bytes,extra){let c=65535;for(const b of [...bytes,...(extra===undefined?[]:[extra])]){let t=b^(c&255);t^=(t<<4)&255;c=((c>>8)^(t<<8)^(t<<3)^(t>>4))&65535;}return c;}
