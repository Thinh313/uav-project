"""Exact JS-lexeme chains and original AJ02 native file/torn negatives."""
from pathlib import Path
import hashlib,io,json,os,shutil,struct,sys,tarfile
HERE=Path(__file__).resolve();ROOT=HERE.parents[1];REPO=ROOT.parents[2];sys.path[:0]=[str(ROOT/'source'),str(REPO)]
from aeris_runtime.product_seal import original_rows
from aeris_runtime.product_native import verify_input_tar
LAB=REPO/'evidence/betasim-integrated01/runtime/.sealbytes'
def frame(seq,at,kind,previous,payload):
 b=struct.pack('!QQB',seq,at,kind)+bytes.fromhex(previous)+payload;h=hashlib.sha256(b).digest();return struct.pack('!I',len(b)+32)+b+h,h.hex()
def tar(raw,snapshot,name):
 path=LAB/name
 with tarfile.open(path,'w:')as f:
  info=tarfile.TarInfo('files/product-input01/'+snapshot['input']['journal']['generation']+'.aj02');info.size=len(raw);f.addfile(info,io.BytesIO(raw))
 return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def denied(fn):
 try:fn()
 except(ValueError,KeyError):return
 raise AssertionError('not rejected')
def main():
 assert not LAB.exists();LAB.mkdir(parents=True);checks=[]
 try:
  body=b'{"data":{"hash":"nested","value":1e-7},"kind":"TEST","n":1,"previous":""}';h=hashlib.sha256(body).hexdigest();line=body[:-1]+b',"sha256":"'+h.encode()+b'"}\n';p=LAB/'flight.jsonl';p.write_bytes(line);raw,rows,head=original_rows(p,'sha256','previous','n',zero='');assert head==h and rows[0]['data']['value']==1e-7;checks.append('exact-original-JS-exponent-lexeme-not-Python-reserialization')
  p.write_bytes(line.replace(b'1e-7',b'2e-7'));denied(lambda:original_rows(p,'sha256','previous','n',zero=''));checks.append('originalchain-byte-tamper-refused')
  magic=b'AERIS_INPUT_JOURNAL_V2\n';envelope=json.dumps({'format':'aeris-native-input-signed-envelope','version':1,'keyId':'d'*64}).encode();intent,h1=frame(1,100,1,'0'*64,envelope);outcome,h2=frame(2,200,2,h1,b'200');journal=magic+intent+outcome;snapshot={'processEpoch':'e'*32,'input':{'producerKeyId':'d'*64,'journal':{'format':'AERIS_INPUT_JOURNAL_AJ02','generation':'e'*32,'closed':True,'failed':False,'durablyDrained':True,'sequence':2,'bytes':len(journal),'head':h2,'pendingOutcome':False}}};r=verify_input_tar(tar(journal,snapshot,'native.tar'),snapshot);assert r['unresolvedIntentSequence']is None and r['signedPayloadSemanticsNotYetIndependentlyVerified'];checks.append('cold-AJ02-head-bytes-sequence-match-genuine-status-domain-no-signatureclaim')
  pending=magic+intent;snapshot['input']['journal'].update(sequence=1,bytes=len(pending),head=h1,pendingOutcome=True);r=verify_input_tar(tar(pending,snapshot,'pending.tar'),snapshot);assert r['unresolvedIntentSequence']==1;checks.append('durablyclosed-unmatchedintent-preservedUNKNOWN-notHTTPsuccess')
  denied(lambda:verify_input_tar(tar(pending[:-1],snapshot,'torn.tar'),snapshot));checks.append('tornAJ02-no-repair')
  old=json.loads(json.dumps(snapshot));old['input']['journal'].update(sequence=2,bytes=len(journal),head=h2,pendingOutcome=False);current={'processEpoch':'f'*32,'input':{'producerKeyId':'e'*64,'journal':{'format':'AERIS_INPUT_JOURNAL_AJ02','generation':'f'*32,'closed':True,'failed':False,'durablyDrained':True,'sequence':0,'bytes':len(magic),'head':'0'*64,'pendingOutcome':False}}}
  both=LAB/'both.tar'
  def multi(first):
   with tarfile.open(both,'w:')as f:
    for gen,raw in[(old['input']['journal']['generation'],first),(current['input']['journal']['generation'],magic)]:
     info=tarfile.TarInfo('files/product-input01/'+gen+'.aj02');info.size=len(raw);f.addfile(info,io.BytesIO(raw))
   return{'path':str(both),'bytes':both.stat().st_size,'sha256':hashlib.sha256(both.read_bytes()).hexdigest()}
  r=verify_input_tar(multi(journal),current,[old]);assert len(r['generations'])==2 and r['sequence']==0 and r['generations'][0]['signedEnvelopeCount']==1 and r['allSelectedGenerationsClosed']and not r['anyUnresolvedIntent'];checks.append('empty-currentgeneration-cannot-substitute-for-original-closed-historical-inputs')
  changed=bytearray(journal);changed[-1]^=1;denied(lambda:verify_input_tar(multi(bytes(changed)),current,[old]));checks.append('tampered-historical-generation-refused-even-if-current-empty-valid')
  out={'status':'PASS_COLD_SOURCE_BYTE_MOCK_NOT_ANDROID','groups':checks,'actualAndroidAP':False,'scratchRemoved':str(LAB)}
 finally:shutil.rmtree(LAB)
 (REPO/'evidence/betasim-integrated01/runtime/product-seal-bytes-mock.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'groups':len(checks)}))
if __name__=='__main__':main()
