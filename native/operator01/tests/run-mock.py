from pathlib import Path
import subprocess,json,shutil,os
R=Path(__file__).resolve().parents[3];N=R/'native/operator01';E=R/'evidence/operator01';W=N/'.mock';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');assert not W.exists();assert shutil.disk_usage(R).free>20*2**30;W.mkdir();attempt=__import__('sys').argv[1];assert len(attempt)==2 and attempt.isdigit();logs=[]
def run(a,good=0):
 p=subprocess.run(list(map(str,a)),cwd=R,text=True,capture_output=True,timeout=90);logs.append({'command':list(map(str,a)),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==good,p.stdout+p.stderr;return p.stdout
try:
 vectors=E/('vectors'+attempt+'.tsv');run(['node',N/'tests/vectors.mjs',vectors]);src=N/'src/vn/rtr/aeris/operator01';pure=[p for p in src.glob('*.java')if p.name not in ['ShellActivity.java','Diagnostics90.java','DiagnosticSaf91.java','RawSaf96.java','PayloadNative97.java']];run([J/'javac','--release','8','-d',W,*pure]);run([J/'java','-cp',W,'vn.rtr.aeris.operator01.PolicyTest']);out=run([J/'java','-cp',W,'vn.rtr.aeris.operator01.Operator01Test',vectors,E/('wires'+attempt+'.txt')]);(E/('operator-mock'+attempt+'.json')).open('x').write(out);ui=run(['node',N/'tests/ui-model.mjs']);(E/('ui-model'+attempt+'.json')).open('x').write(ui)
 legacy=subprocess.run([str(J/'java'),'-cp',str(W),'vn.rtr.aeris.operator01.Payload97Test',str(R/'evidence/native97/vectors.tsv')],cwd=R,text=True,capture_output=True);(E/('legacy-contract-delta'+attempt+'.json')).open('x').write(json.dumps({'status':'INTENTIONAL_CONTRACT_DELTA'if legacy.returncode else'PASS','exit':legacy.returncode,'stdout':legacy.stdout,'stderr':legacy.stderr,'reason':'Original immutable Payload97Test expects SENT_UNCONFIRMED / attributed ACK and generation-wide fence for camera/gimbal; new explicit best-effort repeated intents intentionally remain SENT_UNATTRIBUTED. Baseline test left unchanged.'},indent=2))
 print(out);print(ui)
finally:
 (E/('mock-log'+attempt+'.json')).open('x').write(json.dumps(logs,indent=2));shutil.rmtree(W)
