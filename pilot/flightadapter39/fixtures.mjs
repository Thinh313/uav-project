import {input,VALUES} from '../firmware38/corpus.mjs';
import {REFERENCE} from '../firmware38/contract.mjs';
import {packVersion,packParameter,hex} from '../firmware38/wire.mjs';
import {encode,Decoder,unhex} from '../mavflight37/wire.mjs';
import {telemetryCase} from '../mavflight37/scenarios.mjs';
import {TARGET,CLOCK} from '../apflight36/fixtures.mjs';

export const meta=t=>({origin:'MOCK_REPLAY',target:structuredClone(TARGET),epoch:CLOCK.epoch,receivedAtMs:t});
export const join=chunks=>{const out=new Uint8Array(chunks.reduce((n,c)=>n+c.length,0));let offset=0;for(const c of chunks){out.set(c,offset);offset+=c.length;}return out;};
export function version({seq=0,fields={},sender={},review=null}={}){const i=input();return packVersion({...structuredClone(review?.expected??i.contract.expected),capabilities:review?.encoding==='BYTEWISE'?'24596':'24582',...fields},{system:1,component:1,seq,...sender});}
export function parameters({firstSeq=1,values={},types={},encoding='C_CAST',count=500,index=65535}={}){return Object.keys(REFERENCE.parameters).map((n,k)=>({name:n,raw:packParameter(n,values[n]??VALUES[n],types[n]??REFERENCE.parameters[n].type,encoding,{seq:(firstSeq+k)%256,count,index}),t:20002+k*2}));}
export async function dialogue(){const i=input(),tc=await telemetryCase('adapter39-source');
 // Re-encode pinned fixture fields with central sequence and new receipt times.
 const telemetry=tc.input.frames.map((f,k)=>{const p=new Decoder().push(unhex(f.rawHex))[0];return {raw:encode(p.id,p.fields,{system:1,component:1,seq:29+k}),t:20080+k*2,id:p.id};});
 return {contract:i.contract,profile:tc.input.profile,apState:i.state,altitude:i.altitude,
  steps:[{op:'rx',rawHex:hex(version()),t:20000,meta:meta(20000)},
    ...parameters().map(p=>({op:'rx',rawHex:hex(p.raw),t:p.t,meta:meta(p.t)})),
    ...telemetry.map(p=>({op:'rx',rawHex:hex(p.raw),t:p.t,meta:meta(p.t)}))],inspectAtMs:20120};
}
