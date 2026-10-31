from ui01 import *
import subprocess
owned();run=sys.argv[1]
def script(name,*args):subprocess.run([sys.executable,'-B',str(Path(__file__).parent/(name+'.py')),*args],cwd=R,check=True)
script('start',run);w=journal('loss-existing-before-connect');doc=json.loads(w['journals']['workspaces/initial']['latest']['body']);pins=json.loads((E/'loss-pins06.json').read_text());assert doc['compiled']['plan']['sha256']==pins['planSha256'];assert doc['mission']['draft']['kml']==(R/'evidence/product-milestones/p1-corpus/operator-loss.kml').read_text();tap01('pane-close');tap01('open-sitl83');tap01('connect83');meta=events98(run,'META')[0][1];assert meta['document']==doc;capture(run+'-readonly')
script('wait_health',run);script('start_auto',run,'upload','loss');script('payload_loss',run);script('archive_loss',run)
