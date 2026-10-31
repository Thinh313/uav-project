from ui98 import *
owned();run=sys.argv[1];out=E/'runs'/run;assert events98(run,'CLOSED');tap98('archive-interrupted96');capture(run+'-unknown-review');journal(run+'-interrupted-workspace');raw=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-','.');assert len(raw)<64*2**20;(out/'private-interrupted.tar').open('xb').write(raw);(out/'android-raw.jsonl').open('xb').write(raw98(run))
with tarfile.open(fileobj=io.BytesIO(raw))as t:
 reviews=[]
 for e in t.getmembers():
  if e.isfile()and'/sitl/'in e.name and e.name.endswith('.bin'):
   q=json.loads(t.extractfile(e).read().split(b'\n',6)[6])
   if q['run']==run:reviews.append(q)
 assert len(reviews)==1;q=reviews[0];assert q['accepted']is False and q['execution']['complete']is False and q['execution']['groundDisarmed']is False and q['outcome96']=='INTERRUPTED_UNKNOWN_AIRCRAFT_STATE'and q['authorityRestorable']is False;(out/'review.json').open('x').write(json.dumps(q,ensure_ascii=False,indent=2))
(out/'stop-request.json').open('x').write('{"reason":"Native UNKNOWN review retained; passive observer must reach ground/disarm"}');print('UNKNOWN_REVIEW_SAVED',flush=True)
