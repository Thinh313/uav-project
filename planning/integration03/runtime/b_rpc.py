"""Explicit test driver for public localhost companion API; no flight control, no retry."""
from pathlib import Path
import urllib.request,urllib.error,json,time,sys,hashlib
E=Path(__file__).resolve().parents[3]/'evidence/integration03-runtime';ORIGIN='http://127.0.0.1:8851'
def state():
 with urllib.request.urlopen(ORIGIN+'/api/state',timeout=2)as r:return json.load(r)
def call(route,q=None,expected_error=None):
 assert route in ['connect','join','action','disconnect','select','refresh']
 if route=='action':assert q['resource']!='aircraft' or expected_error,'NO_HOST_FLIGHT_COMMANDS'
 # Passive bounded readiness only. A mutation is attempted exactly once.
 end=time.monotonic()+2
 while True:
  s=state()
  if not s['pending']:break
  assert time.monotonic()<end,'B_READINESS_BUSY_NO_MUTATION_ATTEMPT';time.sleep(.03)
 body=json.dumps(q or {},separators=(',',':')).encode();start=time.monotonic_ns();req=urllib.request.Request(ORIGIN+'/api/'+route,data=body,method='POST',headers={'Origin':ORIGIN,'Content-Type':'application/json','X-Crew-Csrf':s['csrf']})
 try:
  with urllib.request.urlopen(req,timeout=5)as r:status=r.status;raw=r.read()
 except urllib.error.HTTPError as ex:status=ex.code;raw=ex.read()
 response=json.loads(raw);record={'hostMonoNs':str(start),'route':route,'request':q or {},'status':status,'response':response,'responseSHA256':hashlib.sha256(raw).hexdigest(),'noAutomaticRetry':True}
 with(E/'explicit-b-api01.jsonl').open('a')as f:f.write(json.dumps(record,separators=(',',':'))+'\n')
 if expected_error:assert status>=400 and expected_error in response.get('error',''),response
 else:assert status==200,response
 return response
if __name__=='__main__':
 q=json.loads(sys.argv[2])if len(sys.argv)>2 else{};r=call(sys.argv[1],q,sys.argv[3]if len(sys.argv)>3 else None);print(json.dumps({k:r.get(k)for k in ['connected','authenticated','boot','notice','error','selected','scope']},ensure_ascii=False))
