"""Concurrent role/source-clock causal faults on real owned Unix socket."""
from pathlib import Path
import base64,json,os,shutil,socket,struct,sys,threading,time
from unittest.mock import patch
HERE=Path(__file__).resolve();ROOT=HERE.parents[1];REPO=ROOT.parents[2];sys.path[:0]=[str(ROOT/'source'),str(REPO)]
from aeris_runtime.metadata_budget import MetadataBudget
from aeris_runtime.product_writer import ProductWriter
LAB=REPO/'evidence/betasim-integrated01/runtime/.roles'
C={'run':'mock','epoch':'a'*32,'boot':'b'*32,'operator':'pilot','generation':'c'*32,'profileId':'full'}
def exact(s,n):
 b=b''
 while len(b)<n:
  q=s.recv(n-len(b));assert q;b+=q
 return b
def reply(s):return json.loads(exact(s,struct.unpack('!I',exact(s,4))[0]))
def send(s,r):
 b=json.dumps(r,separators=(',',':')).encode();s.sendall(struct.pack('!I',len(b))+b)
def request(w,op,path,data,seq=1):return{'version':1,'token':w.token,'sequence':seq,'context':C,'op':op,'path':path,'payloadBase64':base64.b64encode(data).decode(),'expectedOffset':0}
def writer():
 b=MetadataBudget(LAB/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);b.admit();b.tick('cases');return ProductWriter(b,C)
def main():
 assert not LAB.exists();LAB.mkdir(parents=True);w=writer();cases=[]
 try:
  before=time.monotonic_ns();r=w.dispatch(request(w,'clock-proof','reports/clock-proof',json.dumps({'challenge':'d'*32,'nodeSentNs':'999'}).encode()));after=time.monotonic_ns();clock=r['clock'];assert r['committed']is True and before<=clock['rootReceivedHostNs']<=clock['rootPreparedHostNs']<=after and clock['nodeSentNs']=='999'and clock['authorityGranted']is False;assert w.budget.snapshot()['counters']['requests']==0;cases.append('clock-private-proof-original-root-bracket-durable-noSTATUS-counter')
  w.start();data=socket.socket(socket.AF_UNIX);observer=socket.socket(socket.AF_UNIX);data.settimeout(2);observer.settimeout(2);data.connect(str(w.socket_path));observer.connect(str(w.socket_path));entered=threading.Event();release=threading.Event();original=w.budget.write
  def blocking(owner,path,payload,**kw):
   if str(path).endswith('/journal/fault.jsonl'):
    entered.set();assert release.wait(1);raise OSError(5,'causal EIO while observer polls')
   return original(owner,path,payload,**kw)
  with patch.object(w.budget,'write',blocking):
   send(data,request(w,'append','journal/fault.jsonl',b'not-committed',2));assert entered.wait(1);assert w.last_commit_state is None
   send(observer,request(w,'scene-frame','reports/scene-frame',json.dumps({'challenge':'e'*32}).encode()));scene=reply(observer);assert scene['ok']and scene['readonly']and scene['committed']is False and w.last_commit_state is None;assert w.sequence==2 and w.observer_sequence==1;cases.append('SCENE-independent-metadata-free-noDATAcounter-or-commitstate-clobber')
   release.set();failed=reply(data);assert failed['ok']is False and failed['committed']is None and failed['retryAllowed']is False and w.failure is not None;assert not(w.root/'journal/fault.jsonl').exists();cases.append('concurrent-DATA-EIO-retains-unknown-not-false-or-retry')
  w.begin_close();data.close();observer.close();closed=w.close();assert closed['threadStopped']and all(not t.is_alive()for t in w.workers);cases.append('both-role-workers-positive-bounded-close')
  out={'status':'PASS_HOST_ROLE_FAULT_MOCK_NOT_ANDROID','groups':cases,'actualAndroidAP':False,'scratchRemoved':str(LAB)}
 finally:
  try:w.begin_close();w.close()
  finally:shutil.rmtree(LAB)
 (REPO/'evidence/betasim-integrated01/runtime/writer-roles-mock.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'groups':len(cases)}))
if __name__=='__main__':main()
