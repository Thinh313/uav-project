"""Actual GET/cache/diagnostic code over bounded original response fixtures, no actor."""
from pathlib import Path
from unittest.mock import patch
import base64,hashlib,json,os,shutil,sys,zlib
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path.insert(0,str(P.parent));import test_final_ui_failure06 as f
from aeris_runtime.metadata_budget import encoded
LAB=R/'evidence/betasim-integrated01/runtime/.state07'
def state(reason,noise=''):return encoded({'ok':True,'result':{'busy':False,'error':'ROOT_OBSERVATION_DEADLINE','flight':{'preflight':{'ready':False,'checks':[{'pass':False,'detail':reason}]},'live':{'failure':None}},'noise':noise}})
def main():
 assert not LAB.exists();LAB.mkdir(parents=True);oldlab=f.LAB;f.LAB=LAB;groups=[]
 try:
  ui_raw=f.body('BEFORE_PREFLIGHT');old=state('OLD_REASON');latest=state('LATEST_RAW_PREDICATE');o,ui,opener,now=f.fixture('latest',[ui_raw,old,latest]);ui.observation();now[0]+=1_000_000_000;ui.state();now[0]+=1_000_000_000;ui.state();now[0]+=100_000_000;n=len(opener.calls);ref=ui.persist_failure(ValueError('PUBLIC_UI_WAIT_TYPED_PREFLIGHT'));q=json.loads((o.root/ref['path']).read_bytes());s=q['lastState'];assert len(opener.calls)==n==3 and zlib.decompress(base64.b64decode(q['originalResponseZlibBase64']))==ui_raw and zlib.decompress(base64.b64decode(s['originalResponseZlibBase64']))==latest and s['originalResponseSHA256']==hashlib.sha256(latest).hexdigest()and s['ageAtFailureUpperRootMs']==100 and q['ageUpperMsAtFailure']>2000 and s['sourceStateSummary']['preflight']['checks'][0]['detail']=='LATEST_RAW_PREDICATE';groups.append('independent-latest-API-state-and-older-DOM-originalbytes-hashes-clocks-retained-no-newGET')
  o,ui,opener,now=f.fixture('noise',[f.body('NOISY',noise=base64.b64encode(os.urandom(40000)).decode()),state('X',base64.b64encode(os.urandom(65000)).decode())]);ui.observation();ui.state();a=ui.last_ui_capture['raw'];b=ui.last_state_capture['raw'];ref=ui.persist_failure(ValueError('stop'));q=json.loads((o.root/ref['path']).read_bytes());assert len(encoded(q))<=32768 and base64.b64decode(q['originalResponsePrefixBase64'])==a[:8192]and base64.b64decode(q['lastState']['originalResponsePrefixBase64'])==b[:8192]and q['retainedCompleteOriginalResponse']is False and q['lastState']['retainedCompleteOriginalResponse']is False and q['lastState']['originalResponseSHA256']==hashlib.sha256(b).hexdigest();groups.append('joint32KiB-cap-no-widening-explicit-two-incomplete-original-prefixes')
  o,ui,opener,now=f.fixture('bad',[b'{bad state original']);ui.instance='mock'
  try:ui.state()
  except ValueError:pass
  ref=ui.persist_failure(ValueError('parse'));q=json.loads((o.root/ref['path']).read_bytes());assert zlib.decompress(base64.b64decode(q['lastState']['originalResponseZlibBase64']))==b'{bad state original'and q['lastState']['originalStateResponseValidated']is False and q['originalObservationValidated']is False;groups.append('bad-state-JSON-retained-beforeparse-no-faked-summary-or-DOM')
  o,ui,opener,now=f.fixture('bounds',[b'x'*131073]);ui.instance='mock'
  try:ui.state()
  except RuntimeError:pass
  assert len(ui.last_state_capture['raw'])==131073 and ui.last_state_capture['responseComplete']is False;ref=ui.persist_failure(ValueError('overflow'));q=json.loads((o.root/ref['path']).read_bytes());assert q['lastState']['originalHTTPResponseComplete']is False;groups.append('131072-state-read-bound-keeps-detection-prefix-explicitincomplete-no-extra-bodyread')
  malformed=encoded({'ok':True,'result':{'flight':{'live':['bad-live-type'],'preflight':{'ready':False}}}});o,ui,opener,now=f.fixture('malformed',[malformed]);ui.instance='mock';ui.state();ref=ui.persist_failure(ValueError('nested'));q=json.loads((o.root/ref['path']).read_bytes());assert zlib.decompress(base64.b64decode(q['lastState']['originalResponseZlibBase64']))==malformed and q['lastState']['sourceStateSummary']['liveFailure']is None;groups.append('malformed-live-nestedtype-doesnot-prevent-exactoriginal-failurecapture')
  report={'format':'aeris-original-state-cache-source-mock','status':'PASS_ORIGINAL_RESPONSE_FIXTURES_NOT_OLD_R04_STATE_PROOF','groups':groups,'extraHTTPDuringFailure':0,'oldR04Modified':False,'actorsStarted':False,'scratchRemoved':str(LAB.relative_to(R))}
 finally:f.LAB=oldlab;shutil.rmtree(LAB)
 p=R/'evidence/betasim-integrated01/runtime/state-failure-mock07-final.json';assert not p.exists();p.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':main()
