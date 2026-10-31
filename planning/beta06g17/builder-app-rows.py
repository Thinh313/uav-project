"""One-time WIP recipe construction, exact current G15-derived snippets. No runtime."""
from pathlib import Path
import json,subprocess
p=Path('pilot/beta06g17/overlay.mjs')
assert 'STABILITY_ROWS' not in p.read_text(),'ALREADY_CONSTRUCTED'
base=subprocess.check_output(['node','--input-type=module','-e',"import fs from'node:fs';import{transform}from'./pilot/beta06g17/overlay.mjs';console.log(transform('pilot/beta06g5/app.mjs',fs.readFileSync('pilot/beta06g5/app.mjs','utf8')));"],text=True)
rows=[]
def row(a,b):
 assert base.count(a)==1,(a,base.count(a))
 rows.append({'from':a,'to':b,'count':1})
row('import{createHistoryReader}',"import{createUiTimingHook}from'../beta06g17/ui-timing-hook.mjs';\nimport{createHistoryReader}")
row('parentHostRemainingMs=null}={}){','parentHostRemainingMs=null}={}){const hostFactoryStartedMonoMs=performance.now();')
row('const historyReader=createHistoryReader(),hostLifecycle=createLifecyclePhases();let media,flight;','const historyReader=createHistoryReader(),hostLifecycle=createLifecyclePhases(),uiTiming=createUiTimingHook();let media,flight,resource,resourcePending=null;')
row('let resource,mediaSidecars=0;','let mediaSidecars=0;')
row('let closed=false,mutating=false,','let closed=false,closing=null,mutating=false,')
row("if(route==='ui-observation')return send(200,uiObservation.accept(q));","if(route==='ui-observation'){const accepted=uiObservation.accept(q);try{uiTiming.consume(uiObservation.view(),hostLifecycle.snapshot());}catch(error){campaignFailure={status:'UI_TIMING_DIAGNOSTIC_FAILED',error:String(error.message).slice(0,160),automaticRetry:false,campaignContinuationAllowed:false};throw error;}return send(200,accepted);}")
row('hostLifecycleDiagnostics:hostLifecycle.snapshot(),hostLoopDiagnostics:','hostLifecycleDiagnostics:hostLifecycle.snapshot(),uiTimingDiagnostics:uiTiming.view(),hostLoopDiagnostics:')
row('flight.setClientGuard?.(context=>{const health=','flight.setClientGuard?.(context=>{uiTiming.assertHealthy();const health=')
key='{const historyHealth=historyReader.diagnostics();'
assert base.count(key)==2
rows.append({'from':key,'to':'{uiTiming.assertHealthy();const historyHealth=historyReader.diagnostics();','count':2})
start=base.index(" async function close(reason='EXPLICIT_STOP')")
end=base.index('\n return{historyDiagnostics:',start)
oldclose=base[start:end]
newclose=""" function close(reason='EXPLICIT_STOP'){if(closing)return closing;closed=true;clearInterval(watch);clearTimeout(deadline);client.revoke(reason);payload.invalidate(reason);server.close();return closing=(async()=>{let closureError=null,uiTimingClosure=null;const failed=error=>{closureError??=error;campaignFailure??={status:'HOST_CLOSURE_EVIDENCE_FAILED',error:String(error.message).slice(0,160),automaticRetry:false,campaignContinuationAllowed:false};};try{const owned=resource??await resourcePending;await owned?.close();}catch(error){failed(error);}let evidenceFailure=null;try{await payload.settled();}catch(e){evidenceFailure=e.message;}const until=performance.now()+140000;while(flight.state().busy&&performance.now()<until)await new Promise(r=>setTimeout(r,100));if(flight.state().busy){await writeHostMetadata(path.join(out,'app-close-pending.json'),JSON.stringify({reason:'FLIGHT_OPERATION_STILL_PENDING',authorityRestored:false}),{flag:'wx'});throw Error('FLIGHT_CLOSURE_PENDING_NO_FALSE_SUCCESS');}try{if(flight.state().run){const requestedRun=flight.state().run,result=await flight.action('abort',{...flight.state().request,confirmSimulation:true});await archiveResult(result,requestedRun);}}catch(e){try{await writeHostMetadata(path.join(out,'flight-close-unknown.json'),JSON.stringify(wireError(e)),{flag:'wx'});}catch(error){failed(error);}}try{await historyReader.close();}catch(error){failed(error);}try{uiTimingClosure=await uiTiming.persist(out);}catch(error){failed(error);uiTimingClosure={status:'DIAGNOSTIC_CLOSURE_FAILED',error:String(error.message).slice(0,160),authorityEvidence:false};}try{await saveDiagnosticsClosure({hostLifecycle:hostLifecycle.snapshot(),historyWorker:historyReader.diagnostics(),uiTiming:uiTimingClosure,transport:flight.transportDiagnostics(),lifecycle:uiObservation.view().observation?.lifecycleDiagnostics??null,hostLoopDiagnostics:watchDiagnostics,media:mediaDiagnostics(),authorityEvidence:false});}catch(error){failed(error);}try{await media.close();}catch(error){failed(error);}server.close();server.closeAllConnections();try{await store.close();}catch(error){failed(error);}let uiDiagnostics=null,overlapJournal=null;try{uiDiagnostics=uiJournal.close();}catch(error){failed(error);}try{overlapJournal=journal.close();}catch(error){failed(error);}try{await writeHostMetadata(path.join(out,'app-closure.json'),JSON.stringify({at:new Date().toISOString(),reason,payloadEvidenceFailure:evidenceFailure,resourceEvidenceFailure:closureError?.message??null,closeIndexFailure:campaignFailure,overlapJournal,uiDiagnostics,authorityRestored:false,actualImages:0}),{flag:'wx'});}catch(error){failed(error);}if(closureError)throw closureError;})();} """
row(oldclose,newclose)
a=base.index('async listen(){try{validateRootLauncher(')
b=base.index('watch=setInterval',a)
oldstart=base[a:b]
rstart=oldstart.index('resource=createResourceGuard(')
resource=oldstart[rstart:]
assert resource.endswith('});')
resource=resource.replace('resource=createResourceGuard(','resource=await (resourcePending=createResourceGuard(').replace('onStop:reason=>close(reason).catch(()=>{}),','onStop:reason=>close(reason),')
resource=resource[:-3]+"}));resource.tick();if(closed){await close('STARTUP_STOPPED');throw Error('HOST_CLOSED_DURING_RESOURCE_STARTUP');}"
prefix=oldstart[:rstart].replace('async listen(){try{validateRootLauncher({controllerPid:rootControllerPid,remainingMs:parentHostRemainingMs},process.ppid);',"async listen(){try{const remaining=parentHostRemainingMs-(performance.now()-hostFactoryStartedMonoMs);validateRootLauncher({controllerPid:rootControllerPid,remainingMs:remaining},process.ppid);deadline=setTimeout(()=>close('PARENT_REMAINING_HOST_WINDOW').catch(error=>{process.exitCode=1;console.error(error.message);}),remaining);")
at=prefix.index('await media.listen();')
row(oldstart,prefix[:at]+resource+prefix[at:])
row("deadline=setTimeout(()=>close('PARENT_REMAINING_HOST_WINDOW').catch(()=>{}),parentHostRemainingMs);",'')
row('}catch(e){await historyReader.close();try{await media?.close();}',"}catch(e){try{const owned=resource??await resourcePending;await owned?.close();}catch{}try{await historyReader.close();}catch{}try{await media?.close();}")
s=p.read_text();at=s.index('export const RECIPES=')
s=s[:at]+'export const STABILITY_ROWS=Object.freeze('+json.dumps(rows,separators=(',',':'))+');\n'+s[at:]
s=s.replace('...APP_REPAIR_ROWS,SIDECAR_CONTRACT_RECIPE]','...APP_REPAIR_ROWS,SIDECAR_CONTRACT_RECIPE,...STABILITY_ROWS]')
p.write_text(s)
print(json.dumps({'status':'EXACT_STABILITY_RECIPE_CONSTRUCTED','rows':len(rows)}))
