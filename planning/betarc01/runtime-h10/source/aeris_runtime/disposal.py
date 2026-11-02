"""Physical cleanup of this exact simulator DAG, never mission/ground acceptance.
Called only after command admission is revoked and mission FAILED/unknown.
"""
import os,signal,subprocess,time
from pathlib import Path

def need(value,name):
 if not value:raise RuntimeError('SIM_DISPOSAL_'+name)

def stop_owned(child,*,deadline_ns,now=time.monotonic_ns,mock=False):
 """Positive original Popen owner, process group, bounded TERM/KILL and wait."""
 process=child.process
 need(mock or type(process)is subprocess.Popen,'EXACT_ORIGINAL_POPEN')
 need(type(process.pid)is int and process.pid>0 and list(process.args)==child.argv and type(child.started_ns)is int and 0<child.started_ns<=now(),'ORIGINAL_PID_START_ARGV')
 before=process.poll();signals=[]
 if before is None:
  need(now()<deadline_ns,'DEADLINE_BEFORE_SIGNAL')
  if not mock:need(os.getpgid(process.pid)==process.pid,'SOURCE_OWNED_PROCESS_GROUP')
  # Signal only this original owner's group. This is simulator disposal, never
  # the source normal AP drain and never a statement that AP had landed.
  (process.terminate if mock else lambda:os.killpg(process.pid,signal.SIGTERM))();signals.append('TERM')
  try:process.wait(timeout=max(.001,min(20,(deadline_ns-now())/1e9)))
  except subprocess.TimeoutExpired:
   need(now()<deadline_ns,'DEADLINE_BEFORE_KILL')
   (process.kill if mock else lambda:os.killpg(process.pid,signal.SIGKILL))();signals.append('KILL');process.wait(timeout=max(.001,min(5,(deadline_ns-now())/1e9)))
 code=process.poll();need(type(code)is int,'ACTUAL_CHILD_EXIT')
 return {'pid':process.pid,'startedHostNs':child.started_ns,'argv':list(child.argv),'exit':code,'signals':signals,'APGroundProven':False,'flightAcceptance':False}

def dispose_resources(resources,*,primary_failure,admission_revoked,deadline_ns):
 """Preserve the normal completed_closure untouched on every outcome."""
 need(type(primary_failure)is str and 0<len(primary_failure)<=2048 and admission_revoked is True,'FAILED_REVOKED_CONTEXT')
 need(resources.manifest.get('simulationOnly')is True,'SELECTED_SIMULATION_CANDIDATE')
 need(set(resources.children).issubset({'ap','backend'}),'ONLY_SOURCE_SIMULATION_CHILDREN')
 old_closure=resources.closure;old_complete=resources._completed_closure;rows={};errors=[]
 def step(name,fn):
  try:return fn()
  except BaseException as error:
   errors.append({'step':name,'error':type(error).__name__+':'+str(error)[:512]})
   try:resources.budget.failure(error,detail={'operation':name,'exceptionalSimulatorDisposal':True,'APGroundProven':False})
   except BaseException as storage:errors.append({'step':name+'-diagnostic','error':str(storage)[:256]})
   return None
 # The external product companion must have stopped before this API is called;
 # admission_revoked means no producer can create another command on the socket.
 for name in('ap','backend'):
  if name not in resources.children:continue
  child=resources.children[name];rows[name]=step('stop-'+name,lambda child=child:stop_owned(child,deadline_ns=deadline_ns,mock=resources.budget.mock))
  if name in resources.outputs:rows[name+'Output']=step('capture-'+name,resources.outputs[name].close)
  else:errors.append({'step':'capture-'+name,'error':'ORIGINAL_OUTPUT_SETUP_INCOMPLETE'})
 if getattr(resources,'scene_pipe',None)is not None:step('scene-observer-close',resources.close_scene)
 need(resources.closure is old_closure and resources._completed_closure is old_complete,'NORMAL_DRAIN_PROOF_MUST_NOT_CHANGE')
 physically_closed=all(type(v)is dict and type(v.get('exit'))is int for k,v in rows.items()if k in('ap','backend'))and all(not output.thread.is_alive()and output.released for output in resources.outputs.values())and set(resources.outputs)==set(resources.children)
 return {'status':'SIMULATOR_PHYSICALLY_DISPOSED_MISSION_FAILED'if physically_closed else'SIMULATOR_DISPOSAL_INCOMPLETE_OWNERS_RETAINED','primaryFailure':primary_failure,'admissionRevoked':True,'children':rows,'errors':errors,'normalCompletedClosureChanged':False,'APGroundProven':False,'sourceManagedDrainAccepted':False,'flightAcceptance':False,'automaticRetry':False}
