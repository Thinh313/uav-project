/** Proposal: one bounded, terminal worker operation. No authority and no retry. */
import{parentPort,workerData}from'node:worker_threads';import fs from'node:fs';import path from'node:path';import{fileURLToPath}from'node:url';import{performance}from'node:perf_hooks';
const ROOT=fileURLToPath(new URL('../../',import.meta.url)),base=path.join(ROOT,'evidence/betastability02')+path.sep;
const {History}=await import(new URL('pilot/betastability02/history.mjs',new URL('../../',import.meta.url)));
const {makePackage}=await import(new URL('pilot/betastability02/package.mjs',new URL('../../',import.meta.url)));
const {qualifyRun}=await import(new URL('pilot/betastability02/auto-video.mjs',new URL('../../',import.meta.url)));
const {serializeTraceRange}=await import(new URL('pilot/betastability02/trace-verify.mjs',new URL('../../',import.meta.url)));
const {guardWrite}=await import(new URL('pilot/betastability02/resource.mjs',new URL('../../',import.meta.url)));
const scoped=p=>{const v=path.resolve(p??'');if(!v.startsWith(base))throw Error('ARCHIVE_WORKER_PATH_SCOPE');return v;};
const spans=[];function span(kind,fn){const start=performance.now();try{return fn();}finally{spans.push({kind,durationMs:performance.now()-start});}}
const regular=(p,max)=>{const s=fs.lstatSync(p);if(!s.isFile()||s.isSymbolicLink()||s.size>max)throw Error('ARCHIVE_WORKER_INPUT_BOUND');return s;};
try{
 const{operation,args,historyRoot}=workerData;if(!['archive','read','list','quality'].includes(operation))throw Error('ARCHIVE_WORKER_OPERATION');
 const history=new History(scoped(historyRoot));let result;
 if(operation==='archive'){
  const root=scoped(args.root),workspaceRoot=scoped(args.workspaceRoot),r=args.review;
  if(!r||!(/^[sm][a-f0-9]{20}$/).test(r.run)||r.authorityRestored!==false)throw Error('ARCHIVE_REVIEW_SCOPE');
  const runDir=path.join(root,r.source==='OBSERVED_OWNED_SITL'?'flight/runs':'session',r.run);regular(path.join(runDir,'raw.jsonl'),16*2**20);regular(path.join(runDir,'review.json'),2**20);regular(path.join(workspaceRoot,'journal.jsonl'),16*2**20);
  if(r.accepted&&r.source==='OBSERVED_OWNED_SITL'){
   try{const quality=span('qualifyRun',()=>qualifyRun(root,r)),p=path.join(root,'auto-video-qualification-'+r.run+'.json');
    if(!fs.existsSync(p)){guardWrite();fs.writeFileSync(p,JSON.stringify(quality,null,2),{flag:'wx'});}
    else if(JSON.stringify(JSON.parse(fs.readFileSync(p)))!==JSON.stringify(quality))throw Error('QUALIFICATION_INPUT_CHANGED');
   }catch(e){const p=path.join(root,r.run+'-video-incomplete.json');if(!fs.existsSync(p)){guardWrite();fs.writeFileSync(p,JSON.stringify({run:r.run,error:e.message,video:'NOT_CHECKED',authorityRestored:false}),{flag:'wx'});}}
  }
  if(args.trace){
   const t=args.trace;if(!Number.isSafeInteger(t.start)||!Number.isSafeInteger(t.end)||t.start<1||t.end<t.start||typeof t.receipt!=='string'||!/^[a-z0-9.-]+$/.test(t.receipt))throw Error('ARCHIVE_TRACE_DESCRIPTOR');
   const range=span('traceRange',()=>serializeTraceRange(path.join(root,'media/full-trace'),t.start,t.end,{receipt:t.receipt})),p=path.join(root,'trace-'+r.run+'.jsonl.gz');
   if(!fs.existsSync(p)){guardWrite();span('traceWrite',()=>fs.writeFileSync(p,range.bytes,{flag:'wx'}));}
   else if(!fs.readFileSync(p).equals(range.bytes))throw Error('TRACE_RANGE_IMMUTABLE_COLLISION');
  }
  const pkg=span('makePackage',()=>makePackage(root,r,{workspaceRoot}));result=span('history.archive',()=>history.archive(pkg.bytes));
 }else if(operation==='read'){
  result=span('history.read',()=>history.read(args.run));
 }else if(operation==='list')result=span('history.list',()=>history.list());
 else{
  const archived=span('history.read',()=>history.read(args.run)),pkg=span('packageJSON',()=>JSON.parse(archived.bytes)),file=pkg.files['media/auto-video-qualification.json'];
  result={run:args.run,result:file?JSON.parse(Buffer.from(file.base64,'base64')):null,readiness:{navigation:pkg.review.accepted?'PASS':'INCOMPLETE',media:archived.verification.videoQuality?.status??'NOT_CHECKED',trace:archived.verification.traceCoverage?.status??'NOT_CHECKED',integrity:'VERIFIED_CHAIN_NOT_SOURCE_AUTHENTICATED'}};
 }
 if(result?.bytes){const bytes=Uint8Array.from(result.bytes);parentPort.postMessage({ok:true,result:{...result,bytes},spans},[bytes.buffer]);}
 else parentPort.postMessage({ok:true,result,spans});
}catch(e){parentPort.postMessage({ok:false,error:String(e.message).slice(0,500),spans,automaticRetry:false,authorityRestorable:false});}
finally{parentPort.close();}
