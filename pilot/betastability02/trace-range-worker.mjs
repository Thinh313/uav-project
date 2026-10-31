import{parentPort,workerData}from'node:worker_threads';import{serializeTraceRange}from'./trace-verify.mjs';
try{parentPort.postMessage({ok:true,result:serializeTraceRange(workerData.root,workerData.start,workerData.end,{receipt:workerData.receipt})});}catch(e){parentPort.postMessage({ok:false,error:e.message});}
