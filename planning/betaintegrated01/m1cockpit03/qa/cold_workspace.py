"""Independent bounded workspace/link receiver. No Android, sockets or writes.

Expected bindings and native anchors must be root observations OUTSIDE the raw
bundle. Stored review prose never grants flight or coverage acceptance.
"""
from pathlib import Path
import base64,hashlib,importlib.util,json,re,sys,struct
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[4]
def sha(b):return hashlib.sha256(b).hexdigest()
def bounded(p,limit=131072):
 p=Path(p);assert p.is_file()and not p.is_symlink();b=p.read_bytes();assert len(b)<=limit;return b,json.loads(b)
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
N=module('native_integrity',R/'planning/betaintegrated01/m1control01/qa/native_cold.py')
M=module('passive_mavlink',R/'pilot/betaintegrated01/control01/mavlink.py')
def verify_native_ground(root,anchor,link):
 integrity=N.native_cold(root,anchor);f=M.Framer();tx=M.Framer();seq=None;last=-1;facts={};used={k:0 for k in ['hb','land','pos']};counts=dict(used);groups=0;land=False;landAction=False;intent=None;opened=provider=False;close=None;records=0
 for p in sorted(Path(root).glob('segment-*.jsonl')):
  for line in p.read_bytes().splitlines():
   r=json.loads(line);records+=1;last=r['monotonicNs'];k=r['kind'];raw=base64.b64decode(r['base64'],validate=True)
   if k=='LIFECYCLE':
    o=json.loads(raw)
    if o.get('kind')=='OPENED':
     for key in ['run','epoch','boot','generation','operator','profileId']:assert o[key]==link[key]
     assert o['binarySHA256']==link['APSHA256'];opened=True
   if k=='CONTROL_PROVIDER':
    o=json.loads(raw)
    for key in ['run','epoch','boot','generation']:assert o[key]==link[key]
    assert o['binarySHA256']==link['APSHA256']and o['configSHA256']==link['configSHA256'];provider=True
   if k=='OPERATOR_TOUCH_ACTION':landAction|=json.loads(raw).get('action')=='LAND'
   if k=='TX_INTENT':assert intent is None;intent=raw
   if k=='TX_WRITTEN':
    assert intent==raw;intent=None
    for x in tx.feed(raw,last):
     if x['id']==76 and(x['system'],x['component'])==(255,190):
      q=x['payload'];cmd=struct.unpack_from('<H',q,28)[0];vals=struct.unpack_from('<7f',q)
      if cmd==176 and vals==(1.,9.,0.,0.,0.,0.,0.)and q[30:33]==bytes([42,1,0])and landAction:land=True;used=dict(counts);groups=0
   if k=='TX_UNKNOWN':intent=None
   if k=='RX':
    for offset in range(0,len(raw),4096):
     for x in f.feed(raw[offset:offset+4096],last):
      if(x['system'],x['component'])!=(42,1):continue
      if seq is not None and not 1<=((x['wireSequence']-seq)&255)<128:continue
      seq=x['wireSequence'];p=x['payload'];key=None;good=None
      if x['id']==0:key='hb';good=not(p[6]&128)
      elif x['id']==245:key='land';good=p[1]==1
      elif x['id']==33:key='pos';lat,lon=struct.unpack_from('<ii',p,4);alt=struct.unpack_from('<i',p,16)[0];good=abs(lat)<=900000000 and abs(lon)<=1800000000 and abs(alt)<=400
      if key:counts[key]+=1;facts[key]=(last,good)
      valid=len(facts)==3 and all(v[1]and 0<=last-v[0]<=1500000000 for v in facts.values())
      if land and groups and not valid:groups=0;used=dict(counts)
      if land and valid and all(counts[z]>used[z]for z in counts):groups+=1;used=dict(counts)
   if k=='SESSION_CLOSE':assert close is None;close=(records,json.loads(raw));assert close[1]['authorityRestorable']is False
 assert close and close[0]==records and opened and provider and not f.pending and not tx.pending
 fresh=land and len(facts)==3 and all(v[1]and 0<=last-v[0]<=1500000000 for v in facts.values())
 if not fresh:groups=0
 return dict(integrity=integrity['integrity'],records=records,independentGroundGroups=groups,terminalFreshGround=bool(fresh),completionAcceptance=False,firstClosedReason=close[1]['reason'])
def verify_workspace(files,expected_bindings,external_anchors,expected_source_sha256=None):
 files=Path(files);root=files/'workspace03';assert not root.is_symlink();allpaths=list(root.iterdir());assert len(allpaths)<=256;total=0;drafts={};reviews={};review_hashes={};proof=[]
 for p in allpaths:
  m=re.fullmatch(r'(draft-(\d{6})|review-([A-Za-z0-9_.:-]{1,128}))-([0-9a-f]{64})\.json',p.name);assert m,p.name;b,o=bounded(p);assert sha(b)==m[4];total+=len(b)
  if m[2]:
   rev=int(m[2]);assert rev not in drafts and type(o['revision'])is int and o['revision']==rev and o['trainingOnly']is True;drafts[rev]=(sha(b),o)
  else:
   run=m[3];assert run not in reviews and o['run']==run and o['id']==run;reviews[run]=o;review_hashes[run]=sha(b)
 assert total<=16*2**20 and set(drafts)==set(range(1,len(drafts)+1))
 for run,o in reviews.items():
  _,link=bounded(files/'review-links'/(run+'.json'));assert link==o['preflightContext'];expected=expected_bindings[run]
  for key in ['run','epoch','boot','generation','operator','profileId','configSHA256']:assert link[key]==expected[key]
  assert link['APSHA256']==expected['binarySHA256']and link['modelSHA256']==expected['modelSHA256'];
  if expected_source_sha256 is not None:assert link['sourceSHA256']==expected_source_sha256 and link['sourceIdentity']['sourceSHA256']==expected_source_sha256
  assert drafts[link['surveyRevision']][0]==link['surveySHA256']==o['surveySHA256'];assert o['completionClaim']is False and o['coverageClaim']is False and o['actualImages']==0 and o['authorityRestorable']is False
  anchor=external_anchors[run];assert o['nativeTerminalSHA256']==anchor
  cold=verify_native_ground(files/'control-runs'/run,anchor,link);assert o['groundDistinctFreshGroups']==cold['independentGroundGroups'];assert o['status']!='NATIVE_GROUND_OBSERVED_PENDING_EXTERNAL_VERIFICATION'or cold['independentGroundGroups']>=2
  proof.append(dict(run=run,reviewSHA256=review_hashes[run],**cold))
 return dict(status='PASS_WORKSPACE_NATIVE_LINKS_NO_FLIGHT_ACCEPTANCE',drafts=len(drafts),reviews=len(reviews),bytes=total,records=proof,authorityRestored=False,rootSourceSHA256=expected_source_sha256,rootSourceVerified=expected_source_sha256 is not None)
if __name__=='__main__':print(json.dumps(verify_workspace(sys.argv[1],json.loads(Path(sys.argv[2]).read_text()),json.loads(Path(sys.argv[3]).read_text()),sys.argv[4]if len(sys.argv)>4 else None),indent=2))
