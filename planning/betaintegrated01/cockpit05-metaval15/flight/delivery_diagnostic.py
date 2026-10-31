"""Parent-SHA-bound bounded nonauthority host delivery timings."""
from pathlib import Path
import hashlib,json
from . import contract

def verify(rawroot,anchors,context):
 p=Path(rawroot)/'clock-delivery-diagnostic.json'
 if not p.is_file()or p.is_symlink()or not 1<=p.stat().st_size<=32768:raise ValueError('CLOCK_DELIVERY_DIAGNOSTIC32KiB_REQUIRED')
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();parent=anchors.get('liveParentBackend',{})
 if parent.get('clockDeliveryDiagnosticSHA256')!=h or parent.get('clockDeliveryDiagnosticError')is not None:raise ValueError('CLOCK_DELIVERY_PARENT_SHA')
 v=json.loads(raw);original_observation=anchors.get('rootObservedHostNs')
 if type(original_observation)is not int or not 0<=original_observation<2**64:raise ValueError('CLOCK_DELIVERY_ORIGINAL_CAPTURE_CLOCK_REQUIRED')
 if v.get('format')!='aeris-clockterm14-delivery-diagnostic'or type(v.get('version'))is not int or v['version']!=1 or v.get('diagnosticOnly')is not True or any(v.get(k)!=context[k]for k in('run','epoch','boot'))or v.get('ownerDone')is not True or v.get('ownerFailure')is not None:raise ValueError('CLOCK_DELIVERY_CONTEXT_OR_FAILURE')
 if v.get('ringCapacity')!=64 or type(v.get('lastOperations'))is not list or len(v['lastOperations'])>64 or v.get('authorityOrClockCalibrationFromDiagnostic')is not False:raise ValueError('CLOCK_DELIVERY_BOUNDS_OR_AUTHORITY')
 phases={'POLL','CORRELATOR_RECEIVE','MATCHED_CALLBACK','REQUEST_TICK','REQUEST_REGISTER','REQUEST_SEND','DURABLE_APPEND','PUBLICATION'}
 if type(v.get('phases'))is not dict or not set(v['phases'])<=phases:raise ValueError('CLOCK_DELIVERY_PHASES')
 for row in v['lastOperations']:
  if row.get('phase')not in phases or any(type(row.get(k))is not int or row[k]<0 for k in('beginHostNs','endHostNs','wallNs','threadCPUNs','nonCPUWallNs'))or not 0<=row['beginHostNs']<=row['endHostNs']<=original_observation<2**64 or row['endHostNs']-row['beginHostNs']!=row['wallNs']or row['nonCPUWallNs']!=max(0,row['wallNs']-row['threadCPUNs']):raise ValueError('CLOCK_DELIVERY_TIMING')
 total=0
 for phase,summary in v['phases'].items():
  keys={'count','wallTotalNs','wallMaxNs','threadCPUTotalNs'}
  if type(summary)is not dict or set(summary)!=keys or any(type(summary[k])is not int or summary[k]<0 for k in keys)or summary['count']<1 or summary['wallMaxNs']>summary['wallTotalNs']:raise ValueError('CLOCK_DELIVERY_SUMMARY')
  total+=summary['count']
 if any(type(v.get(k))is not int or v[k]<0 for k in('observedOperations','measurementErrors','polls','receivedDatagrams','matchedCallbacks','requestCadenceSkips'))or total!=v['observedOperations']or len(v['lastOperations'])!=min(64,total):raise ValueError('CLOCK_DELIVERY_COUNTS')
 expected={str((contract.ROOT/'planning/betaintegrated01/cockpit05-clockterm14/runtime'/name).resolve())for name in('owner.py','clock_socket.py','delivery.py')}
 if type(v.get('sourceSHA256'))is not dict or set(v['sourceSHA256'])!=expected:raise ValueError('CLOCK_DELIVERY_EXACT_PRODUCER_SOURCE_SET')
 for path,hsh in v['sourceSHA256'].items():
  pth=Path(path)
  if not pth.is_relative_to(contract.ROOT/'planning/betaintegrated01/cockpit05-clockterm14/runtime')or contract.sha(pth)!=hsh:raise ValueError('CLOCK_DELIVERY_SOURCE')
 if len(v.get('sourceSHA256',{}))!=3:raise ValueError('CLOCK_DELIVERY_THREE_SOURCES')
 return {'status':'PASS_PARENT_BOUND_NONAUTHORITY_CLOCK_DELIVERY_DIAGNOSTIC','sha256':h,'nonCPUIsExclusiveCause':False,'originalClockPrecisionQualified':False,'endToEndPacingQualified':False,'measurementErrors':v.get('measurementErrors'),'originalRootObservedHostNs':original_observation,'verifierCurrentUptimeUsed':False}
