import {readFileSync} from 'node:fs';
import {encodeFull,hex} from '../apstream40/wire.mjs';
import {crc} from '../mavflight37/wire.mjs';
import {profile43,BINARY,NAMES,SCHEMA} from './profile.mjs';
export const baseline=JSON.parse(readFileSync(new URL('../../evidence/flightsafety42/run03/preflight-restored.json',import.meta.url),'utf8'));
export const context=(session='mock43')=>({scope:'READONLY_PREFLIGHT43',origin:'MOCK_REPLAY',binarySha256:BINARY,system:42,component:1,session,boot:'mock-boot',epoch:session,containerId:'a'.repeat(64),pid:123,startedAt:'MOCK_NOT_ACTUAL_PROCESS'});
export function frame(id,fields,seq,system=42){return encodeFull(id,fields,{system,component:1,seq});}
export function telemetry(id,seq,at=100){const f=structuredClone(baseline.latest[id].fields);if(id===242)f.q=[0,0,0,0];if('time_boot_ms'in f)f.time_boot_ms=at;return frame(id,f,seq);}
export function parameter(name,seq,{value,type,count=1369,index=65535,system=42}={}){const p=profile43().expected[name],v=value??(typeof p==='number'?p:140);return frame(22,{param_id:name,param_value:v,param_type:type??SCHEMA[name][0],param_count:count,param_index:index},seq,system);}
export function nonfiniteParameter(name,seq,value=NaN){let b=parameter(name,seq,{value:5});new DataView(b.buffer).setFloat32(10,value,true);const c=crc(b.subarray(1,-2),220);b[b.length-2]=c&255;b[b.length-1]=c>>8;return b;}
export function transcript(){let seq=0,t=0;const actions=[],rx=(b,at=++t)=>actions.push({kind:'RX',rawHex:hex(b),at});rx(telemetry(0,seq++,0),0);actions.push({kind:'DISCOVER',at:1},{kind:'WRITTEN',at:1});rx(telemetry(148,seq++),2);t=3;for(const id of [1,24,33,162,193,242,245])rx(telemetry(id,seq++,t));actions.push({kind:'BEGIN',at:20});t=21;for(const name of NAMES){actions.push({kind:'READ_NEXT',at:t},{kind:'WRITTEN',at:t});rx(parameter(name,seq++),t+1);t+=2;}return {profile:profile43(),context:context(),actions,seq,t,origin:'MOCK_REPLAY_ONLY_NO_NETWORK'};}
