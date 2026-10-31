"""New-owner lifecycle faults with real bounded Python threads, no sockets/services."""
from pathlib import Path
from importlib import import_module
from unittest.mock import patch
import json,threading,argparse,shutil
R=Path(__file__).resolve().parents[3];H='planning.betaintegrated01.cockpit05-clockowner02';B=import_module(H+'.runtime.backend');O=import_module(H+'.runtime.owner')
E=R/'evidence/betaintegrated01-cockpit05-clockowner02/host/startup-mock01'
def main():
 E.mkdir(parents=True,exist_ok=False);s=E/'scratch';s.mkdir();cfg={'bind':['127.0.0.1',9012],'requestedSpeedup':1,'capMs':500,'maximumSeconds':180,'run':'mockrun','epoch':'epoch','boot':'boot','evidence':str(s),'load':'x','wind':'x','seed':0};p=s/'config.json';p.write_text(json.dumps(cfg));checks=[]
 for fault in('adapter_constructor','hub_start'):
  owners=[];hubs=[]
  class Owner:
   def __init__(self,*a,**kw):self.stop_event=threading.Event();self.done=threading.Event();self.closed=False;owners.append(self)
   def start(self):
    def wait():self.stop_event.wait(1);self.done.set()
    self.thread=threading.Thread(target=wait,daemon=False);self.thread.start()
   def close(self,timeout):self.stop_event.set();self.thread.join(timeout);self.closed=True
  class Hub:
   def __init__(self,*a):self.stop_event=threading.Event();self.done=threading.Event();self.closed=False;hubs.append(self)
   def start(self):
    if fault=='hub_start':raise RuntimeError('MOCK_HUB_START')
   def stop(self):self.closed=True;self.done.set()
  def fail(*a,**kw):raise RuntimeError('MOCK_ADAPTER_CONSTRUCTOR')
  policy=import_module(H+'.policy')
  with patch.object(B,'ClockOwner',Owner),patch.object(B,'TransportHub',Hub),patch.object(B,'FrameAdapter',fail),patch.object(B,'Model',lambda *a:None),patch.object(B,'profile',lambda *a:None),patch.object(argparse.ArgumentParser,'parse_args',lambda self:argparse.Namespace(config=str(p))),patch.object(policy,'validate_recording_policy',lambda c:{'amendmentSHA256':'a'*64}):
   try:B.main()
   except RuntimeError as error:assert str(error).startswith('MOCK_')
   else:raise AssertionError('missingfault')
  assert owners[0].closed and owners[0].done.is_set()and not owners[0].thread.is_alive()and hubs[0].closed
  checks.append({'fault':fault,'bothStopped':True,'lingeringNonDaemonThread':False})
 calls=[]
 def failedjournal(*a,**kw):raise OSError('MOCK_CLOCK_JOURNAL_CONSTRUCTOR')
 o=O.ClockOwner(s,'mockrun','epoch','boot',180,'a'*64,journal_factory=failedjournal,socket_factory=lambda *a,**kw:calls.append(1));o.start();assert o.done.wait(1)
 try:o.close()
 except RuntimeError:pass
 else:raise AssertionError('ownerfailurelost')
 assert not calls and not o.thread.is_alive();checks.append({'fault':'clock_journal_constructor','socketConstructed':False,'failureLatched':True,'threadEnded':True})
 removed=sum(x.stat().st_size for x in s.rglob('*')if x.is_file());shutil.rmtree(s);value={'status':'PASS','cases':checks,'actualPrimeOrSocketOrAP':False,'scratchRemoved':True,'removedBytes':removed};(E/'results.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2))
if __name__=='__main__':main()
