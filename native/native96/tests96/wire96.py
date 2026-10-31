from pathlib import Path
import json,subprocess
R=Path(__file__).resolve().parents[3];N=R/'native/native96';E=R/'evidence/native96';W=N/'.host96';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin');S=N/'src/vn/rtr/aeris/native96'
subprocess.run([str(J/'javac'),'--release','8','-d',str(W),*[str(S/(n+'.java'))for n in['Json','DraftStore','RawJournal95','Dialect95','Profile95','WireGate95','DirectTransport95','GateReplay95Test']]],capture_output=True,check=True)
run=lambda p:subprocess.run([str(J/'java'),'-cp',str(W),'vn.rtr.aeris.native96.GateReplay95Test',str(R/p)],capture_output=True,text=True)
p=run('evidence/native95/qualified94-stream.tsv');assert p.returncode==0,p.stderr;positive=json.loads(p.stdout);cases=[]
for file,key in [('negative-cases.json',None),('native-faults95.json','cases')]:
 d=json.loads((R/'evidence/native95'/file).read_text());rows=d if key is None else d[key]
 for row in rows:
  p=run(row['path']);expected=row.get('expected',row.get('expect'));assert p.returncode!=0 and expected in p.stderr,(row,p.stderr);cases.append({'name':row['name'],'expected':expected,'pass':True})
(E/'wire96-tests.json').open('x').write(json.dumps({'status':'PASS','checks':1+len(cases),'positive':positive,'negative':cases,'scope':'NATIVE96_JAVA_GATE_AGAINST_FROZEN_CORPUS_NO_HARDWARE'},indent=2));print(1+len(cases))
