/** Isolated composition hook. await construction BEFORE exposing the host guard.
 * Same 1s audit / caller 250ms tick, original trend and quota decision, no admission bypass.
 * A future entry must await close(); this is deliberately NOT wired into frozen G15.
 */
import fs from 'node:fs';
import path from 'node:path';
import {decideResource} from '../beta06/resource.mjs';
import {createQuotaScanner,decide,policySha256} from './quota-scanner.mjs';
export async function createResourceGuard({root,out,onStop,onObservation}){
  const scanner=createQuotaScanner();let fd;
  try{await scanner.scan();fd=fs.openSync(path.join(out,'resource-guard.jsonl'),'wx',0o600);}catch(error){await scanner.close();throw error;}
  const samples=[];let closed=false,bytes=0,lastObservation=-Infinity,inflight=null,closing=null,stopped=null,stopCallbackError=null;
  const stop=reason=>{if(stopped)return;stopped=reason;scanner.close().catch(error=>{stopCallbackError=String(error.message??error);});try{const result=onStop(stopped);if(result&&typeof result.then==='function')result.catch(error=>{stopCallbackError=String(error.message??error);});}catch(error){stopCallbackError=String(error.message??error);}};
  const audit=()=>{if(closed||inflight||stopped)return;inflight=scanner.scan().catch(error=>{if(!closed)stop('SCOPED_QUOTA_AUDIT:'+error.message);}).finally(()=>{inflight=null;});};
  const timer=setInterval(audit,1000);timer.unref();
  return{
    tick(){
      if(closed)return;if(stopped)return stop(stopped);
      const t=Number(process.hrtime.bigint())/1e6,s=fs.statfsSync(root),free=s.bavail*s.bsize,d=decideResource(samples,{t,free});samples.push({t,free});while(samples.length&&t-samples[0].t>15000)samples.shift();
      let latest;try{latest=scanner.fresh();decide(latest,{phase:'guard',freeBytes:free});}catch(error){return stop(error.message);}
      const line=Buffer.from(JSON.stringify({t:Math.round(t),free,forecast:Math.round(d.forecast),activeBytes:latest.newBytes,activeEntries:latest.newEntries,aggregateBytes:latest.aggregateBytes,historySha256:latest.historySha256,quotaAuditAgeMs:performance.now()-latest.finishedMonoMs})+'\n');
      if(bytes+line.length>4*2**20)return stop('RESOURCE_GUARD_TRACE_QUOTA');
      let offset=0,tries=0;while(offset<line.length){if(++tries>32)throw Error('GUARD_SHORT_WRITE_BOUND');const n=fs.writeSync(fd,line,offset,line.length-offset);if(!Number.isSafeInteger(n)||n<=0)throw Error('GUARD_ZERO_WRITE');offset+=n;}bytes+=line.length;
      if(d.stop)return stop(d.floorBreach?'RESOURCE_FLOOR_BREACH':'EARLY_STOP_28GIB_OR_15S_TREND');
      if(t-lastObservation>=1000){lastObservation=t;onObservation();}
    },
    diagnostics(){return{...scanner.diagnostics(),stopped,stopCallbackError,auditPending:inflight!==null,policySha256,composition:'ISOLATED_NOT_WIRED_G15'};},
    close(){if(closing)return closing;closed=true;clearInterval(timer);closing=(async()=>{let firstError=null,result;try{fs.fsyncSync(fd);}catch(error){firstError=error;}try{fs.closeSync(fd);}catch(error){firstError??=error;}try{result=await scanner.close();}catch(error){firstError??=error;}if(firstError)throw firstError;return result;})();return closing;}
  };
}
