/** Read-only G15 measurement. Instrumentation is test-only, never loaded by the candidate. */
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {ROOT,POLICY,POLICY_PATH,scan,policySha256} from '../../pilot/beta06g15/quota.mjs';
const out=path.join(ROOT,'evidence/stability16/builder-quota-diagnosis01.json');
const disk=await fsp.statfs(ROOT);if(disk.bavail*disk.bsize<20*2**30)throw Error('DISK_FLOOR');
const sha=b=>createHash('sha256').update(b).digest('hex'), hpath=path.join(ROOT,POLICY.history.path);
const clocked=fn=>{const t=performance.now(),value=fn();return {value,ms:performance.now()-t};};
const read=clocked(()=>fs.readFileSync(hpath)), hash=clocked(()=>sha(read.value)), parse=clocked(()=>JSON.parse(read.value));
const metric={};const originals={};
for(const name of ['opendir','lstat','readFile']){originals[name]=fsp[name];metric[name]={calls:0,elapsedMs:0,bytes:0};fsp[name]=async(...args)=>{const t=performance.now();try{const r=await originals[name](...args);if(name==='readFile')metric[name].bytes+=r.length;return r;}finally{metric[name].calls++;metric[name].elapsedMs+=performance.now()-t;}};}
const results=[];
try{for(const verifyHashes of [false,true]){for(const x of Object.values(metric))Object.assign(x,{calls:0,elapsedMs:0,bytes:0});const t=performance.now(),cpu=process.cpuUsage();let last=t,maxLag=0,ticks=0;const timer=setInterval(()=>{const now=performance.now();maxLag=Math.max(maxLag,now-last-5);last=now;ticks++;},5);try{const u=await scan({verifyHashes});results.push({verifyHashes,status:'COMPLETE',wallMs:performance.now()-t,reportedDurationMs:u.durationMs,usage:{newEntries:u.newEntries,newBytes:u.newBytes,aggregateEntries:u.aggregateEntries,aggregateBytes:u.aggregateBytes},maxTimerLagMs:maxLag,ticks,cpuMicroseconds:process.cpuUsage(cpu),io:structuredClone(metric)});}catch(e){results.push({verifyHashes,status:'REFUSED',error:e.message,wallMs:performance.now()-t,maxTimerLagMs:maxLag,ticks,cpuMicroseconds:process.cpuUsage(cpu),io:structuredClone(metric)});}finally{clearInterval(timer);}}}finally{for(const[name,fn]of Object.entries(originals))fsp[name]=fn;}
const report={schema:'STABILITY16_QUOTA_DIAGNOSIS_V1',kind:'READ_ONLY_REAL_FILESYSTEM_NOT_RUNTIME',policySha256,source:{path:'pilot/beta06g15/quota.mjs',sha256:sha(fs.readFileSync(path.join(ROOT,'pilot/beta06g15/quota.mjs')))},history:{path:POLICY.history.path,bytes:read.value.length,pinnedSHA:POLICY.history.sha256,actualSHA:hash.value,entries:Object.keys(parse.value.entries).length,readSyncMs:read.ms,hashSyncMs:hash.ms,parseSyncMs:parse.ms},results,limits:{historyLoadExcludedFromOriginalDuration:true,ioElapsedIncludesAwaitNotExclusiveCPU:true,observedG15LatencyCause:'UNKNOWN',suspensionStaleRefusal:'PRESERVED'},freeBytes:disk.bavail*disk.bsize};
fs.mkdirSync(path.dirname(out),{recursive:true});const fd=fs.openSync(out,'wx',0o600);try{fs.writeFileSync(fd,JSON.stringify(report,null,2)+'\n');fs.fsyncSync(fd);}finally{fs.closeSync(fd);}console.log(JSON.stringify(report));
