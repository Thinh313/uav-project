from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parents[3];N=R/'native/native96';E=R/'evidence/native96';W=N/'.host96';W.mkdir(exist_ok=True);J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');src=N/'src/vn/rtr/aeris/native96'
subprocess.run([str(J/'javac'),'--release','8','-d',str(W),*[str(src/(n+'.java'))for n in ['Json','DraftStore','UiJournal96','RawArchive96','FileOps87']],str(N/'tests96/Raw96Test.java')],capture_output=True,check=True)
p=subprocess.run([str(J/'java'),'-cp',str(W),'vn.rtr.aeris.native96.Raw96Test',str(R/'evidence/native95/runs/s095f2c41e36548be9071/android-raw.jsonl'),str(E/'mock96-04')],capture_output=True,text=True);assert p.returncode==0,p.stderr
(E/'pure96-tests04.json').open('x').write(p.stdout);print(p.stdout)
