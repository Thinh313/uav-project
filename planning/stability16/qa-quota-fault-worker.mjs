/** QA-only copy-on-read corruption or owned thread exit. Never modifies the pinned file. */
import fs from'node:fs';import path from'node:path';import{workerData}from'node:worker_threads';
import{ROOT,POLICY}from'../../pilot/beta06g15/quota.mjs';
if(workerData.mode==='exit')process.exit(17);
const target=fs.statSync(path.join(ROOT,POLICY.history.path)),original=fs.readFileSync;
fs.readFileSync=function(p,...args){const s=typeof p==='number'?fs.fstatSync(p):fs.statSync(p),data=original.call(this,p,...args);if(s.dev===target.dev&&s.ino===target.ino){Atomics.add(new Int32Array(workerData.hits),0,1);const copy=Buffer.from(data);copy[0]^=1;return copy;}return data;};
await import('../../pilot/stability16/quota-worker.mjs');
