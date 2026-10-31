"""Post-closure raw qualification. Separate upstream Python decoder and receiver replays."""
import sys,json,subprocess,hashlib
from pathlib import Path
from package88 import build,receive
R=Path(__file__).resolve().parents[2];E=R/'evidence/native93';label=sys.argv[1];state=json.loads((E/(label+'-closed.json')).read_text());r=state['review'];run=r['run'];out=E/'runs'/run
for cmd in [['node','native/native93/raw_verify_final.mjs',run],['python3','-B','native/native93/upstream_raw_oracle.py',run,label]]:
 q=subprocess.run(cmd,cwd=R,text=True,capture_output=True);(E/(label+'-'+('raw'if cmd[0]=='node'else'python')+'-verification.txt')).open('x').write(q.stdout+q.stderr);assert q.returncode==0,q.stderr
who='rtr-review-station';nonce='native93-'+label+'-closed';d=build(run,who,nonce);store=E/'independent-raw-receiver';received=receive(E/'packages'/(d['id']+'.zip'),who,nonce,store);expected=label=='nominal';assert received['missionAccepted']==expected and received['semantic']['failureVerified']==(not expected)
plan=json.loads((out/'plan.json').read_text());assert plan['acquisition']['kml']==r['model92']['draft']['kml']and'<LineString>'in plan['acquisition']['kml'];assert len(plan['compiled']['items'])==12 and sum(i['command']==206 for i in plan['compiled']['items'])==4
report={'status':'PASS','label':label,'run':run,'missionAccepted':received['missionAccepted'],'failureVerified':received['semantic']['failureVerified'],'modelSha256':r['model92']['sha256'],'missionSha256':r['missionSha256'],'planSha256':r['planSha256'],'rawReceipt':str((store/(d['id']+'.receipt.json')).relative_to(R)),'scope':'CORRIDOR_INTERNAL_QUAD_NOT_HERA_NOT_CAMERA_IMAGE_EXECUTION'};(E/(label+'-qualification.json')).open('x').write(json.dumps(report,indent=2));print(json.dumps(report))
