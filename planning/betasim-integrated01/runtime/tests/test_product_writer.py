"""Real metadata budget + owned Unix socket/file fault tests; no Android/AP."""
from pathlib import Path
import base64,hashlib,json,os,shutil,socket,struct,sys,time
from unittest.mock import patch
HERE=Path(__file__).resolve();ROOT=HERE.parents[1];REPO=ROOT.parents[2];sys.path[:0]=[str(ROOT/'source'),str(REPO)]
from aeris_runtime.metadata_budget import MetadataBudget
from aeris_runtime.product_writer import ProductWriter
LAB=REPO/'evidence/betasim-integrated01/runtime/.w'
CONTEXT={'run':'mock','epoch':'a'*32,'boot':'b'*32,'operator':'pilot','generation':'c'*32,'profileId':'full'}
def writer(name):
 root=LAB/name;root.mkdir(parents=True);b=MetadataBudget(root/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);b.admit();b.tick('cases');return ProductWriter(b,CONTEXT)
def request(w,payload=b'hello',path='journal/events.jsonl',sequence=1,offset=0):return {'version':1,'token':w.token,'sequence':sequence,'context':dict(CONTEXT),'op':'append','path':path,'payloadBase64':base64.b64encode(payload).decode(),'expectedOffset':offset}
def denied(fn):
 try:fn()
 except(ValueError,OSError,FileExistsError):return
 raise AssertionError('not rejected')
def exact(sock,n):
 raw=b''
 while len(raw)<n:
  part=sock.recv(n-len(raw));assert part;raw+=part
 return raw

def main():
 assert not LAB.exists();LAB.mkdir(parents=True);cases=[]
 try:
  w=writer('a');r=w.dispatch(request(w));assert r['ok']and r['committed']and(w.root/'journal/events.jsonl').read_bytes()==b'hello';r2=w.dispatch(request(w,b'!',sequence=2,offset=5));assert r2['ref']['offset']==5 and(w.root/'journal/events.jsonl').read_bytes()==b'hello!';assert w.budget.snapshot()['counters']['requests']==0 and w.budget.snapshot()['counters']['commands']==0;cases.append('real-budget-fsync-lossless-append-correct-counter-domain')
  for key,value in [('context',{**CONTEXT,'boot':'d'*32}),('token','d'*64),('sequence',99),('path','../outside'),('expectedOffset',99),('op','delete')]:
   bad=request(w,sequence=3,offset=6);bad[key]=value;before=w.budget.snapshot()['writes'];denied(lambda:w.dispatch(bad));assert w.budget.snapshot()['writes']==before
  cases.append('foreign-context-token-replay-path-offset-op-denied-prewrite')
  w.dispatch({**request(w,b'x',path='state/one.json',sequence=3),'op':'exclusive'});before=w.budget.snapshot()['writes'];denied(lambda:w.dispatch({**request(w,b'y',path='state/one.json',sequence=4,offset=1),'op':'exclusive'}));assert w.budget.snapshot()['writes']==before;cases.append('no-replace-delete-or-overwrite')
  for label,mode in [('eio','eio'),('short','short'),('fsync','fsync')]:
   w=writer(label);target=w.root/'journal/events.jsonl';orig_write=os.write;orig_fsync=os.fsync;calls=[0]
   def ownfd(fd):return target.exists()and os.fstat(fd).st_ino==target.stat().st_ino
   def faultwrite(fd,data):
    if ownfd(fd):
     if mode=='eio':raise OSError(5,'injected EIO')
     if mode=='short':
      calls[0]+=1
      return orig_write(fd,data[:1])if calls[0]==1 else 0
    return orig_write(fd,data)
   def faultsync(fd):
    if mode=='fsync'and ownfd(fd):raise OSError(5,'injected fsync')
    return orig_fsync(fd)
   with patch('os.write',faultwrite),patch('os.fsync',faultsync):denied(lambda:w.dispatch(request(w)))
   assert w.failure is not None and w.last_commit_state is None and w.budget.snapshot()['failed']is not None
   if mode=='short':assert target.read_bytes()==b'h'
   denied(lambda:w.dispatch(request(w,sequence=2)))
   cases.append(label+'-retains-prefix-unknown-commit-no-retry')
  w=writer('quota');lease=w.budget.reserve_lease({'lifecycle':w.budget.available('lifecycle')-4096});denied(lambda:w.dispatch(request(w,b'x'*16384)));assert not(w.root/'journal/events.jsonl').exists();cases.append('shared-owner-quota-denied-before-payload')
  w=writer('s')
  desc=w.start()
  with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)as sock:
   sock.settimeout(2);sock.connect(desc['socketPath']);time.sleep(.25);body=json.dumps(request(w)).encode();sock.sendall(struct.pack('!I',len(body))+body);n=struct.unpack('!I',exact(sock,4))[0];reply=json.loads(exact(sock,n));assert reply['ok']and reply['committed']
  closed=w.close();assert closed['threadStopped']and not w.thread.is_alive()and not w.socket_path.exists();cases.append('real-owned-Unix-frame-idle-firstbyte-and-bounded-close')
  report={'status':'PASS_HOST_FILE_RPC_MOCK_NOT_ANDROID','groups':cases,'actualAndroidAP':False,'sourceCounterDomain':'Product file writes do not consume AndroidSTATUS900 orADBcommands3700; original owner byte/highwater/globalcaps remain','scratchRemoved':str(LAB)}
 finally:shutil.rmtree(LAB)
 out=REPO/'evidence/betasim-integrated01/runtime/product-writer-mock.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'groups':len(cases)}))
if __name__=='__main__':main()
