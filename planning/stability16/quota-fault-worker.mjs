/** Owned fixture only: delay the exact pinned inventory read, then execute the real worker. */
import fs from 'node:fs';
import {workerData} from 'node:worker_threads';
import {POLICY,ROOT} from '../../pilot/beta06g15/quota.mjs';
import path from 'node:path';
const original=fs.readFileSync,target=fs.statSync(path.join(ROOT,POLICY.history.path));let hit=false;
fs.readFileSync=function(p,...args){const s=typeof p==='number'?fs.fstatSync(p):fs.statSync(p);if(!hit&&s.dev===target.dev&&s.ino===target.ino){hit=true;Atomics.add(new Int32Array(workerData.hits),0,1);if(workerData.mode==='cpu'){const until=performance.now()+workerData.delayMs;while(performance.now()<until){/* deterministic main/worker CPU contrast */}}else Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,workerData.delayMs);}return original.call(this,p,...args);};
await import('../../pilot/stability16/quota-worker.mjs');
