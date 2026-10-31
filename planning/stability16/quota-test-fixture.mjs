/** Test-only exact source seam: Worker constructor and optional local clock, no policy edits. */
import fs from 'node:fs';
import {Worker} from 'node:worker_threads';
import {createHash,randomUUID} from 'node:crypto';
const sourceURL=new URL('../../pilot/stability16/quota-scanner.mjs',import.meta.url);
export async function scannerFixture({workerURL=new URL('../../pilot/stability16/quota-worker.mjs',import.meta.url),workerData,WorkerOverride=Worker,now=null}={}){
  const original=fs.readFileSync(sourceURL,'utf8'),key='stability16.quota.fixture.'+randomUUID();
  let source=original.replace("from '../beta06g15/quota.mjs'",'from '+JSON.stringify(new URL('../../pilot/beta06g15/quota.mjs',import.meta.url).href));
  const old="const worker=new Worker(new URL('./quota-worker.mjs',import.meta.url));";
  if(source.split(old).length!==2)throw Error('EXACT_WORKER_TEST_SEAM');
  source='const fixture=globalThis[Symbol.for('+JSON.stringify(key)+')];\n'+source.replace(old,'const worker=new fixture.Worker(fixture.workerURL,{workerData:fixture.workerData});');
  if(now)source=source.split('performance.now()').join('fixture.now()');
  globalThis[Symbol.for(key)]={Worker:WorkerOverride,workerURL,workerData,now};
  try{const module=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));return{...module,sourceSHA256:createHash('sha256').update(original).digest('hex'),seam:{WorkerConstructorOnly:true,clockOverride:!!now,policyUnchanged:true}};}finally{delete globalThis[Symbol.for(key)];}
}
