import assert from'node:assert/strict';import fs from'node:fs';import path from'node:path';import{pathToFileURL}from'node:url';
const OriginalDate=Date;globalThis.Date=class extends OriginalDate{constructor(...args){super(...(args.length?args:[1792464000000]));}static now(){return 1792464000000;}};globalThis.window=globalThis;const assets=path.resolve(process.argv[2]),repo=path.resolve(import.meta.dirname,'../../..');
const{SitlLink:New}=await import(pathToFileURL(path.join(assets,'direct95/vendor/services/sitl.mjs')));
const{SitlLink:Old}=await import(pathToFileURL(path.join(repo,'native/crew02/assets/direct95/vendor/services/sitl.mjs')));
let clock=0;const make=C=>{const x=new C({clock:()=>clock});x.sessionId='fixture';x.transport='connected';x.vehicle={system:42,component:1};x.socket={writable:true,write:()=>{},destroy:()=>{}};return x;};
const a=make(Old),b=make(New);let snapshots=0;
for(let i=1;i<=26000;i++){clock=i;const m={id:i%50===0?0:33,system:42,component:1,seq:i%256,receivedAt95:i,rawHex:'fixture'+i,annotation:{index:i},fields:i%50===0?{autopilot:3,type:2,base_mode:0,custom_mode:4,system_status:4}:{time_boot_ms:i,lat:108540000,lon:1068070000,relative_alt:0,alt:10000,vx:0,vy:0}};a.receive(m);b.receive(m);m.annotation.index=-1;if(i%333===0)for(const x of[a,b])x.send(0,{custom_mode:0,type:6,autopilot:8,base_mode:0,system_status:4});if(i%1000===0||i===1||i===9999||i===10001){assert.deepEqual(b.frames,a.frames);assert.deepEqual(b.journal(),a.journal());snapshots++;}}
assert.equal(b.frames.length,10000);const j=b.journal(),before=structuredClone(b.frames);j.frames[0].fields.mutated=true;assert.deepEqual(b.frames,before);
// Deliberate new diagnostic getter contract: detached ordered snapshots, not public mutable storage.
const detached=b.frames;detached.length=0;assert.deepEqual(b.frames,before);
for(const x of[a,b])x.reset();assert.deepEqual(b.frames,a.frames);assert.equal(b.frames.length,10000);
for(const x of[a,b])x.disconnect();assert.deepEqual(b.frames,a.frames);assert.equal(b.frames.length,10000);
assert.deepEqual(b.journal(),a.journal());
console.log(JSON.stringify({status:'PASS',scope:'ACTUAL_OLD_NEW_SITLLINK_NO_NETWORK',frames:26000,mixedOutgoing:true,exactBoundarySnapshots:snapshots,cloneOnAppend:true,journalDetached:true,resetDisconnectRetainHistory:true,diagnosticGetterContract:'ordered detached latest10000; raw-array identity/mutation compatibility not claimed'}));
