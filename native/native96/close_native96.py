from android_qa import *
import importlib.util,base64
sys=__import__('sys');sys.dont_write_bytecode=True
run=sys.argv[1];owned();out=E/'runs'/run
spec=importlib.util.spec_from_file_location('close95_oracle',R/'pilot/apstream40/oracle-v2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
end=time.monotonic()+180
while time.monotonic()<end:
 p=m.MAVLink(None);p.robust_parsing=True;latest={};reached=set();armed=False
 for line in (out/'observer.jsonl').read_text().splitlines():
  row=json.loads(line)
  for f in p.parse_buffer(bytes.fromhex(row['hex']))or[]:
   if f.get_srcSystem()!=42 or f.get_srcComponent()!=1:continue
   if f.get_msgId()==0:armed|=bool(f.base_mode&128)
   if f.get_msgId()==46:reached.add(f.seq)
   latest[f.get_msgId()]=(row,f)
 h=latest.get(0);g=latest.get(245);pos=latest.get(33)
 if armed and h and g and pos and not h[1].base_mode&128 and g[1].landed_state==1 and abs(pos[1].relative_alt)<1000 and all(i in reached for i in [3,5,7,9]):
  assert all(time.monotonic_ns()-int(x[0]['hostMonoNs'])<3e9 for x in [h,g,pos]);break
 time.sleep(2)
else:raise AssertionError('INDEPENDENT_GROUND_DISARM_DEADLINE')
adb('shell','input','tap',52,605);time.sleep(.5);capture(run+'-ground-complete')
# Button coordinates from actual screenshots of this same 1280x800 layout.
adb('shell','input','tap',452,449);time.sleep(.7);capture(run+'-review-saved')
journal(run+'-closed-workspace')
raw=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-','.')
(E/(run+'-closed-files.tar')).open('xb').write(raw)
with tarfile.open(fileobj=io.BytesIO(raw))as t:
 native=t.extractfile('./direct95/'+run+'/raw.jsonl').read();(out/'android-raw.jsonl').open('xb').write(native)
 reviews=[]
 for entry in t.getmembers():
  if entry.isfile()and '/sitl/'in entry.name and entry.name.endswith('.bin'):
   r=json.loads(t.extractfile(entry).read().split(b'\n',6)[6])
   if r['run']==run:reviews.append(r)
 assert len(reviews)==1 and reviews[0]['accepted'] is True
 (out/'review.json').open('x').write(json.dumps(reviews[0],ensure_ascii=False))
(out/'stop-request.json').open('x').write('{"reason":"Final03 closed native review after independent observer ground-disarm"}')
print('NATIVE96_REVIEW_CLOSED')
