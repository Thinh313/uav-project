from pathlib import Path
import subprocess,json,shutil
R=Path.cwd();N=R/'native/native98verify';E=R/'evidence/native98verify';W=N/'.host';assert not W.exists();W.mkdir();J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');src=N/'src/vn/rtr/aeris/native98'
def run(a):
 p=subprocess.run(list(map(str,a)),capture_output=True,text=True,timeout=45);assert p.returncode==0,p.stdout+p.stderr;return p.stdout
try:
 pure=[p for p in src.glob('*.java')if p.name not in ['ShellActivity.java','Diagnostics90.java','DiagnosticSaf91.java','RawSaf96.java','PayloadNative97.java']];run([J/'javac','--release','8','-d',W,*pure,R/'native/native98/tests98/Boundary97Test.java'])
 for name,klass,args in [('unified','Unified98Test',[R/'evidence/native98/vectors98.tsv',E/'wire04.txt']),('payload','Payload97Test',[R/'evidence/native98/vectors98.tsv']),('boundary','Boundary97Test',[R/'evidence/native98/vectors98.tsv'])]:
  output=run([J/'java','-cp',W,'vn.rtr.aeris.native98.'+klass,*args]);data=json.loads(output);assert data['status']=='PASS';(E/(name+'-regression04.json')).open('x').write(output);print(name,data['checks'],flush=True)
finally:shutil.rmtree(W)
