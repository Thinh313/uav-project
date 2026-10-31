from ui01 import *
owned();tag=sys.argv[1];last_run=sys.argv[2];assert tag in ['process','coldboot'];out=E/('restart-'+tag);out.mkdir()
def pull():
 raw=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-','.')
 with tarfile.open(fileobj=io.BytesIO(raw))as t:files={m.name:t.extractfile(m).read()for m in t.getmembers()if m.isfile()}
 return raw,files
before,files=pull();(out/'before.tar').open('xb').write(before);keep={k:hashlib.sha256(v).hexdigest()for k,v in files.items()if k.startswith(('./direct95/','./workspaces/'))};assert keep
if tag=='coldboot':assert keep==json.loads((E/'restart-process/verification.json').read_text())['keptSHA256'],'COLD_BOOT_STORAGE_DRIFT'
claim=json.loads((E/'runs'/last_run/'launch.json').read_text());assert(E/'runs'/last_run/'closure.json').exists();q={k:claim[k]for k in ['run','containerId','pid','startedAt','binarySha256']};adb('shell','am','force-stop',P);adb('shell','am','start','-n',P+'/.ShellActivity','--es','source87','direct','--es','owned95',"'"+json.dumps(q,separators=(',',':'))+"'");time.sleep(1);last();tap01('pane-close');adb('shell','input','tap',52,171);tap01('payload');capture('restart-'+tag+'-unknown-no-restored-authority');controls=last()['controls'];required=['shutter','op-capture','op-send-zoom','op-send-focus','op-send-gimbal'];proof={k:next(c for c in controls if c['id']==k)['disabled'] for k in required};assert all(proof.values()),proof;journal('restart-'+tag+'-workspace');after,files2=pull();(out/'after.tar').open('xb').write(after);assert keep=={k:hashlib.sha256(v).hexdigest()for k,v in files2.items()if k.startswith(('./direct95/','./workspaces/'))},'PERSISTENCE_DRIFT'
runs=[]
for name,b in files2.items():
 if name.startswith('./direct95/')and name.endswith('/raw.jsonl'):
  rows=[json.loads(line)for line in b.splitlines()];assert rows[-1]['kind']=='CLOSED';runs.append(name)
ui=[len(b)for name,b in files2.items()if name.startswith('./ui96/')and name.endswith('.jsonl')];assert len(ui)<=16 and max(ui)<=2*2**20 and sum(ui)<=16*2**20
r={'status':'PASS','tag':tag,'scope':'Force-stop/relaunch owned Android Activity'if tag=='process'else'Owned emulator stopped and relaunched without snapshot/wipe; storage SHA cross-boot compared','preservedRawAndWorkspaceFiles':len(keep),'closedRuns':runs,'noNewRawGeneration':True,'noControlAuthorityRestored':True,'freshRendererDisabledControls':proof,'UIProofType':'Self-reported bounds/state plus actual screenshot, not hardware attestation','uiGenerations':len(ui),'uiMaxBytes':max(ui),'uiTotalBytes':sum(ui),'keptSHA256':keep};(out/'verification.json').open('x').write(json.dumps(r,indent=2));print(json.dumps({k:r[k]for k in ['status','tag','preservedRawAndWorkspaceFiles','uiGenerations']}))
