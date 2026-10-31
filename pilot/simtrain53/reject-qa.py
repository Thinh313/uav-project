"""Loopback fault tests, explicitly not an ArduPilot/flight run."""
from pathlib import Path
import json,shutil,socket,struct,subprocess,sys,time
R=Path(__file__).resolve().parents[2];E=R/'evidence/simtrain53/mock'
sys.path.insert(0,str(R/'pilot/sim32-journal04'))
from wal_journal import read_wal


def main():
 E.mkdir();checks=[]
 for name in ['truncated','badRate','duplicate','foreignPeer','badPWM']:
  assert shutil.disk_usage(R).free>24*2**30
  out=E/name;out.mkdir();(out/'request.json').write_text(json.dumps({'load':'empty','wind':'calm','seed':32,'scope':'MOCK_ONLY_NOT_AP'}))
  log=(out/'console.txt').open('x');p=subprocess.Popen([sys.executable,'-B',str(R/'pilot/simtrain53/backend.py'),'mock',name],stdout=log,stderr=subprocess.STDOUT,cwd=R)
  try:
   deadline=time.monotonic()+5
   while not(out/'backend-ready.json').exists()and p.poll()is None and time.monotonic()<deadline:time.sleep(.02)
   assert(out/'backend-ready.json').exists(),'MOCK_START'
   with socket.socket(socket.AF_INET,socket.SOCK_DGRAM)as s,socket.socket(socket.AF_INET,socket.SOCK_DGRAM)as other:
    s.bind(('127.0.0.1',0));other.bind(('127.0.0.1',0));s.settimeout(2)
    valid=struct.pack('<HHI16H',18458,1200,0,*([1000]*16));sent=[]
    if name in ['duplicate','foreignPeer']:
     s.sendto(valid,('127.0.0.1',9002));sent.append(valid.hex());response=s.recv(2048);assert json.loads(response)['timestamp']>0
    bad=valid[:-1]if name=='truncated'else struct.pack('<HHI16H',18458,999 if name=='badRate'else 1200,1 if name=='foreignPeer'else 0,*([2500]*4+[1000]*12 if name=='badPWM'else[1000]*16))
    (other if name=='foreignPeer'else s).sendto(bad,('127.0.0.1',9002));sent.append(bad.hex())
    p.wait(timeout=5);assert p.returncode==1
   result=json.loads((out/'backend-result.json').read_text());assert result['status']=='FAILED'
   w=read_wal(out/'frames.wal');assert w['error']is None
   rx=[json.loads(r['payload'])for r in w['records']if r['kind']=='RX']
   assert [r['rawHex']for r in rx]==sent and all(r['source']=='MOCK_LOOPBACK_DATAGRAM_NOT_AP'for r in rx)
   assert result['frames']==(1 if name in ['duplicate','foreignPeer']else 0)
   assert not any(r['kind']=='CLOSE'for r in w['records']),'FAILURE_NOT_COMPLETE'
   checks.append({'name':name,'pass':True,'rawReceivedDatagramsRetained':len(rx),'committedFrames':result['frames'],'error':result['error'],'scope':'MOCK_UDP_NOT_AP_NOT_FLIGHT'})
  finally:
   if p.poll()is None:p.terminate();p.wait(timeout=5)
   log.close()
 with(R/'evidence/simtrain53/rejected-rx1.json').open('x')as f:json.dump({'status':'PASS_MOCK_FAULT_CAPTURE_ONLY','checks':checks,'scope':'No Docker/AP/flight instance; positive model path unchanged after real-flight matrix'},f,indent=2);f.write('\n')
 print(json.dumps({'status':'PASS_MOCK_FAULT_CAPTURE_ONLY','checks':len(checks)}))


if __name__=='__main__':main()
