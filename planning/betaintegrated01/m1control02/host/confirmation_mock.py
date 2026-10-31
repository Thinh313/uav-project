"""Closed real native journal tests; mutations are descriptors only, no raw edits."""
from pathlib import Path
import sys,json,copy,hashlib
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.control04.confirmation import verify_confirmation,descriptor_sha256

def main():
 p=R/'evidence/betaintegrated01-m1control02/host/old-regression01/derived-loss05-confirmation-descriptor.json';d=json.loads(p.read_text());b=d['hostBracket'];cases=[]
 assert verify_confirmation(d,descriptor_sha256(d),b['run'],b['epoch'],b['boot'])['nativeIntegrity']=='PASS_EXTERNAL_ANCHOR';cases.append({'case':'exact_closed_native_and_reconstructed_root_bracket','status':'PASS'})
 for name,mut in [('wrong_explicit_record',lambda x:x.update(confirmationRecordSHA256='0'*64)),('foreign_generation',lambda x:x['hostBracket'].update(generation='foreign')),('wrong_displayed_hash',lambda x:x['hostBracket'].update(displayedHomeHash='0'*64)),('bracket_reordered',lambda x:x['hostBracket'].update(beforeActionHostNs=x['hostBracket']['afterObservedConfirmedHostNs']+1)),('bracket_over5seconds',lambda x:x['hostBracket'].update(afterObservedConfirmedHostNs=x['hostBracket']['beforeActionHostNs']+5_000_000_001)),('bracket_boolean_clock',lambda x:x['hostBracket'].update(beforeActionHostNs=True)),('wrong_native_external_anchor',lambda x:x.update(nativeExternalAnchor='0'*64)),('extra_claimedHome_not_schema',lambda x:x.update(claimedHome={'latE7':0}))]:
  changed=copy.deepcopy(d);mut(changed)
  try:verify_confirmation(changed,descriptor_sha256(changed),b['run'],b['epoch'],b['boot']);raise RuntimeError('MUST_REJECT:'+name)
  except(ValueError,AssertionError,KeyError):cases.append({'case':name,'status':'PASS'})
 try:verify_confirmation(d,'0'*64,b['run'],b['epoch'],b['boot']);raise RuntimeError('ANCHOR_MUST_REJECT')
 except ValueError:cases.append({'case':'external_descriptor_anchor_mismatch','status':'PASS'})
 out=R/'evidence/betaintegrated01-m1control02/host/confirmation-mock01';out.mkdir()
 (out/'results.json').open('x').write(json.dumps({'status':'PASS_CLOSED_NATIVE_CONFIRMATION_BINDING','groups':len(cases),'cases':cases,'sourceDescriptorSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'oldRawOrReceiptsEdited':False,'servicesStarted':0},indent=2)+'\n');print(json.dumps({'status':'PASS','groups':len(cases)}))
if __name__=='__main__':main()
