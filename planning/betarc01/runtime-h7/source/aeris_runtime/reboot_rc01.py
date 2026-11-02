"""Separately admitted read-only AP/backend boot context after old fault drain.
No Activity, companion, native observation fabrication, input writer or grant.
Old failed context stays failed; this is not physical preflight or retention.
"""
from pathlib import Path
import hashlib,json,time
from .rc01 import need
from .lifecycle import Context
from .mission16 import common_bindings
from .acceptance_rc01 import original_ref
from .launch import SimulationLauncher
from .telemetry import CommittedTransportReader
from .paths import repository

def old_fault(path,digest,manifest,candidate):
 p=Path(path).absolute();scope=repository()/'evidence/betarc01';need(p.is_relative_to(scope)and p.is_file()and not any(q.is_symlink()for q in[p,*p.parents])and p.stat().st_size<=32768,'READONLY_OLD_FAULT_SCOPE');raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==digest,'READONLY_OLD_FAULT_SHA');v=json.loads(raw);need(v.get('format')=='aeris-betarc01-root-old-ap-fault-acceptance'and v.get('version')==1 and v.get('status')=='ROOT_COLD_VERIFIED_OLD_AP_CONTEXT_FAILED_DRAINED'and v.get('candidateSHA256')==candidate and v.get('commonBindings')==common_bindings(manifest)and v.get('kind')=='AP_REBOOT'and v.get('allOldActorsClosed')is True and v.get('oldFailurePreserved')is True and v.get('authorityRestorable')is False,'READONLY_OLD_CONTEXT_COLD_PREREQUISITE');need(Context(**v['context']).value()==v['context'],'READONLY_OLD_CONTEXT_TYPED');refs=v.get('originalEvidence');need(type(refs)is list and 4<=len(refs)<=12 and {'fault-request','old-ap-stage','owner-terminal','guardian'}<=set(r['role']for r in refs),'READONLY_OLD_FAULT_ORIGINAL_ROLES');[original_ref(r,scope)for r in refs];return v

def check_probe(owner):
 owner.check_deadline();c=owner.case;need(c is not None and c.get('readOnlyBootProbeRC01')is True and owner.root.name in('r301','r302')and c['companion']is None and c['writer'].server is None and c['writer'].thread is None and c['writer'].inflight is None and c['native'].latest is None and c['device'].observer.process is None,'READONLY_NO_ACTOR_OR_COMMAND_INGRESS')
 if c['monitor']._never_started():owner.budget.require_real_actor();owner.health();need(owner.guardian.process.poll()is None,'READONLY_GUARDIAN_PREPARATION_ALIVE');owner.guardian.output.check()
 else:c['monitor'].check()
 for name in c['resources'].children:c['resources'].require_alive(name)
 state=c['root']/'raw/transport-state.json'
 if state.exists():
  raw=state.read_bytes();need(len(raw)<=65536,'READONLY_TRANSPORT_PROJECTION_BOUND');return c['reader'].advance(json.loads(raw))
 return False

def start_probe(owner,image,prior,digest):
 c=owner.case;need(owner.root.name in('r301','r302')and c is not None and not c['APStarted']and not c['resources'].children and c['companion']is None and c['native'].latest is None,'READONLY_ONE_FRESH_AP_CONTEXT');need(c['context']['boot']!=prior['context']['boot']and c['context']['run']!=prior['context']['run'],'READONLY_NO_OLD_BOOT_REUSE');c['readOnlyBootProbeRC01']=True;c['config']['wipeState']=False;c['config']['readOnlyBootProbeRC01']={'format':'aeris-readonly-ap-boot-probe-rc01','version':1,'context':dict(c['context']),'priorContext':prior['context'],'oldFaultSHA256':digest,'stateMode':'COLD_CONFIG_NO_EEPROM_OR_MISSION_RETENTION_CLAIM','oldStateUntouched':True,'authorityRestorable':False,'nativeActivityStarted':False};c['reader']=CommittedTransportReader(c['root']/'raw/transport-journal',c['context']);c['monitor'].start();launcher=SimulationLauncher(c['config'],c['root']/'simulation',image=image,query=c['device'].host_query,check_live=lambda:check_probe(owner),budget=owner.budget);c['launcher']=launcher;receipt=launcher(c['resources'],owner.campaign.deadline_ns);c['APStarted']=True;c['phase']='READ_ONLY_NEW_AP_OBSERVATION';owner.event('READ_ONLY_NEW_AP_CONTEXT_READY',{'priorContext':prior['context'],'newContext':c['context'],'actualAPLaunch':receipt,'controlAuthorityGranted':False,'nativeActivityStarted':False,'missionOrEEPROMRetentionProven':False});return receipt

def no_native_ingress(reader):
 need(not reader.native_connection_seen and not reader.native_bytes_seen and not reader.pending_forward_seen and not reader.forward_unknown and reader.forward_intent is None and not any(reader.forward_pending.values()),'READONLY_ORIGINAL_NATIVE_CONNECTION_RX_FORWARD_MUST_BE_ABSENT')
 need(reader.witness.prefix=={'sequence':reader.seq,'sha256':reader.head},'READONLY_COMPLETE_COMMITTED_PREFIX')
 return dict(reader.witness.prefix)

def observe_probe(owner,prior,*,seconds=12):
 c=owner.case;end=time.monotonic_ns()+int(seconds*1e9)
 while time.monotonic_ns()<end:
  complete=check_probe(owner);w=c['reader'].witness;h=w.h;p=w.p
  if complete:no_native_ingress(c['reader'])
  if complete and h is not None and p is not None and h.get('armed')is False and type(p.get('bootMs'))is int and p['bootMs']>=0 and all(0<=time.monotonic_ns()-q['hostNs']<=1_500_000_000 for q in(h,p))and c['reader'].frames>0:
   actual={'format':'aeris-betarc01-readonly-new-ap-observation','version':1,'candidateSHA256':owner.digest,'oldContext':prior['context'],'newContext':dict(c['context']),'originalCRCHeartbeat':dict(h),'originalCRCGlobalPositionWithBootMs':dict(p),'observedActualAPBootMs':p['bootMs'],'committedTransportPrefix':dict(w.prefix),'actualAPLaunch':c['launcher'].receipt,'oldFailurePreserved':True,'nativeActivityStarted':False,'nativeInputSourceStarted':False,'MAVLinkApplicationTXBytes':0,'nativeIngressAbsenceMeaning':'COMPLETE_COMMITTED_PREFIX_NO_CONNECTION_RX_PENDING_OR_FORWARD','nativeConnectionEverSeen':False,'nativeRXEverSeen':False,'pendingForwardEverSeen':False,'flightAuthorityGranted':False,'physicalPreflightAccepted':False,'missionRetentionProven':False,'EEPROMRetentionProven':False,'stateMode':'COLD_CONFIG_NO_EEPROM_OR_MISSION_RETENTION_CLAIM','observedAPBootTimes':dict(w.boot_by_id),'bootClockRegressionClaimed':False,'requiresIndependentOldNewStageAndClockReplay':True,'flightAcceptance':False};owner.write('read-only-new-ap-observation.json',actual);return actual
  time.sleep(.1)
 raise TimeoutError('READONLY_ACTUAL_NEW_AP_CRC_HEARTBEAT_AND_BOOTCLOCK_REQUIRED_NOT_PID_OR_LABEL')
