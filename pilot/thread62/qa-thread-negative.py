"""Corrupt small sealed mock fixtures to prove the join refuses false evidence."""
from pathlib import Path
import json,struct
from thread_analysis import load
R=Path(__file__).resolve().parents[2];E=R/'evidence/thread62';src=E/'mock/t62cmockopt01';root=E/'mock/thread-negative01';root.mkdir();checks=[]
for case in ['torn','errno','cpuRegression','missedTick','foreignPid']:
 d=root/case;d.mkdir()
 for n in ['thread-samples.json','thread-samples.bin','thread-target.json','thread-observer-ready.json','backend-ready.json']:(d/n).write_bytes((src/n).read_bytes())
 b=bytearray((d/'thread-samples.bin').read_bytes());w=15
 if case=='torn':b=b[:-1]
 elif case=='errno':struct.pack_into('<q',b,24+5*8,5)
 elif case=='cpuRegression':struct.pack_into('<q',b,24+w*8+6*8,0)
 elif case=='missedTick':struct.pack_into('<q',b,24+3*8,3)
 else:
  q=json.loads((d/'backend-ready.json').read_text());q['pid']+=1;(d/'backend-ready.json').write_text(json.dumps(q))
 (d/'thread-samples.bin').write_bytes(b);failed=False
 try:load(d)
 except AssertionError:failed=True
 assert failed,case;checks.append({'name':case+' evidence refused','pass':True})
with(E/'qa-thread-negative.json').open('x')as f:json.dump({'status':'PASS_ADVERSARIAL_THREAD_JOIN','checks':checks,'scope':'Intentional corrupt mock copies only; original mock and actual evidence unchanged'},f,indent=2)
print(json.dumps({'checks':len(checks)}))
