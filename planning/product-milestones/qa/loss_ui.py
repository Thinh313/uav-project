from ui01 import *
import subprocess
owned();run=sys.argv[1]
def script(name,*args):subprocess.run([sys.executable,'-B',str(Path(__file__).parent/(name+'.py')),*args],cwd=R,check=True)
script('start',run);script('import_plan','operator-loss.kml')
w=journal('loss-model-before-flight');doc=json.loads(w['journals']['workspaces/initial']['latest']['body']);assert doc['mission']['draft']['kml']==(R/'evidence/product-milestones/p1-corpus/operator-loss.kml').read_text();assert doc['mission']['draft']['options']['datumAcknowledged'];verified=subprocess.run(['node','native/native96/receiver_semantic96.mjs'],cwd=R,input=json.dumps(doc).encode(),capture_output=True,check=True);v=json.loads(verified.stdout);(E/'loss-model-frozen-compiler-parity.json').open('x').write(json.dumps(v,indent=2));pins=json.loads((E/'nominal-pins06.json').read_text());pins['planSha256']=v['planSha256'];(E/'loss-pins06.json').open('x').write(json.dumps(pins,indent=2))
# Compilation opens the SITL panel itself.
tap01('connect83');capture(run+'-readonly');script('wait_health',run);script('start_auto',run,'upload','loss');script('payload_loss',run);script('archive_loss',run)
