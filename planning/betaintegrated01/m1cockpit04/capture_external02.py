"""Outside-raw parent observations retained by Root after managed shutdown.
No file under raw is modified. Self-reported outputs still require cold verification.
"""
from pathlib import Path
import sys,json,hashlib,os,time
R=Path(__file__).resolve().parents[3]
case=sys.argv[1];assert case in ('actual-combined02-01','actual-combined02-02','actual-combined02-03')
C=R/'evidence/betaintegrated01-m1cockpit04'/case/'control'
def read(n):return json.loads((C/n).read_text())
def last(n):
 lines=(C/n).read_text().splitlines();return json.loads(lines[-1])
v={'rootObservedHostNs':time.monotonic_ns(),'scope':'LOCAL_ROOT_PARENT_OBSERVATIONS_NOT_REMOTE_AUTH_OR_ACCEPTANCE','liveParentBackend':last('backend-control-stdout.txt'),'liveParentAP':last('container-control-stdout.txt'),'nativeClosedCheckpoint':read('native-last-external-observation.json'),'closure':read('closure.json'),'outsideRawSourceSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with(C/'external-anchors.json').open('x')as f:json.dump(v,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'case':case,'backendAnchor':v['liveParentBackend'].get('commitAnchor'),'APAnchor':v['liveParentAP'].get('terminalSHA256'),'nativeAnchor':v['nativeClosedCheckpoint'].get('journal',{}).get('commitAnchor'),'nativeClosed':v['nativeClosedCheckpoint'].get('closed'),'failure':v['closure']['failure']}))
