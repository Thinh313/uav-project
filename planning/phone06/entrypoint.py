"""Single explicit engineering entrypoint. No command auto-connects, grants, arms or retries."""
from pathlib import Path
import argparse,sys,subprocess,json,os,time,shutil,re,shlex
sys.dont_write_bytecode=True
P=Path(__file__).parent;R=P.parents[1];ADB=Path('/opt/homebrew/share/android-commandlinetools/platform-tools/adb')
def command(args):
 args=list(map(str,args))
 if args and args[0]=='adb':
  if not ADB.is_file():raise ValueError('CACHED_ADB_NOT_AVAILABLE_NO_DOWNLOAD')
  args[0]=str(ADB)
 p=subprocess.run(args,cwd=R,check=True,text=True,capture_output=True,timeout=10);return p.stdout.strip()
def serial06(serial):
 if not isinstance(serial,str)or not re.fullmatch('[A-Za-z0-9._-]{1,128}',serial)or serial.startswith('emulator-'):raise ValueError('USB_PHYSICAL_SERIAL_REQUIRED')
 return serial
def usb_proof06(serial):
 serial06(serial);rows=command(['adb','devices','-l']).splitlines();matches=[line.split()for line in rows if line.split()and line.split()[0]==serial]
 if len(matches)!=1 or len(matches[0])<3 or matches[0][1]!='device' or not any(x.startswith('usb:')for x in matches[0][2:]):raise ValueError('USB_EXACT_AUTHORIZED_ROW_REQUIRED')
 path=command(['adb','-s',serial,'get-devpath'])
 if not path.startswith('usb:')or len(path)>256:raise ValueError('USB_TRANSPORT_PATH_REQUIRED')
 return {'serial':serial,'authorizedRow':matches[0],'devpath':path}
def owned_mappings06(serial):
 result=[]
 for direction,args in [('reverse',['adb','-s',serial,'reverse','--list']),('forward',['adb','forward','--list'])]:
  for line in command(args).splitlines():
   row=line.split()
   if len(row)==3 and (direction=='reverse'or row[0]==serial):result.append((direction,row[1],row[2]))
 return result
def main():
 a=argparse.ArgumentParser();a.add_argument('action',choices=['source','mock','build','preflight','usb','usb-close','launch','run','ticket','receiver']);a.add_argument('--admission',type=Path);a.add_argument('--run');a.add_argument('--case',choices=['nominal','loss']);a.add_argument('--attempt');a.add_argument('--apply',action='store_true');a.add_argument('--package',type=Path);a.add_argument('--usb-receipt',type=Path);a.add_argument('--expect',type=Path);a.add_argument('--expect-sha256');a.add_argument('--launch-json',type=Path);args=a.parse_args()
 if args.action in ['source','mock','build']:
  if args.action=='source':sys.path.insert(0,str(R/'native/phone06'));from overlay import source;print(json.dumps({'status':'SOURCE_PINS_VALID','files':len(source())}));return
  if not args.attempt or not args.attempt.isdigit()or len(args.attempt)!=2:raise ValueError('EXPLICIT_ATTEMPT_REQUIRED')
  os.execv(sys.executable,[sys.executable,'-B',str(R/'native/phone06'/('tests/check.py'if args.action=='mock'else'build.py')),args.attempt])
 if args.action=='receiver':
  if not args.package or not args.expect or not args.expect_sha256:raise ValueError('EXPLICIT_PACKAGE_AND_PREDECLARED_EXPECTATION_SHA_REQUIRED')
  os.execv(sys.executable,[sys.executable,'-B',str(P/'receiver06.py'),'--package',str(args.package),'--run',args.run or'','--expect',str(args.expect),'--expect-sha256',args.expect_sha256])
 if args.action=='usb-close':
  from phase06 import read_json
  if not args.apply or not args.usb_receipt:raise ValueError('EXPLICIT_OWNERSHIP_RECEIPT_AND_APPLY_REQUIRED')
  if not args.usb_receipt.resolve().is_relative_to((R/'evidence/phone06/runtime').resolve()):raise ValueError('USB_RECEIPT_ROOT')
  saved=read_json(args.usb_receipt);serial=serial06(saved['serial']);base=['adb','-s',serial]
  if saved.get('package')!='vn.rtr.aeris.phone06'or not isinstance(saved.get('created'),list)or len(saved['created'])>4:raise ValueError('USB_RECEIPT_CONTEXT')
  current=owned_mappings06(serial)
  for direction,port in saved['created']:
   if (direction,port)not in [('reverse',5960),('reverse',5961),('forward',5942),('forward',5967)]:raise ValueError('USB_MAPPING_NOT_OWNED')
   mapping=(direction,'tcp:'+str(port),'tcp:'+str(port))
   if mapping not in current:raise ValueError('USB_MAPPING_CHANGED_NO_REMOVE')
  results=[]
  for direction,port in saved['created']:
   try:command(base+[direction,'--remove','tcp:'+str(port)]);results.append({'direction':direction,'port':port,'status':'REMOVED'})
   except Exception as e:results.append({'direction':direction,'port':port,'status':'UNKNOWN_REMOVE_FAILED','error':type(e).__name__+':'+str(e)[:240]})
  receipt={'serial':serial,'status':'CLEANUP_UNKNOWN'if any(x['status']!='REMOVED'for x in results)else'REMOVED_ONLY_EXACT_OWNED','mappings':results,'admissionFreshnessRequired':False}
  print(json.dumps(receipt))
  if receipt['status']=='CLEANUP_UNKNOWN':raise SystemExit(2)
  return
 from phase06 import validate_phase
 q=validate_phase(args.admission);serial=q['selectedSerial'];base=['adb','-s',serial];proof=R/'evidence/phone06/runtime'/('usb-'+serial+'.json')
 if args.action=='preflight':print(json.dumps({'status':'HOST_DECLARATION_VALID_NOT_DEVICE_READY','serial':serial,'sourceId':q['nativeSourceId'],'manualQualification':'UNSUPPORTED_PENDING_ACTUAL_PROOF','runBudget':q['allowedRuns']}));return
 if args.action.startswith('usb'):
  if not args.apply:raise ValueError('EXPLICIT_APPLY_REQUIRED')
  deviceProof=usb_proof06(serial)
  if proof.exists():raise ValueError('USB_MAPPING_RECEIPT_EXISTS_NO_REPLAY')
  reverse=command(base+['reverse','--list']);forward=command(['adb','forward','--list'])
  if any('tcp:'+str(port)in reverse+' '+forward for port in[5960,5961,5942,5967]):raise ValueError('USB_PORT_MAPPING_CONFLICT_NO_KILL')
  created=[]
  try:
   for direction,port in [('reverse',5960),('reverse',5961),('forward',5942),('forward',5967)]:command(base+[direction,'--no-rebind','tcp:'+str(port),'tcp:'+str(port)]);created.append((direction,port))
   proof.parent.mkdir(parents=True,exist_ok=True)
   with proof.open('x')as f:json.dump({'serial':serial,'created':created,'package':'vn.rtr.aeris.phone06','noPrivateDataRead':True,'usbTransportProof':deviceProof},f,indent=2);f.flush();os.fsync(f.fileno())
  except BaseException:
   for direction,port in created:
    try:
     if (direction,'tcp:'+str(port),'tcp:'+str(port))in owned_mappings06(serial):command(base+[direction,'--remove','tcp:'+str(port)])
    except Exception:pass
   raise
  print(json.dumps({'status':'USB_MAPPINGS_RECORDED_NOT_FLIGHT_AUTHORITY','receipt':str(proof)}));return
 if args.action=='launch':
  from phase06 import read_json,AP_SHA
  if not args.apply or not args.launch_json:raise ValueError('EXPLICIT_LAUNCH_DESCRIPTOR_AND_APPLY_REQUIRED')
  deviceProof=usb_proof06(serial);launch=read_json(args.launch_json,16384);run=launch.get('run')
  if run not in q['allowedRuns']or args.launch_json.resolve()!=(R/'evidence/phone06/runtime/runs'/run/'launch.json').resolve()or not re.fullmatch('[a-f0-9]{64}',launch.get('containerId',''))or type(launch.get('pid'))is not int or launch['pid']<=0 or launch.get('binarySha256')!=AP_SHA:raise ValueError('OWNED_PUBLIC_LAUNCH_CONTEXT')
  receipt=R/'evidence/phone06/runtime/runs'/run/'phone-launch.json'
  if receipt.exists():raise ValueError('PHONE_LAUNCH_ALREADY_ATTEMPTED_NO_RETRY')
  probe=subprocess.run([str(ADB),'-s',serial,'shell','pidof','vn.rtr.aeris.phone06'],capture_output=True,text=True,timeout=10)
  if probe.returncode not in [0,1]or probe.stdout.strip():raise ValueError('NEW_ACTIVITY_REQUIRES_OWN_PACKAGE_STOPPED_EXPLICITLY_NO_AUTO_KILL')
  claim=json.dumps(launch,separators=(',',':'))
  if len(claim.encode())>16384:raise ValueError('OWNED_INTENT_BYTE_BOUND')
  remote=shlex.join(['am','start','-n','vn.rtr.aeris.phone06/.ShellActivity','--es','source87','direct','--es','owned95',claim]);result=None;error=None
  try:
   result=command(base+['shell',remote])
   if 'Error:'in result or 'Exception'in result:raise ValueError('AM_START_REFUSED')
  except Exception as e:error=type(e).__name__+':'+str(e)[:512]
  receipt.parent.mkdir(parents=True,exist_ok=True)
  with receipt.open('x')as f:json.dump({'status':'LAUNCH_UNKNOWN_NO_RETRY'if error else'ACTIVITY_START_REQUESTED_NOT_CONNECTED','serial':serial,'run':run,'package':'vn.rtr.aeris.phone06','source87':'direct','launchDescriptor':str(args.launch_json),'usbProof':deviceProof,'result':result,'error':error,'automaticConnectOrGrant':False},f,indent=2);f.flush();os.fsync(f.fileno())
  if error:raise ValueError(error)
  print('ACTIVITY_START_REQUESTED_NO_CONNECT_OR_GRANT');return
 if args.run not in q['allowedRuns']:raise ValueError('RUN_NOT_ADMITTED')
 os.environ['PHONE06_ADMISSION']=str(args.admission.resolve())
 if args.action=='run':os.execv(sys.executable,[sys.executable,'-B',str(P/'runtime.py'),args.run,args.case or'nominal'])
 if args.action=='ticket':os.execv(sys.executable,[sys.executable,'-B',str(P/'admission06.py'),'--admission',str(args.admission),'--launch',str(R/'evidence/phone06/runtime/runs'/args.run/'launch.json')])
if __name__=='__main__':main()
