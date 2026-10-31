"""Actual public Android journey. Root supplies simulator actors, never intents.
This driver contains no flight HTTP POST or shell MAVLink escape hatch.
"""
from aeris_runtime.public_ui_workload import PublicUIDriver,need
import json,re,time

def run(owner,case,check):
 ui=PublicUIDriver(owner,case,check);case['uiDriver']=ui
 ui.bind_geometry();ui.observation()
 ui.tap('workspace');ui.tap('sitl-fixture')
 ui.wait_ui(lambda o:o.get('currentView')=='plan'and o.get('modal')is False and o.get('workbenchBusy')is False and o.get('planSha256')is None,description='FIXTURE_MODEL_AND_MODAL')
 ui.checked('datum');ui.tap('compile')
 ui.wait_ui(lambda o:o.get('currentView')=='plan'and o.get('modal')is False and o.get('workbenchBusy')is False and type(o.get('planSha256'))is str and re.fullmatch('[a-f0-9]{64}',o['planSha256'])is not None,description='COMPILE_COMPLETED')
 ui.tap('workspace');saved_initial=ui.save_workspace();ui.tap('close-modal');ui.tap('next-preflight');ui.checked('consent');ui.tap('approve')
 if case['plannedSeconds']==760:ui.choose('video-measure-profile','Dài · tối đa 12 phút')
 ui.tap('b-activate');ui.checked('b-home');ui.tap('b-connect');ui.wait(lambda s:bool(s['flight']['run']),seconds=15,description='CONNECTED')
 ui.tap('b-preflight');ui.wait(lambda s:s['flight']['preflight']and s['flight']['preflight']['ready'],seconds=10,description='TYPED_PREFLIGHT')
 ui.tap('b-grant');ui.tap('b-upload');ui.wait(lambda s:bool(s['flight']['live'].get('readback63')),seconds=10,description='MISSION_READBACK')
 ui.tap('b-discover');ui.tap('b-select');ui.tap('b-payload-grant')
 ui.wait(lambda s:s.get('payloadCamera')is not None,seconds=5,description='PAYLOAD_CAMERA_READBACK')
 # Source browser is opened once by Root before ARM with explicit auto-source=1.
 # It may wait for a qualified camera, but must never retry a failed publisher.
 ui.tap('video-start');ui.target('video-measure',seconds=60);ui.tap('video-measure')
 ui.tap('b-preflight');ui.tap('b-arm');ui.wait(lambda s:s['flight']['live']['stage']=='ARMED_HOME_REVIEW',seconds=10,description='POST_ARM_HOME')
 ui.tap('b-home-refresh');ui.checked('b-home-after');ui.tap('b-auto')
 ui.wait(lambda s:bool(s['flight']['live']['armed'])and(s['flight'].get('latestPosition')or{}).get('relativeHomeM',0)>=3,seconds=25,description='AIRBORNE_AUTO')
 ui.tap('video-capture');ui.tap('b-hold');ui.wait(lambda s:(s['flight'].get('manual')or{}).get('phase')=='HELD',seconds=5,description='HELD')
 ui.tap('b-manual-grant');x,y,w=ui.right_pad();ui.pointer_event('DOWN',x,y)
 ui.wait(lambda s:(s['flight'].get('manual')or{}).get('phase')=='MANUAL',seconds=5,description='GENUINE_NEUTRAL_HANDSHAKE')
 if case['plannedSeconds']!=760:
  # One small genuine pitch excursion in the short gate, then neutral. This
  # is Android-injected touch, not a physical-Hera HID or tracking claim.
  before=ui.state()['flight'].get('latestPosition');moved_y=round(y-w*.22);ui.pointer_event('MOVE',x,moved_y);until=time.monotonic_ns()+1_500_000_000
  while time.monotonic_ns()<until:
   check();state=ui.state();need((state['flight'].get('manual')or{}).get('phase')=='MANUAL','SHORT_MANEUVER_AUTHORITY');time.sleep(.2)
  ui.pointer_event('MOVE',x,y);after=ui.state()['flight'].get('latestPosition');ui.event('GENUINE_ANDROID_SHORT_PITCH_EXCURSION',{'beforePosition':before,'afterPosition':after,'padCenter':[x,y],'actualMove':[x,moved_y],'seconds':1.5,'executionProven':False,'requiresColdOriginalRCAndFDMJoin':True})
 duration=600 if case['plannedSeconds']==760 else 5;start=time.monotonic_ns();end=start+duration*1_000_000_000
 # A genuine held pointer is sampled by Android at unchanged20Hz. This loop
 # neither invents samples nor refreshes a clock/authority from host time.
 while time.monotonic_ns()<end:
  check();native=ui.native();s=ui.state();m=s['flight'].get('manual')or{}
  need(m.get('phase')=='MANUAL'and m.get('failure')is None,'MANUAL_CONTINUITY');need(native['input']['failed']is False and native['input']['configured']is True,'NATIVE_INPUT_SOURCE_CONTINUITY');time.sleep(.5)
 ui.pointer_event('UP',x,y);ui.wait(lambda s:(s['flight'].get('manual')or{}).get('phase')=='HELD',seconds=5,description='RELEASE_TO_HOLD')
 ui.event('MANUAL_SOURCE_INTERVAL',{'startedHostNs':start,'endedHostNs':time.monotonic_ns(),'requiredDurationSeconds':duration,'source':'GENUINE_ANDROID_INJECTED_TOUCH_NOT_HERA_HID','inputRateHz':20,'freshnessMs':250,'leaseMs':200,'noHostGeneratedInputSamples':True})
 # A fresh explicit AUTO action is distinct from manual motion authority.
 # The previous RC lease remains retired; no touch is held during this tap.
 ui.tap('b-manual-release')
 ui.wait(lambda s:s['flight']['completion']['complete']is True,seconds=65,description='ORIGINAL_AUTO_COMPLETION')
 ui.target('video-save',seconds=95);ui.tap('video-save');ui.tap('b-close');s=ui.wait(lambda s:bool(s['reviews']),seconds=8,description='DURABLE_REVIEW');need(s['reviews'][-1]['accepted']is True,'NOMINAL_REVIEW_ACCEPTED')
 # Qualified video is checked only after the genuine Root CRC interval and
 # closed-review join exists; querying earlier is not retried as if a PASS.
 until=time.monotonic_ns()+10_000_000_000
 while case.get('intervalProof')is None and time.monotonic_ns()<until:
  check();need(case.get('intervalError')is None,'ROOT_VIDEO_INTERVAL_FAILED');time.sleep(.05)
 need(case.get('intervalProof')is not None,'ROOT_VIDEO_INTERVAL_NOT_READY');ui.tap('beta-quality');qualification=ui.wait(lambda s:s.get('latestVideoQualification')is not None,seconds=10,description='VIDEO_QUALIFICATION_RESULT');need(qualification['latestVideoQualification'].get('status')=='PASS','ORIGINAL_VIDEO_QUALIFICATION_NOT_PASS')
 # Public replay must load verified bytes and expose its real play/pause state;
 # no host-side direct player call or fabricated display sample is used.
 ui.tap('review-replay-'+s['reviews'][-1]['run']);ui.tap('replay-play');ui.target('replay-pause');time.sleep(1);ui.tap('replay-pause');ui.target('replay-play');ui.event('PUBLIC_REVIEW_REPLAY_PLAY_PAUSE',{'run':s['reviews'][-1]['run'],'source':'GENUINE_ANDROID_UI_EVENTS','positionAccuracyIndependentlyAccepted':False})
 # Explicit native workspace commit, then real Android process death/reload.
 ui.tap('workspace');saved_final=ui.save_workspace();ui.tap('close-modal');old_pid=ui.probe.pid;old_epoch=ui.probe.process_epoch
 original_closed=ui.native(True)['input'];need(original_closed.get('closed')is True and original_closed.get('configured')is False and original_closed.get('pending')is False and original_closed.get('failed')is False and original_closed.get('journal',{}).get('durablyDrained')is True,'ORIGINAL_PRE_RESTART_INPUT_GENERATION_CLOSED');case['device'].command(['shell','am','force-stop','vn.rtr.aeris.mission'],deadline_ns=time.monotonic_ns()+10_000_000_000);transition=owner.planned_native_rollover(deadline_ns=time.monotonic_ns()+25_000_000_000);case['managementCommand']('NATIVE_ROLLOVER')
 ui.geometry=None;ui.last_native=None;ui.next_native=0;ui.bind_geometry();restored=ui.workspace_saved();need(restored['head']==saved_final['head']and restored['planSHA256']==saved_final['planSHA256']and restored['observation'].get('consent')is False,'NATIVE_WORKSPACE_RESTART_NO_AUTHORITY');post=ui.state();need(post['client'].get('active')is not True and post['flight'].get('authority')is None,'RESTART_NO_OPERATOR_OR_FLIGHT_AUTHORITY');need(ui.probe.pid!=old_pid and ui.probe.process_epoch!=old_epoch,'ACTUAL_NEW_ANDROID_PROCESS');ui.tap('nav-review');ui.native(True)
 ui.event('PUBLIC_ANDROID_JOURNEY_COMPLETE',{'review':s['reviews'][-1],'nativeObservationRef':ui.probe.last_ref,'workspaceInitial':{k:v for k,v in saved_initial.items()if k!='observation'},'workspaceFinal':{k:v for k,v in saved_final.items()if k!='observation'},'restart':transition,'manualIntervention':False})
 return{'status':'PUBLIC_ANDROID_UI_WORKLOAD_COMPLETED','manualIntervention':False,'nativeUI':True,'manualSeconds':duration,'reviewRun':s['reviews'][-1]['run'],'reviewAccepted':True,'androidWorkspacePersistenceAndRestart':True,'scope':'NOMINAL_POLYGON_WITH_MANUAL_HOLD_AUTO_VIDEO_PAYLOAD_RESTART','notCovered':['LINKDROP','AP_REBOOT','CORRIDOR_CORPUS','FULL_RAW_SAF_PENDING_HANDOFF']}

def handoff(owner,case,raw_reference,check):
 from aeris_runtime.saf_receiver import verify_recipient,decode
 import base64,hashlib
 ui=case['uiDriver'];probe=case['native'];device=case['device'];need(device.budget.mock is False,'ACTUAL_SAF_REQUIRES_NONMOCK_OWNER')
 q,*_=ui.get('/api/raw-status');need(q.get('ok')is True and q['result'].get('ready')is True,'ROOT_CLOSED_RAW_READY');parts=q['result']['parts'];need(len(parts)<=8,'JOINT_SAF_DOCUMENT_BOUND')
 def saved(stream,index,previous):
  until=time.monotonic_ns()+15_000_000_000
  while time.monotonic_ns()<until:
   check();status=ui.native(True);exp=status['exportBudget']
   if exp.get('successCount',0)>previous:
    cap=probe.saf_document(stream,index);return cap
   time.sleep(1)
  raise TimeoutError('PUBLIC_UI_SAF_SUCCESS_NOT_OBSERVED_NO_RETRY')
 initial=ui.native(True)['exportBudget'].get('successCount',0);ui.tap('beta-export-raw');ui.save_dialog();manifest_cap=saved('manifest',-1,initial)
 # Obtain the bare immutable manifest bytes from its genuine SAF URI.
 # No host-source archive or summary is substituted for recipient bytes.
 with device.open_saf_document(manifest_cap,deadline_ns=time.monotonic_ns()+30_000_000_000,check=check)as source:
  chunks=[];size=0
  while True:
   b=source.read(65536)
   if not b:break
   size+=len(b);need(size<=32*1024*1024,'ACTUAL_MANIFEST_DOCUMENT32M');chunks.append(b)
  document=b''.join(chunks)
 original=document;need(hashlib.sha256(original).hexdigest()==raw_reference['manifestSHA256'],'ACTUAL_DOCUMENT_MANIFEST_SHA');manifest=decode(original);need(manifest.get('format')=='aeris-betasim-closed-raw-manifest'and manifest.get('authorityRestorable')is False,'ACTUAL_MANIFEST_SCOPE')
 caps={}
 for part in parts:
  stream=part['stream'];index=part['index'];previous=ui.native(True)['exportBudget'].get('successCount',0);ui.tap('raw-part-'+stream+'-'+str(index));ui.save_dialog();caps[(stream,index)]=saved(stream,index,previous)
 def opener(stream,index):
  cap=caps[(stream,index)]
  return lambda:device.open_saf_document(cap,deadline_ns=time.monotonic_ns()+60_000_000_000,check=check)
 result=verify_recipient(original,manifest_sha=raw_reference['manifestSHA256'],expected_context=case['context'],expected_candidate=owner.digest,bundle_openers=[opener('bundle',p['index'])for p in manifest['bundle']['parts']],native_openers=[opener('native-closed-files',p['index'])for p in manifest['nativeStream']['parts']])
 from aeris_runtime.once_reader import read_receipts
 expected={('manifest',-1)}|set(caps);rows=[r for r in read_receipts(device.store.root,'diagnostic')if r.get('format')=='aeris-native-saf-recipient-stream'and r.get('nativeManifestSHA256')==raw_reference['manifestSHA256']]
 need(len(rows)==len(expected)and {(r['stream'],r['index'])for r in rows}==expected and all(r.get('completeOriginalStream')is True and r.get('bothOriginalPipeEOF')is True and r.get('failure')is None and r.get('exit')==0 for r in rows),'ORIGINAL_NATIVE_URI_COMMAND_COMPLETENESS_JOIN')
 result.update(actualSAFOrigin='VERIFIED_GENUINE_NATIVE_IMMUTABLE_URI_RECEIPTS_AND_ORIGINAL_ADB_CONTENT_STREAMS',actualSAFBytesVerified=True,originalSAFStreamCount=len(rows),packageDocumentSHA256=hashlib.sha256(document).hexdigest(),executionEvidenceVerified=False)
 owner.write('recipient-independent-byte-verification.json',result);return {'status':'SAF_FULL_RAW_BYTES_EXPORTED_RECEIVER_VERIFIED','receiver':result,'manualIntervention':False,'fullRawRequiresSeparateFlightAndSignatureAcceptance':True}
