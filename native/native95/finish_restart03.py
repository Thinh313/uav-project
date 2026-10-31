from android_qa import *
owned()
expected=json.loads((E/'s095f2c41e36548be9071-closed-workspace.json').read_text())
actual=json.loads((E/'95-reboot03.json').read_text());assert actual['files']==expected['files']
def files(package):
 raw=adb('exec-out','tar','-C','/data/user/0/'+package+'/files','-cf','-','.')
 with tarfile.open(fileobj=io.BytesIO(raw))as t:return raw,{m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t.getmembers() if m.isfile()}
with tarfile.open(E/'s095f2c41e36548be9071-closed-files.tar')as t:before={m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t.getmembers() if m.isfile() and m.name.startswith(('./direct95/','./workspaces/'))}
raw,now=files(P);assert before=={k:v for k,v in now.items() if k.startswith(('./direct95/','./workspaces/'))}
(E/'android95-final03-files.tar').open('xb').write(raw)
old=json.loads((E/'old-private-before.json').read_text());checks={}
for package,hashes in old.items():
 _,current=files(package);assert hashes==current,package;checks[package]=len(current)
capture('95-final03-history-fresh')
adb('shell','input','tap',260,290);time.sleep(.7);capture('95-final03-review-selected')
(E/'restart03.json').open('x').write(json.dumps({'status':'PASS','processRestart':True,'androidReboot':True,'workspaceAndRawProtectedFiles':len(before),'bytesUnchanged':True,'automaticReconnect':False,'authorityRestored':False,'oldAppPrivateFilesUnchanged':checks,'currentUIEvidence':'95-final03-history-fresh.png + 95-final03-review-selected.png','rejectedDiagnosticEvidence':'95-reboot03-ui.jsonl is stale due persistent 2MiB diagnostic cap; not used for source/mode acceptance','scope':'CLOSED_SESSION_RESTART_NOT_AIRBORNE_CRASH_RECOVERY'},indent=2))
print('FINAL03_RESTART_PERSISTENCE_PASS')
