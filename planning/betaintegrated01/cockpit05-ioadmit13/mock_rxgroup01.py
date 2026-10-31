"""Adversarial pure grouped-RX clock/schema tests with synthetic row wrappers."""
from pathlib import Path
from importlib import import_module
import base64,hashlib,json,copy,struct
R=Path(__file__).resolve().parents[3];H='planning.betaintegrated01.cockpit05-ioadmit13.flight';G=import_module(H+'.rx_group');W=import_module(H+'.native_wire');M=import_module('pilot.betaintegrated01.control01.mavlink');E=R/'evidence/betaintegrated01-cockpit05-ioadmit13/host'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(v):return json.dumps(v,separators=(',',':')).encode()
def row(n,at,kind,data):return dict(n=n,monotonicNs=at,kind=kind,base64=base64.b64encode(data).decode())
def fixture():
 payload=struct.pack('<IBBBBB',17,2,3,128,4,3);packet=bytes([253,len(payload),0,0,1,42,1,0,0,0])+payload;packet+=struct.pack('<H',M.crc(packet[1:],M.DEFINITIONS[0][2]))
 a=row(10,100_000_000,'RX',packet);group=dict(format='aeris-native-rx-group',version=1,receiptElapsedNs=90_000_000,rawRecordN=10,rawPayloadSHA256=sha(packet),groupRecords=2,kernelNetworkAge='NOT_MEASURED');gb=enc(group);b=row(11,101_000_000,'AP_RX_GROUP',gb);commit=dict(format='aeris-native-rx-group-commit',version=1,receiptElapsedNs=90_000_000,rawRecordN=10,rawPayloadSHA256=sha(packet),groupRecordN=11,groupPayloadSHA256=sha(gb),groupDurableNs=270_000_000,parserAfterBarrier=True,completionWitnessDurability='NEXT_STRICT_BARRIER_OR_CLOSED_SEAL');c=row(12,271_000_000,'AP_RX_GROUP_COMMIT',enc(commit));return[a,b,c]
def replace(rows,index,key,value):
 v=json.loads(base64.b64decode(rows[index]['base64']));v[key]=value;rows[index]['base64']=base64.b64encode(enc(v)).decode();return rows

def main():
 cases=[]
 def audit(rows):
  a=G.RXAudit();events=[]
  for r in rows:
   e=a.feed(r)
   if e is not None:events.append(e)
  return a.finish(),events
 def check(name,rows,ok=True):
  err=None
  try:audit(rows);accepted=True
  except Exception as e:accepted=False;err=type(e).__name__+':'+str(e)
  cases.append(dict(case=name,expected=ok,accepted=accepted,error=err));assert accepted is ok,(name,err)
 check('valid_three_rows_one_barrier_semantics',fixture())
 _,events=audit(fixture());assert events[0]['receiptElapsedNs']==90_000_000 and events[0]['groupDurableNs']==270_000_000
 for index,key,bad in[(1,'version',True),(1,'rawRecordN',True),(1,'rawRecordN',9),(1,'rawPayloadSHA256','0'*64),(1,'groupRecords',3),(1,'receiptElapsedNs',100_000_001),(1,'kernelNetworkAge','KNOWN'),(2,'version',True),(2,'groupRecordN',True),(2,'groupRecordN',10),(2,'rawRecordN',11),(2,'rawPayloadSHA256','0'*64),(2,'groupPayloadSHA256','0'*64),(2,'groupDurableNs',100_999_999),(2,'groupDurableNs',271_000_001),(2,'receiptElapsedNs',90_000_001),(2,'parserAfterBarrier',False),(2,'completionWitnessDurability','ALREADY_DURABLE')]:check('bad_'+str(index)+'_'+key,replace(fixture(),index,key,bad),False)
 check('missing_group',fixture()[::2],False);check('missing_commit',fixture()[:2],False);check('orphan_commit',fixture()[2:],False);check('header_in_group',[fixture()[0],row(11,101_000_000,'HEADER',b'{}'),*fixture()[1:]],False)
 check('legacy_two_barrier_receipt_rejected',[row(1,1,'AP_RX_RECEIPT',b'{}')],False)
 tx,hb=W.native_wire_evidence(fixture());assert tx=={}and len(hb)==1 and hb[0]['guestNs']==90_000_000 and hb[0]['rawRXAppendNs']==100_000_000 and hb[0]['groupDurableNs']==270_000_000 and hb[0]['mode']==17 and hb[0]['armed']is True
 cases.append(dict(case='wire_heartbeat_uses_original_receipt_not_append_or_delayed_barrier',expected=True,accepted=True,error=None))
 output=dict(status='PASS_GROUPED_RX_SCHEMA_AND_ORIGINAL_RECEIPT_UNITS_ONLY',cases=cases,sourceSHA256={str(p.relative_to(R)):sha(p.read_bytes())for p in[Path(__file__),Path(G.__file__),Path(W.__file__)]},provenance='SYNTHETIC_UNSEALED_ROW_WRAPPERS_AND_MAVLINK_FIXTURE_NOT_REAL_GROUP_FSYNC_OR_DEVICE',runtimeExecuted=False,deviceCommands=False,physicalClosedChainOrJavaParityQualified=False)
 (E/'rxgroup-unit01.json').open('x').write(json.dumps(output,indent=2)+'\n');print(json.dumps(dict(status=output['status'],cases=len(cases))))
if __name__=='__main__':main()
