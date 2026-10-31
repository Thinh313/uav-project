"""Diagnostic profile receipt, bound to live parent stdout; never exclusive IO cause."""
from pathlib import Path
import hashlib,re
from .native_chain import strict_json
PHASES={'serialize','guard','write','fsync','STAGE','recvwait'}
def integer(v):return type(v)is int and v>=0
def verify(rawroot,anchors,context):
 p=Path(rawroot)/'host-profile.json'
 if not p.is_file()or p.is_symlink()or not 1<=p.stat().st_size<=131072:raise ValueError('HOST_PROFILE128KiB_REQUIRED')
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();expected=anchors.get('liveParentBackend',{}).get('hostProfileSHA256')
 if type(expected)is not str or re.fullmatch('[a-f0-9]{64}',expected)is None or h!=expected:raise ValueError('HOST_PROFILE_OUTSIDE_STDOUT_ANCHOR')
 v=strict_json(raw)
 if v.get('format')!='aeris-compact10-host-memory-profile'or type(v.get('version'))is not int or v['version']!=1 or any(v.get(k)!=context[k]for k in('run','epoch','boot'))or v.get('journalClosed')is not True or v.get('hotExtraFileWrites')!=0:raise ValueError('HOST_PROFILE_CONTEXT_FORMAT')
 phases=v.get('phases');total=0;coverage={}
 if type(phases)is not dict or set(phases)!=PHASES:raise ValueError('HOST_PROFILE_PHASES')
 for name,s in phases.items():
  if any(not integer(s.get(k))for k in('calls','measuredCount','expectedMeasuredCount','measuredWallTotalNs','measuredThreadCPUTotalNs','measuredWallMaxNs','measuredThreadCPUMaxNs')):raise ValueError('HOST_PROFILE_TYPED_COUNTS')
  allIO=name in('write','fsync');expectedCount=s['calls']if allIO else(s['calls']+15)//16
  if s['calls']<=0 or s['measuredCount']!=expectedCount or s['expectedMeasuredCount']!=expectedCount or s['sampledMaximaAreNotFullCoverage']is not(not allIO):raise ValueError('HOST_PROFILE_COVERAGE')
  policy='ALL_REUSE_EXISTING_DIAGNOSTICIO_CLOCKS'if allIO else'DETERMINISTIC_FIRST_AND_EVERY16_CALLS'
  if s.get('coverage')!=policy:raise ValueError('HOST_PROFILE_SELECTION')
  hist=s.get('measuredHistogram');worst=s.get('measuredWorst32')
  if type(hist)is not list or len(hist)!=8 or any(not integer(x)for x in hist)or sum(hist)!=expectedCount or type(worst)is not list or len(worst)!=min(32,expectedCount):raise ValueError('HOST_PROFILE_BOUNDED_HISTOGRAM')
  for x in worst:
   if set(x)!={'beginHostNs','endHostNs','wallNs','threadCPUNs'}or any(not integer(n)for n in x.values())or x['endHostNs']-x['beginHostNs']!=x['wallNs']or x['wallNs']>s['measuredWallMaxNs']:raise ValueError('HOST_PROFILE_SPAN')
  total+=s['calls'];coverage[name]={'calls':s['calls'],'measuredCount':expectedCount,'coverage':policy,'maximaSampled':not allIO}
 if total!=v.get('operations')or total>100000000 or v.get('guardCoverageStarts')!='POST_CONSTRUCTOR_WRAPPER_ACTUAL_PRIME_AND_INITIAL_CHECKS_UNTIMED_NOT_SKIPPED':raise ValueError('HOST_PROFILE_TOTAL_OR_INITIAL_SCOPE')
 return dict(status='PASS_SOURCE_BOUND_DIAGNOSTIC_PROFILE_NOT_PACING_ACCEPTANCE',sha256=h,coverage=coverage,phaseDurations='NESTED_INCLUSIVE_MEASURED_ONLY_NO_EXCLUSIVE_CAUSE_OR_SUM',initialGuardPrimeTimed=False,actualGuardChecksUnchanged=True)
