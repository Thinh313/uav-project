/** Current real entry/overlay/worker/guard under one explicit32GiB statfs facade; no sockets. */
import fs from'node:fs';import fsp from'node:fs/promises';import{createBeta06G17}from'../../pilot/beta06g17/entry.mjs';
let owned=false;
export async function createMockApp(options){
 if(owned)throw Error('ONE_SOURCE_MOCK_APP_AT_A_TIME');const physical=fs.statfsSync('.');if(physical.bavail*physical.bsize<20*2**30)throw Error('SOURCE_MOCK_FLOOR');owned=true;
 const sync=fs.statfsSync,asyncStat=fsp.statfs;fs.statfsSync=(...args)=>{const s=sync(...args);return{...s,bavail:typeof s.bavail==='bigint'?32n*1024n**3n/BigInt(s.bsize):32*2**30/s.bsize};};fsp.statfs=async(...args)=>{const s=await asyncStat(...args);return{...s,bavail:typeof s.bavail==='bigint'?32n*1024n**3n/BigInt(s.bsize):32*2**30/s.bsize};};
 const restore=()=>{fs.statfsSync=sync;fsp.statfs=asyncStat;owned=false;};let app;
 try{app=await createBeta06G17({...options,rootControllerPid:process.ppid,parentHostRemainingMs:30000});app.media.listen=async()=>{};app.server.listen=(...args)=>{queueMicrotask(()=>args.at(-1)());return app.server;};await app.listen();return{...app,sourceMockFixture:{physicalFacadeBytes:32*2**30,actualFreeBytes:physical.bavail*physical.bsize,entryAndWorkerReal:true,socketsOpened:0,actualRuntime:false},async close(reason){try{return await app.close(reason);}finally{restore();}}};}catch(error){try{await app?.close('MOCK_STARTUP_FAILED');}finally{restore();}throw error;}
}
