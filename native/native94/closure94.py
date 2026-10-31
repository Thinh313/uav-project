import socket,json,subprocess,os
from pathlib import Path
e=Path('evidence/native94');ports={}
for p in[5582,5583,5905,5906,8874]:
 with socket.socket()as s:s.bind(('127.0.0.1',p));ports[str(p)]='FREE_REBIND'
r=subprocess.run(['docker','inspect','aeris-native94'],capture_output=True);assert r.returncode!=0
launch=json.loads((e/'android-launch.json').read_text())
for k in['pid','controllerPid']:
 try:os.kill(launch[k],0);raise AssertionError(k+' alive')
 except ProcessLookupError:pass
assert not Path('.local/native94/bridge-token').exists()
(e/'runtime-closure94.json').open('x').write(json.dumps({'ports':ports,'ownedContainerAbsent':True,'emulatorAndControllerExited':True,'bridgeTokenAbsent':True,'dockerImagePrune':'completed; reclaimed 0B; no volumes/containers pruned','scope':'OWNED_NATIVE94_RESOURCES_ONLY'},indent=2));print('CLOSED_AND_NO_TOKEN')
