import{workerData}from'node:worker_threads';import fs from'node:fs';import path from'node:path';
if(!path.resolve(workerData.historyRoot).includes('/evidence/betastability02/archive-correction02-tests'))throw Error('TEST_ONLY_PATH');
fs.mkdirSync(workerData.historyRoot,{recursive:true});fs.writeFileSync(path.join(workerData.historyRoot,'.pending-fault-injection'),'retained pending fixture',{flag:'wx'});process.exit(7);
