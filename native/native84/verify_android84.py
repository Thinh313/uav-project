from pathlib import Path
import json,hashlib,tarfile,base64,re,sys
R=Path(__file__).resolve().parents[2];E=R/'evidence/native84';suffix=sys.argv[1]
names=['android84-before-restart'+suffix,'android84-after-restart'+suffix,'android84-after-cold-reboot'+suffix];snapshots=[]
for name in names:
 with tarfile.open(E/(name+'.tar'))as t:
  assert not any(m.issym()or m.islnk()for m in t.getmembers());files={m.name:t.extractfile(m).read()for m in t.getmembers()if m.isfile()}
 assert not any('..'in Path(n).parts or n.endswith('.pending')for n in files)
 snapshots.append(files)
assert snapshots[0]==snapshots[1]==snapshots[2];files=snapshots[-1];selected=files.get('workspaces/CURRENT',b'initial').decode().strip();prefix='workspaces/'+selected+'/sitl/';head=files[prefix+'HEAD'].decode().strip();records={}
for n,b in files.items():
 if not n.startswith(prefix)or not n.endswith('.bin'):continue
 token=hashlib.sha256(b).hexdigest();parts=b.split(b'\n',6);assert len(parts)==7 and parts[0]==b'AERISWORKSPACE33'and n.endswith(token+'.bin')and len(parts[6])==int(parts[4])and parts[5]==b'1';body=parts[6];sha=hashlib.sha256(body).hexdigest();assert sha==parts[3].decode();records[token]={'token':token,'previous':parts[2].decode(),'revision':int(parts[1]),'sha256':sha,'bodyBase64':base64.b64encode(body).decode()}
at=head;chain=[];seen=set()
while at!='ROOT':
 assert at in records and at not in seen;seen.add(at);r=records[at];chain.append(r);at=r['previous']
assert len(seen)==len(records),'Unexpected orphan in actual journal'
out={'status':'PASS_EXACT_JOURNAL_AFTER_APP_AND_COLD_RESTART','suffix':suffix,'selected':selected,'head':head,'journalRecords':len(chain),'identicalFiles':len(files),'filesSha256':{n:hashlib.sha256(b).hexdigest()for n,b in files.items()},'records':chain,'authorityRestored':False}
(E/('android-journal-verification'+suffix+'.json')).open('x').write(json.dumps(out,indent=2));print('PASS_NATIVE_BYTES_CHAIN '+str(len(chain)))
