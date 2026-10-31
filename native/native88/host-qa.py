from pathlib import Path
import subprocess,json,shutil,datetime
R=Path(__file__).resolve().parents[2];N=R/'native/native88';E=R/'evidence/native88';W=N/'.build';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');assert not W.exists() and shutil.disk_usage(R).free>=22*2**30;W.mkdir();results=[]
try:
 src=N/'src/vn/rtr/aeris/native88';pure=[p for p in src.glob('*.java')if p.name!='ShellActivity.java'];p=subprocess.run([str(J/'bin/javac'),'--release','8','-d',str(W),*map(str,pure)],capture_output=True,text=True);assert p.returncode==0,p.stderr
 for name in ['PolicyTest','DraftStoreTest','ArchiveEdgesTest']:
  cmd=[str(J/'bin/java'),'-cp',str(W),'vn.rtr.aeris.native88.'+name,str(E/('host-'+name+'01'))];p=subprocess.run(cmd,capture_output=True,text=True);results.append({'test':name,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,p.stdout+p.stderr
 (E/'host-qa01.json').open('x').write(json.dumps({'at':datetime.datetime.now().astimezone().isoformat(),'status':'PASS','scope':'HOST_JVM_NOT_ART','results':results},indent=2));print(json.dumps({'status':'PASS','summaries':[r['stdout'].splitlines()[-1]for r in results]}))
finally:shutil.rmtree(W)
