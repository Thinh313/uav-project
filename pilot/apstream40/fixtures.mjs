import {dialogue as d39,parameters,version,join} from '../flightadapter39/fixtures.mjs';
import {DEFINITIONS,FullFramer,encodeFull,hex,unhex} from './wire.mjs';
import {crc} from '../mavflight37/wire.mjs';
export {parameters,version,join};
export const meta=(target,epoch,t)=>({origin:'MOCK_REPLAY',target:structuredClone(target),epoch,receivedAtMs:t});
export function resequence(raw,seq){const b=raw.slice(),v2=b[0]===253;intSeq(seq);b[v2?4:2]=seq;const id=v2?b[7]+b[8]*256+b[9]*65536:b[5],h=v2?10:6,c=crc(b.subarray(1,h+b[1]),DEFINITIONS[id].crc);b[h+b[1]]=c&255;b[h+b[1]+1]=c>>8;return b;}
const intSeq=s=>{if(!Number.isInteger(s)||s<0||s>255)throw Error('seq');};
export function signed(raw){const b=new Uint8Array(raw.length+13);b.set(raw);b[2]=1;const id=b[7]+b[8]*256+b[9]*65536,c=crc(b.subarray(1,10+b[1]),DEFINITIONS[id].crc);b[10+b[1]]=c&255;b[11+b[1]]=c>>8;b.fill(253,raw.length);return b;}
export function opaque({system=2,component=100}={}){return Uint8Array.of(253,3,0,0,7,system,component,255,255,254,253,254,253,11,22);}
export async function dialogue(){const old=await d39(),{contract,profile,apState,altitude}=old,steps=[];
 const rx=(raw,t)=>({op:'rx',rawHex:hex(raw),t,meta:meta(contract.target,contract.epoch,t)});
 steps.push(rx(encodeFull(0,{type:2,autopilot:3,base_mode:129,custom_mode:3},{seq:0}),20000),{op:'discover',t:20001},rx(version({seq:1}),20002));
 parameters({firstSeq:2}).forEach((p,k)=>steps.push(rx(p.raw,20004+k*2)));
 old.steps.slice(29).forEach((s,k)=>steps.push(rx(resequence(unhex(s.rawHex),30+k),20090+k*2)));
 return {contract,profile,apState,altitude,steps,inspectAtMs:20120,writerFault:false};
}
export function rx(i,raw,t){return {op:'rx',rawHex:hex(raw),t,meta:meta(i.contract.target,i.contract.epoch,t)};}
export function resequenceAP(steps){let seq=0;for(const s of steps)if(s.op==='rx'){const b=unhex(s.rawHex);if(b[5]===1&&b[6]===1&&DEFINITIONS[b[7]+b[8]*256+b[9]*65536])s.rawHex=hex(resequence(b,seq++%256));}return steps;}
