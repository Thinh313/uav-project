/** Worker isolation only; exact frozen inventory and admission algorithms remain in G17. */
import {Worker} from 'node:worker_threads';
import {POLICY,policySha256,decide} from './quota.mjs';
export {POLICY,policySha256,decide};
// This adapter is explicitly scoped to the immutable G17 inventory. A future
// campaign must verify a new tuple; it cannot silently reuse these constants.
export const PINNED_BASIS=Object.freeze({policySha256:'9b0ae2e0cbb8696db8b18c47abcfeff90c643c0b82b3d91f20477974340cfde8',historySha256:'385862d681127ff6645b8c14efb3fa8bf21cbb5fffb2fd080d469982a7f8276b',historicalEntries:8527,historicalBytes:314139839});
function assertBasis(){if(policySha256!==PINNED_BASIS.policySha256||POLICY.history.sha256!==PINNED_BASIS.historySha256)throw Error('QUOTA_PINNED_G17_BASIS_REQUIRED');}
const exact=(x,keys)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).sort().join()===keys.sort().join();
const integer=n=>Number.isSafeInteger(n)&&n>=0;
const duration=n=>typeof n==='number'&&Number.isFinite(n)&&n>=0;
function immutable(x){if(x&&typeof x==='object'){Object.freeze(x);for(const v of Object.values(x))immutable(v);}return x;}
export function validateResult(text,job){
  assertBasis();
  if(typeof text!=='string'||Buffer.byteLength(text)>64*1024)throw Error('QUOTA_RESULT_BOUND');
  const r=JSON.parse(text);
  if(exact(r,['id','error'])){if(r.id!==job.id||typeof r.error!=='string'||r.error.length>512)throw Error('QUOTA_ERROR_CONTEXT');throw Error('QUOTA_SCAN:'+r.error);}
  if(!exact(r,['id','policySha256','historySha256','verifyHashes','workerDurationMs','usage'])||r.id!==job.id||r.policySha256!==policySha256||r.historySha256!==POLICY.history.sha256||r.verifyHashes!==job.verifyHashes||!duration(r.workerDurationMs)||r.workerDurationMs>POLICY.scanner.cycleMs)throw Error('QUOTA_RESULT_CONTEXT');
  const u=r.usage;
  if(!exact(u,['counts','apRuns','capacity','newEntries','newBytes','historicalEntries','historicalBytes','aggregateEntries','aggregateBytes','finishedAt','finishedMonoMs','durationMs','slices','policySha256','historySha256'])||u.policySha256!==policySha256||u.historySha256!==POLICY.history.sha256)throw Error('QUOTA_USAGE_SCHEMA');
  if(!exact(u.counts,Object.keys(POLICY.categories)))throw Error('QUOTA_COUNT_KEYS');
  for(const v of Object.values(u.counts))if(!exact(v,['entries','bytes'])||!integer(v.entries)||!integer(v.bytes))throw Error('QUOTA_COUNT_BOUND');
  if(!u.apRuns||Array.isArray(u.apRuns)||typeof u.apRuns!=='object'||Object.keys(u.apRuns).length>4)throw Error('QUOTA_AP_BOUND');
  for(const[k,v]of Object.entries(u.apRuns))if(!/^s[a-f0-9]{20}$/.test(k)||!exact(v,['entries','bytes','stateEntries','captureResults','normalEntries'])||!Object.values(v).every(integer))throw Error('QUOTA_AP_SCHEMA');
  if(!exact(u.capacity,['sitlRequests','hostProcesses','basis'])||!integer(u.capacity.sitlRequests)||u.capacity.sitlRequests!==Object.keys(u.apRuns).length||!integer(u.capacity.hostProcesses)||u.capacity.hostProcesses>2||u.capacity.basis!=='RETAINED_NAMESPACE_CAPACITY_ONLY_NOT_AUTHORITY_OR_CLOCK')throw Error('QUOTA_CAPACITY_SCHEMA');
  for(const k of ['newEntries','newBytes','historicalEntries','historicalBytes','aggregateEntries','aggregateBytes','slices'])if(!integer(u[k]))throw Error('QUOTA_TOTAL_BOUND');
  for(const k of ['finishedAt','finishedMonoMs','durationMs'])if(!duration(u[k]))throw Error('QUOTA_TIME_SCHEMA');
  if(u.historicalEntries!==PINNED_BASIS.historicalEntries||u.historicalBytes!==PINNED_BASIS.historicalBytes||u.aggregateEntries>POLICY.scanner.maxEntries||u.slices>Math.ceil(POLICY.scanner.maxEntries/POLICY.scanner.sliceEntries)||u.aggregateEntries!==u.historicalEntries+u.newEntries||u.aggregateBytes!==u.historicalBytes+u.newBytes||u.durationMs>POLICY.scanner.cycleMs)throw Error('QUOTA_TOTAL_CONTEXT');
  if(Object.values(u.counts).reduce((n,c)=>n+c.entries,0)!==u.newEntries||Object.values(u.counts).reduce((n,c)=>n+c.bytes,0)!==u.newBytes)throw Error('QUOTA_TOTAL_MISMATCH');
  return r;
}
export function createQuotaScanner(){
  assertBasis();
  let closed=false,fatal=null,pending=null,latest=null,nextId=0,terminationCode=null;
  const worker=new Worker(new URL('./quota-worker.mjs',import.meta.url));
  let termination=null;
  const terminate=()=>termination??=(worker.terminate().then(code=>{if(Number.isInteger(code))terminationCode=code;return terminationCode;}));
  function poison(error){if(closed)return;fatal??=String(error.message??error);latest=null;if(pending){clearTimeout(pending.timer);pending.reject(Error(fatal));pending=null;}void terminate();}
  worker.on('error',poison);
  worker.on('exit',code=>{if(Number.isInteger(code))terminationCode=code;if(!closed)poison(Error('QUOTA_WORKER_EXIT:'+code));});
  worker.on('message',text=>{
    if(closed||fatal)return;
    if(!pending)return poison(Error('QUOTA_UNSOLICITED_RESULT'));
    const job=pending,now=performance.now();
    try{
      if(now<job.start||now-job.start>POLICY.scanner.cycleMs)throw Error('QUOTA_PARENT_CYCLE_DEADLINE');
      const r=validateResult(text,job);
      // Worker absolute stamps are never used as parent freshness anchors.
      // Dispatch is a conservative parent-domain lower bound on completion. A delayed
      // message never grants a fresh 15 seconds; acceptedAt is diagnostics only.
      latest=immutable({...r.usage,finishedMonoMs:job.start,acceptedAtMonoMs:now,auditStartedMonoMs:job.start,auditElapsedMs:now-job.start,workerDurationMs:r.workerDurationMs,clockDomain:'PARENT_NODE_PERFORMANCE_NOW_MS',verifyHashes:job.verifyHashes});
      clearTimeout(job.timer);pending=null;job.resolve(latest);
    }catch(error){poison(error);}
  });
  function assertOpen(){if(closed)throw Error('QUOTA_SCANNER_CLOSED');if(fatal)throw Error(fatal);}
  return{
    scan({verifyHashes=false}={}){
      try{assertOpen();if(typeof verifyHashes!=='boolean')throw Error('QUOTA_VERIFY_HASHES_BOOLEAN');if(pending)throw Error('QUOTA_SCAN_BUSY');}catch(error){return Promise.reject(error);}
      return new Promise((resolve,reject)=>{const job={id:++nextId,verifyHashes,start:performance.now(),resolve,reject,timer:null};pending=job;job.timer=setTimeout(()=>poison(Error('QUOTA_PARENT_CYCLE_DEADLINE')),POLICY.scanner.cycleMs);try{worker.postMessage({id:job.id,verifyHashes,policySha256});}catch(error){poison(error);}});
    },
    fresh(){assertOpen();const now=performance.now();if(!latest||now<latest.finishedMonoMs||now-latest.finishedMonoMs>POLICY.scanner.staleMs){poison(Error('SCOPED_QUOTA_STALE_FAIL_CLOSED'));throw Error(fatal);}return latest;},
    diagnostics(){return{closed,fatal,pending:pending!==null,accepted:latest!==null,terminationCode,cycleMs:POLICY.scanner.cycleMs,staleMs:POLICY.scanner.staleMs,queueCapacity:0,workers:1,policySha256};},
    async close(){if(!closed){closed=true;latest=null;if(pending){clearTimeout(pending.timer);pending.reject(Error('QUOTA_SCAN_CANCELED_ON_CLOSE'));pending=null;}}await terminate();return{closed:true,terminationCode};}
  };
}
