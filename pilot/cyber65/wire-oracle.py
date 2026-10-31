"""Independent stdlib decoder of captured mock TX; no JS codec imported or binary executed."""
import json,struct,hashlib,pathlib,math,sys
R=pathlib.Path(__file__).resolve().parents[2]
source=R/'evidence/cyber65'/sys.argv[1];x=json.loads(source.read_text());bad=[];checks=0;frames=0
def crc(data):
 c=0xffff
 for byte in data:
  q=(byte^(c&255))&255;q=(q^((q<<4)&255))&255;c=((c>>8)^(q<<8)^(q<<3)^(q>>4))&65535
 return c
def check(ok,name):
 global checks
 checks+=1
 if not ok:bad.append(name)
for result in x['body']['results']:
 sid=result['scenarioId'];review=result['review']['body'];out=review['transport']['transport']['outbound'];expected=result['wireExpectations'];check(len(out)==len(expected),sid+': count')
 for i,(envelope,e) in enumerate(zip(out,expected)):
  b=bytes(envelope['bytes']);prefix=sid+':'+str(i);frames+=1
  check(b[0]==253 and b[2]==0 and len(b)==12+b[1],prefix+': bounded unsigned v2 fixture')
  check(int.from_bytes(b[7:10],'little')==76,prefix+': COMMAND_LONG only')
  check(b[5:7]==bytes([255,190]),prefix+': fixed synthetic GCS')
  check(crc(b[1:-2]+bytes([152]))==int.from_bytes(b[-2:],'little'),prefix+': CRC extra152')
  p=b[10:-2]+b'\0'*(33-b[1]);params=struct.unpack('<7f',p[:28]);cmd=struct.unpack('<H',p[28:30])[0]
  check(cmd==e['command'] and p[30]==42 and p[31]==e['component'],prefix+': exact camera/manager target')
  check(cmd in [531,532,2000,1000] and cmd not in [176,400],prefix+': no flight command')
  for key,value in e['params'].items():check(math.isclose(params[int(key[-1])-1],value,abs_tol=1e-5),prefix+':'+key)
  check(p[32]==0,prefix+': no confirmation retry')
  if cmd in [531,532]:check(math.isnan(params[3]),prefix+': unspecified speed stays NaN')
  if cmd==2000:check(math.isnan(params[6]),prefix+': unspecified seq extra stays NaN')
  if cmd==1000:check(math.isnan(params[2]) and math.isnan(params[3]),prefix+': unspecified rates stay NaN')
  # Eligibility is computed from captured TX, not a physical receiver/execution claim.
  eligible=[target for target in [1,100,101,154] if p[31]==target]
  check(eligible==[e['component']],prefix+': opposite-component exclusion')
out={'status':'PASS_SCOPED_MOCK_WIRE_ORACLE' if not bad else 'FAIL_WIRE_ORACLE','source':str(source.relative_to(R)),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'frames':frames,'checks':checks,'failures':bad,'scope':'Independent Python layout/CRC/target comparison of mock TX; not physical receiver or execution evidence'}
p=R/'evidence/cyber65'/sys.argv[2]
with p.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps(out));raise SystemExit(bool(bad))
