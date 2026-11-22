"""One-shot simulator fault requests; no MAVLink encoder or flight command API."""
from pathlib import Path
import hashlib,json,re,secrets,time
from .metadata_budget import encoded
from .rc01 import need,KINDS

FAULTS={'g301':'LINK_LOSS','g302':'AP_REBOOT','g303':'NATIVE_RESTART','g304':'NATIVE_RESTART'}
def airborne(case,now):
 w=case['reader'].witness;h,p=w.h,w.p
 need(h is not None and p is not None and h['armed']is True and p['relativeAltitudeMm']>=3000,'ORIGINAL_CRC_AIRBORNE_BEFORE_FAULT')
 need(all(type(x.get('hostNs'))is int and 0<=now-x['hostNs']<=1_500_000_000 for x in(h,p)),'FRESH_CRC_AIRBORNE_BEFORE_FAULT')
 need(w.prefix is not None,'DURABLE_TRANSPORT_BEFORE_FAULT');return {'heartbeat':dict(h),'position':dict(p),'committedPrefix':dict(w.prefix)}
def request(owner,case):
 """Only positively owned simulator paths, original request before effect."""
 owner.check();kind=FAULTS.get(owner.root.name);need(kind is not None and not case.get('faultRC01'),'ONE_EXPLICIT_SUPPORTED_FAULT');now=time.monotonic_ns();proof=airborne(case,now)
 value={'format':'aeris-betarc01-original-fault-request','version':1,'kind':kind,'context':dict(case['context']),'candidateSHA256':owner.digest,'requestHostNs':now,'nonce':secrets.token_hex(16),'airborneOriginal':proof,'authorityRestorable':False,'expectedNormalMissionOutcome':False}
 owner.write('fault-original-request-rc01.json',value);case['faultRC01']={**value,'dispatched':False}
 if kind=='LINK_LOSS':
  data={k:case['context'][k]for k in('run','epoch','boot')};data.update(action='CUT_NATIVE_LINK',nonce=value['nonce'],hostNs=time.monotonic_ns());path=case['root']/'raw/cut-request.json';raw=encoded(data);need(not path.exists(),'NO_PREEXISTING_LINK_FAULT');owner.budget.write('external_task',path,raw)
 elif kind=='AP_REBOOT':
  data={k:case['context'][k]for k in('run','epoch','boot')};data.update(action='REBOOT_OWNED_AP',nonce=value['nonce'],hostNs=time.monotonic_ns(),newAPBoot=secrets.token_hex(16));path=case['root']/'raw/ap-reboot-request.json';raw=encoded(data);need(not path.exists(),'NO_PREEXISTING_REBOOT_FAULT');owner.budget.write('external_task',path,raw)
 elif kind=='NATIVE_RESTART':
  # A real Activity death; old input outcome remains UNKNOWN until original
  # replay. A later explicit new session never revives its lease or grant.
  case['device'].command(['shell','am','force-stop',case['device'].APPLICATION_PACKAGE],deadline_ns=time.monotonic_ns()+10_000_000_000);case['faultRC01']['forceStopCommandRef']=case['device'].last_command_ref
 else:raise ValueError('RC01_UNREACHABLE_FAULT')
 case['faultRC01']['dispatched']=True;owner.write('fault-dispatch-rc01.json',case['faultRC01']);return dict(case['faultRC01'])

def reboot_request(path,config,now):
 p=Path(path);need(p.is_file()and not p.is_symlink()and p.stat().st_size<=2048,'REBOOT_REQUEST_FILE');q=json.loads(p.read_bytes());need(set(q)=={'run','epoch','boot','action','nonce','hostNs','newAPBoot'}and all(q[k]==config[k]for k in('run','epoch','boot'))and q['action']=='REBOOT_OWNED_AP'and re.fullmatch('[a-f0-9]{32}',q['nonce'])and re.fullmatch('[a-f0-9]{32}',q['newAPBoot'])and q['newAPBoot']!=q['boot']and type(q['hostNs'])is int and 0<=now-q['hostNs']<=2_000_000_000,'REBOOT_REQUEST_ORIGINAL_CONTEXT_FRESHNESS');return q
