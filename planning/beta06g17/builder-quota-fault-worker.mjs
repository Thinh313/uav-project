/** Owned mock only: second complete inventory read stalls1250ms, then exact G17 worker continues. */
import fs from'node:fs';import path from'node:path';import{workerData}from'node:worker_threads';import{ROOT,POLICY}from'../../pilot/beta06g17/quota.mjs';
const target=fs.statSync(path.join(ROOT,POLICY.history.path)),original=fs.readFileSync;let reads=0;
fs.readFileSync=function(p,...args){const s=typeof p==='number'?fs.fstatSync(p):fs.statSync(p);if(s.dev===target.dev&&s.ino===target.ino&&++reads===2){Atomics.add(new Int32Array(workerData.hits),0,1);Atomics.wait(new Int32Array(new SharedArrayBuffer(4)),0,0,1250);}return original.call(this,p,...args);};
await import('../../pilot/beta06g17/quota-worker.mjs');
