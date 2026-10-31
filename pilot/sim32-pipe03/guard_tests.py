"""Adversarial lease/nonce tests, including real loopback late/foreign packets."""
from pathlib import Path
import json,time,threading,socket,struct,sys
from epoch import Epoch
from clock_host import Correlator,ClockObserver

R=Path(__file__).resolve().parents[2]
E=R/'evidence/sim32-pipe03/guard-fixtures'
E.mkdir()
checks=[]


def check(name,passed):
    checks.append({'name':name,'pass':bool(passed)})
    assert passed,name


def fixture(name):
    p=E/name;p.mkdir();(p/'state').mkdir();return p


def failure(fn):
    try:fn()
    except RuntimeError:return True
    return False


p=fixture('queued-stale');now=[0,0];ep=Epoch(p/'state',p,'test',lambda:now[0],lambda:now[1]);ep.progress();now[:]=[3_200_000_000,3_200_000_000]
check('queued packet rejected before model after3.2s',failure(ep.check));now[:]=[0,0]
check('terminal epoch cannot revive or reset',failure(ep.progress))
p=fixture('sleep-wall');now=[0,0];ep=Epoch(p/'state',p,'test',lambda:now[0],lambda:now[1]);ep.progress();now[:]=[100_000_000,3_200_000_000]
check('wall elapsed catches sleep excluded from monotonic',failure(ep.check))
p=fixture('clock-jump');now=[0,0];ep=Epoch(p/'state',p,'test',lambda:now[0],lambda:now[1]);ep.progress();now[:]=[1_000_000,260_000_000]
check('clock discontinuity invalidates epoch',failure(ep.check))
p=fixture('under-deadline');now=[0,0];ep=Epoch(p/'state',p,'test',lambda:now[0],lambda:now[1]);ep.progress();now[:]=[900_000_000,900_000_000];ep.check();ep.progress()
check('900ms is not quietly changed to3s stale',not ep.terminal)
c=Correlator(('127.0.0.1',9006));c.register(1,0);c.register(2,10);c.requests[1]['timeout']=True
check('out-of-order response matches original nonce',c.receive(struct.pack('<7Q',2,20,21,0,0,0,0),('127.0.0.1',9006),30)['status']=='MATCHED')
check('known late response retained without identity poisoning',c.receive(struct.pack('<7Q',1,1,2,0,0,0,0),('127.0.0.1',9006),40)['status']=='LATE_MATCHED')
check('duplicate is explicitly classified',c.receive(struct.pack('<7Q',1,1,2,0,0,0,0),('127.0.0.1',9006),50)['status']=='DUPLICATE_MATCHED')
check('unknown nonce rejected',failure(lambda:c.receive(struct.pack('<7Q',55,1,2,0,0,0,0),('127.0.0.1',9006),50)))
check('foreign peer rejected',failure(lambda:c.receive(struct.pack('<7Q',2,1,2,0,0,0,0),('127.0.0.1',9008),50)))


def replay(name,unknown):
    p=fixture(name);ready=threading.Event();stop=threading.Event()
    def peer():
        delayed=[]
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
            s.bind(('127.0.0.1',9006));s.settimeout(.03);ready.set()
            first=True
            while not stop.is_set():
                try:
                    data,addr=s.recvfrom(8);rid=struct.unpack('<Q',data)[0];a=time.monotonic_ns();packet=struct.pack('<7Q',rid+10000 if unknown else rid,a,time.monotonic_ns(),0,0,0,0)
                    if first and not unknown:delayed.append((time.monotonic()+.65,packet,addr));first=False
                    else:s.sendto(packet,addr)
                except socket.timeout:pass
                due=[x for x in delayed if time.monotonic()>=x[0]]
                for x in due:s.sendto(x[1],x[2]);delayed.remove(x)
    t=threading.Thread(target=peer);t.start();assert ready.wait(2)
    obs=ClockObserver(p,'test','epoch',peer=('127.0.0.1',9006),cal_port=9007)
    time.sleep(1.2);bad=failure(obs.seal);stop.set();t.join(2)
    rows=[json.loads(x)for x in(p/'clock-pairs.jsonl').read_text().splitlines()]
    if unknown:check('foreign nonce raw packet saved and seal refuses',bad and (p/'clock-error.json').exists() and (p/'clock-raw.jsonl').stat().st_size>0)
    else:check('real loopback late reply matches without capture failure',not bad and any(x['status']=='LATE_MATCHED'for x in rows))


replay('late-loopback',False);replay('unknown-loopback',True)
with(R/'evidence/sim32-pipe03/guard-tests.json').open('x')as f:json.dump({'status':'PASS','checks':checks,'scope':'Deterministic/adversarial unit and loopback protocol tests, not SITL acceptance'},f,indent=2);f.write('\n')
print('GUARD_NONCE_ADVERSARIAL_PASS',len(checks))
