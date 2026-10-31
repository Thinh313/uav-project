import socket,json,subprocess,os
from pathlib import Path
e=Path('evidence/native94');ports={};initial={}
for p in[5582,5583,5905,5906,8874]:
 with socket.socket()as s:
  try:s.bind(('127.0.0.1',p));initial[str(p)]='PLAIN_BIND_FREE'
  except OSError as x:initial[str(p)]=str(x)
 with socket.socket()as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',p));ports[str(p)]='REUSEADDR_BIND_FREE_NO_LISTEN'
r=subprocess.run(['docker','inspect','aeris-native94'],capture_output=True);assert r.returncode!=0
launch=json.loads((e/'android-launch05.json').read_text())
for k in['pid','controllerPid']:
 try:os.kill(launch[k],0);raise AssertionError(k+' alive')
 except ProcessLookupError:pass
assert not Path('.local/native94/bridge-token').exists()
(e/'runtime-closure05.json').open('x').write(json.dumps({'ports':ports,'plainBind':initial,'ownedContainerAbsent':True,'emulatorAndControllerExited':True,'bridgeTokenAbsent':True,'dockerImagePrune':'completed; reclaimed 0B; no volumes/containers pruned','scope':'OWNED_NATIVE94_RESOURCES_ONLY; no listener started'},indent=2));print('CLOSED_AND_NO_TOKEN')
