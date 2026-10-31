from ui97 import *
owned();run=json.loads((E/'gimbal08.json').read_text())['run'];assert parsed(run)[-1][0]=='CLOSED'
def pull(pkg):
 b=adb('exec-out','tar','-C','/data/user/0/'+pkg+'/files','-cf','-','.');t=tarfile.open(fileobj=io.BytesIO(b));return b,{m.name:t.extractfile(m).read()for m in t.getmembers()if m.isfile()}
b,files=pull(P);(E/'native-private-before-restart.tar').open('xb').write(b)
for case,uuid in [('camera','f7607a0e-ca71-48df-bc05-cf4683632dbd'),('gimbal',run)]:
 target=E/'run04'/(case+'-native-raw.jsonl');data=files['./payload97/'+uuid+'/raw.jsonl']
 if target.exists():assert target.read_bytes()==data
 else:target.open('xb').write(data)
(E/'run04'/'stop-request.json').open('x').write(json.dumps({'reason':'native gimbal and camera closed; no more commands'}))
keep={k:hashlib.sha256(v).hexdigest()for k,v in files.items()if k.startswith(('./payload97/','./workspaces/'))};adb('shell','am','force-stop',P);adb('shell','am','start','-n',P+'/.ShellActivity');time.sleep(.8);adb('shell','input','tap',52,537);time.sleep(.3);capture('restart97-no-authority');report=last();assert any(x['id']=='open97'and not x['disabled']for x in report['controls']);b2,files2=pull(P);(E/'native-private-after-restart.tar').open('xb').write(b2);assert keep=={k:hashlib.sha256(v).hexdigest()for k,v in files2.items()if k.startswith(('./payload97/','./workspaces/'))}
old=json.loads((E/'old-private-before.json').read_text());counts={}
for pkg,expected in old.items():
 _,f=pull(pkg);actual={k:hashlib.sha256(v).hexdigest()for k,v in f.items()};assert actual==expected,pkg;counts[pkg]=len(f)
u=[len(v)for k,v in files2.items()if k.startswith('./ui96/')and k.endswith('.jsonl')];assert len(u)<=16 and max(u)<=2*2**20 and sum(u)<=16*2**20
(E/'restart97.json').open('x').write(json.dumps({'status':'PASS','preservedPayloadWorkspaceFiles':len(keep),'noAutomaticSocketOrRawGeneration':True,'noAuthorityRestore':True,'oldPackagesUnchanged':counts,'uiGenerations':len(u),'uiMaxBytes':max(u),'uiTotalBytes':sum(u),'restart':'Android Activity process force-stop/relaunch, not OS reboot'},indent=2));print('RESTART_PRESERVATION_PASS',flush=True)
