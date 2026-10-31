from pathlib import Path
import subprocess,json,time,shutil,datetime
R=Path(__file__).resolve().parents[2];N=R/'native/shell30';E=R/'evidence/native30';J='/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin/java';W=N/'.qa-crash';checks=[];runs=[]
if W.exists():raise SystemExit('Old scratch exists')
W.mkdir()
def call(mode,root,token='ROOT',body=b''):
 p=subprocess.run([J,'-cp',str(N/'dist/journal-host.jar'),'vn.rtr.aeris.shell30.JournalMain',mode,str(root),*([token]if mode=='save'else[])],input=body,capture_output=True);assert p.returncode==0,p.stderr;return json.loads(p.stdout)
def check(name,ok):checks.append({'name':name,'pass':bool(ok)});assert ok,name
try:
 for phase in ['RECORD_PUBLISHED','HEAD_PENDING','HEAD_COMMITTED']:
  root=W/phase;first=call('save',root,body=b'old');marker=W/(phase+'.marker');p=subprocess.Popen([J,'-cp',str(N/'dist/journal-host.jar'),'vn.rtr.aeris.shell30.CrashMain',str(root),first['token'],phase,str(marker)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE);p.stdin.write(b'new');p.stdin.close()
  try:
   for i in range(50):
    if marker.exists():break
    time.sleep(.1)
   check('controlled own process staged '+phase,marker.exists() and marker.read_text()==phase and p.poll() is None)
   p.kill();code=p.wait(timeout=5);check('actual owned JVM SIGKILL '+phase,code==-9)
   last=call('load',root);check('new JVM committed-head recovery '+phase,last['bodyBase64']==('bmV3'if phase=='HEAD_COMMITTED'else'b2xk'))
   check('pending state and immutable revisions retained '+phase,last['pending']==(phase=='HEAD_PENDING') and len(list(root.glob('*.bin')))==2)
   runs.append({'phase':phase,'pid':p.pid,'exit':code,'before':first,'after':last,'scope':'Host JVM/file system, not Android or physical power loss'})
  finally:
   if p.poll()is None:p.kill();p.wait(timeout=5)
finally:
 (E/'host-crash.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS'if len(checks)==12 and all(x['pass']for x in checks)else'FAIL','checks':checks,'runs':runs},indent=2)+'\n');shutil.rmtree(W)
print(len(checks),'host crash checks PASS')
