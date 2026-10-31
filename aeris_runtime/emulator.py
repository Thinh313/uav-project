"""Stable owned cached emulator guardian; never AP, input, bootstrap, or aircraft control."""
from pathlib import Path
import argparse,hashlib,json,os,signal,socket,subprocess,time
from .admission import DiskGuard
from .candidate import put,sha
from .campaign import Campaign
from .paths import repository
from .policy import case_budget,campaign_budget
from .monitor import host_power
from pilot.betaintegrated01.runtime.ap_stage import canonical
STOP=False
def stop(*args):
 global STOP
 STOP=True

def observe_guardian(root,source_sha,*,now=time.monotonic_ns):
 root=Path(root);raw=(root/'guard.jsonl').read_bytes()[-65536:];lines=raw.splitlines();rows=[]
 for line in lines[-3:]:
  try:rows.append(json.loads(line))
  except(ValueError,UnicodeError):pass
 if not rows:raise ValueError('GENUINE_GUARDIAN_RECEIPT_REQUIRED')
 launch=json.loads((root/'launch.json').read_bytes());actual=subprocess.check_output(['ps','-p',str(launch['guardianPID']),'-o','lstart='],text=True,timeout=2).strip()
 return {'hostNs':rows[-1]['hostNs'],'alive':actual==launch['guardianProcessStart'],'closed':(root/'closure.json').exists(),'sourceVerified':source_sha==sha(__file__)==launch['guardianSourceSHA256']}

def run(spec,root,campaign_clock,inventory):
 global STOP
 root=Path(root);root.mkdir(exist_ok=False);campaign=Campaign(campaign_clock);repo=repository();guard=DiskGuard(repo);child=None;log=None;failure=None;started=time.monotonic_ns()
 try:
  campaign.check();b=case_budget(__import__('shutil').disk_usage(repo).free,180)
  if b['admitted']is not True:raise ValueError('EMULATOR_ORIGINAL_SHORT_BUDGET')
  p=host_power()
  if not p['AC'] and p['batteryPercent']<30:raise RuntimeError('POWER_ENTRY30')
  argv=spec['argv'];avd=Path(spec['AVD']);sdk=Path(spec['SDK']);adb=spec['ADB']
  if argv[:5]!=[str(sdk/'emulator/emulator'),'-avd','aeris-beta-m1','-port','5582'] or '-wipe-data'in argv:raise ValueError('CACHED_OWNED_EMULATOR_ARGV')
  for name,fact in spec['prerequisites'].items():
   if sha(fact['path'])!=fact['sha256']:raise ValueError('CACHED_PREREQUISITE:'+name)
  if sha(avd/'config.ini')!=spec['AVDConfigSHA256']:raise ValueError('AVD_CONFIGURATION_SHA')
  if 'emulator-5582' in subprocess.check_output([adb,'devices'],text=True,timeout=2):raise RuntimeError('EMULATOR_ALREADY_PRESENT')
  for port in (5582,5583):
   with socket.socket() as s:s.bind(('127.0.0.1',port))
  prime=guard.prime();campaign.check();ledger=inventory();_caps(ledger);put(root/'admission.json',canonical({'capacity':b,'power':p,'actualPrime':prime,'sourceSHA256':sha(__file__),'absoluteCampaignDeadlineNs':campaign.deadline_ns,'APStarted':False})+b'\n')
  log=(root/'console.txt').open('xb');env={**os.environ,'ANDROID_AVD_HOME':str(avd.parent),'ANDROID_USER_HOME':spec['ANDROID_USER_HOME'],'ANDROID_HOME':str(sdk),'ANDROID_SDK_ROOT':str(sdk)};child=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  put(root/'launch.json',canonical({'pid':child.pid,'processStart':subprocess.check_output(['ps','-p',str(child.pid),'-o','lstart='],text=True,timeout=2).strip(),'guardianPID':os.getpid(),'guardianProcessStart':subprocess.check_output(['ps','-p',str(os.getpid()),'-o','lstart='],text=True,timeout=2).strip(),'guardianSourceSHA256':sha(__file__),'argv':argv,'startedHostNs':started,'originalCampaignDeadlineNs':campaign.deadline_ns})+b'\n')
  last=time.monotonic_ns();wall=time.time();tick=0
  with (root/'guard.jsonl').open('xb') as f:
   while not STOP:
    guard.check();campaign.check()
    if child.poll() is not None:raise RuntimeError('OWNED_EMULATOR_EXIT')
    n=time.monotonic_ns();w=time.time();gap=(w-wall)-(n-last)/1e9
    if n-last>2_000_000_000 or abs(gap)>2:raise RuntimeError('SUSPEND_OR_GUARD_GAP')
    last=n;wall=w;p=host_power()
    if not p['AC'] and p['batteryPercent']<=20:raise RuntimeError('BATTERY_STOP20')
    if (root/'console.txt').stat().st_size>16*2**20:raise RuntimeError('EMULATOR_CONSOLE16MiB')
    tick+=1
    if tick%10==0:_caps(inventory())
    f.write(canonical({'hostNs':n,'power':p,'freeBytes':guard.diagnostic()['currentFreeBytes'],'wallMonoGapSeconds':gap})+b'\n');f.flush();os.fsync(f.fileno());time.sleep(.5)
 except BaseException as e:
  failure=type(e).__name__+':'+str(e);put(root/'failure.json',canonical({'failure':failure,'hostNs':time.monotonic_ns(),'APStarted':False})+b'\n')
 finally:
  if child is not None and child.poll() is None:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=25)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=10)
  if log:log.flush();os.fsync(log.fileno());log.close()
  put(root/'closure.json',canonical({'failure':failure,'exit':None if child is None else child.poll(),'hostNs':time.monotonic_ns(),'APStarted':False,'flightCommands':0})+b'\n')
 return 1 if failure else 0

def _caps(v):
 if any(type(v.get(k))is not int or not 0<=v[k]<=limit for k,limit in {'metadataBytes':64*2**20,'exportBytes':192*2**20,'AVDPositiveGrowthBytes':512*2**20,'artifactBytes':4*2**20,'taskAllocatedBytes':campaign_budget()['taskHardPeakBytes']}.items()):raise RuntimeError('SHARED_ORIGINAL_CAP')

def main():
 from .inventory import Inventory
 from .entry import module_origin_receipt
 from .candidate import load
 candidate=os.environ['AERIS_CANDIDATE_DIR'];load(candidate,os.environ['AERIS_CANDIDATE_SHA256']);module_origin_receipt(candidate)
 p=argparse.ArgumentParser();p.add_argument('--spec',required=True);p.add_argument('--root',required=True);p.add_argument('--campaign',required=True);p.add_argument('--evidence',required=True);p.add_argument('--planning',required=True);p.add_argument('--avd-baseline',required=True);a=p.parse_args();spec=json.loads(Path(a.spec).read_bytes());signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);raise SystemExit(run(spec,a.root,a.campaign,Inventory(a.evidence,a.planning,spec['AVD'],a.avd_baseline)))
if __name__=='__main__':main()
