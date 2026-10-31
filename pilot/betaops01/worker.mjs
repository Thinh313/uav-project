import{parentPort,workerData}from'node:worker_threads';import{verify}from'./verify.mjs';
try{parentPort.postMessage({result:await verify(workerData.bytes)});}catch(e){parentPort.postMessage({error:String(e.message).slice(0,200)});}
