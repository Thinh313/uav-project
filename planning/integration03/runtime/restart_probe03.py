"""Actual owned emulator restart observation + read-only private/kernel manifests. No connection or authority intents."""
from ui98 import *
owned();tag=sys.argv[1];assert tag in ['process','coldboot'];out=E/('restart-'+tag+'03');out.mkdir();adb('shell','am','force-stop',P)
start=time.monotonic_ns();adb('shell','am','start','-n',P+'/.ShellActivity','--es','source87','direct');deadline=time.monotonic()+20
while True:
 try:renderer=last();break
 except (AssertionError,IndexError):
  assert time.monotonic()<deadline,'RESTART_UI_NOT_FRESH';time.sleep(.3)
capture('restart-'+tag+'03-main');assert renderer.get('sourceStatus') is not None
# Wait to expose any unintended automatic socket/authority creation; no UI action.
time.sleep(3);pid=adb('shell','pidof',P).decode().strip();assert re.fullmatch(r'\d+',pid);uid=adb('shell','cat','/proc/'+pid+'/status').decode();uid=int(re.search(r'^Uid:\s+(\d+)',uid,re.M).group(1));matches=[];tables={}
for table in ['tcp','tcp6']:
 raw=adb('exec-out','cat','/proc/net/'+table).decode();tables[table]=raw
 for line in raw.splitlines()[1:]:
  fields=line.split()
  if len(fields)<10 or int(fields[7])!=uid:continue
  local=int(fields[1].split(':')[-1],16);remote=int(fields[2].split(':')[-1],16)
  if local in [5937,5942] or remote in [5937,5942]:matches.append({'table':table,'line':line,'local':local,'remote':remote})
q={'pass':not matches,'activeFlightOrCrewSockets':matches,'package':P,'pid':int(pid),'uid':uid,'scope':'Actual /proc/net TCP and TCP6 same Android app UID, current observation only','tables':tables};(out/'kernel.json').open('x').write(json.dumps(q,indent=2)+'\n');assert not matches,'AUTOMATIC_FLIGHT_OR_CREW_SOCKET'
base='/data/user/0/'+P+'/files/';raw=adb('shell','find',base,'-type','f','-exec','sha256sum','{}','+',timeout=90).decode();files={}
for line in raw.splitlines():
 sha,name=line.split(None,1);name=name.strip();assert re.fullmatch('[a-f0-9]{64}',sha) and name.startswith(base);files[name[len(base):]]=sha
(out/'manifest.json').open('x').write(json.dumps({'files':files,'scope':'Root-collected SHA of all current app private files','count':len(files)},indent=2)+'\n')
proof={'pass':True,'automaticReconnect':False,'automaticAuthority':False,'source':'Fresh direct Activity with no owned95 claim; no connect/listen/join/claim intents','hostStartMonoNs':str(start),'nativeUI':renderer,'kernelReceipt':'kernel.json','manifest':'manifest.json','hardware':'OWNED_EMULATOR_ONLY'};(out/'runtime.json').open('x').write(json.dumps(proof,indent=2,ensure_ascii=False)+'\n');adb('shell','am','force-stop',P);print('ACTUAL_RESTART_NO_SOCKET_OBSERVED_'+tag)
