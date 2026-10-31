import assert from 'node:assert/strict';
import {classify,SCHEDULE,manifest,sensorGuard,BINARY} from './contract.mjs';
const rows=[],check=(id,fn)=>{fn();rows.push({id,pass:true});};
for(const [id,args,expected]of [
 ['contact',{minimumClearanceM:-.01,guestDurationMs:2000,tailMaxSpeedMps:2},'UNSAFE_VIRTUAL_CONTACT'],
 ['touch',{minimumClearanceM:0,guestDurationMs:8000,tailMaxSpeedMps:0},'UNSAFE_VIRTUAL_CONTACT'],
 ['margin-loss',{minimumClearanceM:1.199,guestDurationMs:8000,tailMaxSpeedMps:0},'UNSAFE_CLEARANCE_LOSS'],
 ['safe-boundary',{minimumClearanceM:1.2,guestDurationMs:8000,tailMaxSpeedMps:.5},'SAFE_STOP_OBSERVED'],
 ['short-window',{minimumClearanceM:2,guestDurationMs:7999,tailMaxSpeedMps:0},'INCONCLUSIVE'],
 ['still-moving',{minimumClearanceM:2,guestDurationMs:8000,tailMaxSpeedMps:.501},'INCONCLUSIVE']])check(id,()=>assert.equal(classify(args),expected));
for(const field of ['minimumClearanceM','guestDurationMs','tailMaxSpeedMps'])for(const value of [NaN,Infinity,'1',true])check('invalid-'+field+'-'+String(value),()=>assert.throws(()=>classify({minimumClearanceM:2,guestDurationMs:8000,tailMaxSpeedMps:0,[field]:value})));
check('negative-duration',()=>assert.throws(()=>classify({minimumClearanceM:2,guestDurationMs:-1,tailMaxSpeedMps:0})));
check('balanced-orders',()=>{assert.equal(Object.keys(SCHEDULE).length,4);assert.equal(Object.values(SCHEDULE).filter(v=>v[0]==='BASELINE').length,2);assert.ok(Object.values(SCHEDULE).every(v=>new Set(v).size===2));});
const m={scope:'OWNED_REAL_SIMDROP77',binarySha256:BINARY,containerId:'a'.repeat(64),pid:1,startedAt:'boot77',boot:'boot77',target:'42/1',session:'run04'};
check('new-campaign-manifest',()=>manifest(m));
for(const [key,val]of [['scope','OWNED_REAL_SITL76'],['session','run07'],['boot','old'],['target','99/1']])check('manifest-'+key,()=>assert.throws(()=>manifest({...m,[key]:val})));
const s={target:m.target,session:m.session,boot:m.boot,frame:'BODY_FRD_METRES',clock:'HOST_MONOTONIC_MS',at:100,bootMs:200,ranges:Array(8).fill(12)};
check('sensor-valid',()=>sensorGuard(s,m,100));
for(const [key,val]of [['session','run01'],['boot','old'],['at',101],['at',-101],['frame','ENU'],['ranges',[NaN]]])check('sensor-'+key+'-'+rows.length,()=>assert.throws(()=>sensorGuard({...s,[key]:val},m,100)));
console.log(JSON.stringify({status:'PASS',passed:rows.length,total:rows.length,rows,scope:'PURE_MOCK_ONLY'}));
