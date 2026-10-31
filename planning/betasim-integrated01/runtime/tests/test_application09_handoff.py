"""Execute selected handoff source with memory SDK/receiver stubs.
Proof is flow/argv only, NOT real SAF bytes or independent receiver acceptance.
"""
from pathlib import Path
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch
import hashlib,importlib.util,io,json,sys
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)]
from aeris_runtime.metadata_budget import encoded
spec=importlib.util.spec_from_file_location('application09_handoff_source',T/'scenario-app09.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
CONTEXT={'run':'case','epoch':'e'*32,'boot':'b'*32,'operator':'A','generation':'g','profileId':'WORKBENCH_SIM_V1'};CANDIDATE='c'*64
manifest={'format':'aeris-betasim-closed-raw-manifest','authorityRestorable':False,'context':CONTEXT,'sourceCandidateSHA256':CANDIDATE,'bundle':{'parts':[{'index':0}]},'nativeStream':{'parts':[{'index':0}]}};original=encoded(manifest);digest=hashlib.sha256(original).hexdigest();parts=[{'stream':'bundle','index':0},{'stream':'native-closed-files','index':0}]
class Device:
 def __init__(self):self.budget=SimpleNamespace(mock=False);self.store=SimpleNamespace(root=Path('/MEMORY_ONLY'));self.argv=[];self.rows=[]
 @contextmanager
 def open_saf_document(self,cap,**kw):
  self.argv.append(['/fake/adb','-s','emulator-5582','exec-out','content','read','--uri',cap.uri]);yield io.BytesIO(original if cap.stream=='manifest'else b'MEMORY_STUB');self.rows.append({'format':'aeris-native-saf-recipient-stream','nativeManifestSHA256':digest,'stream':cap.stream,'index':cap.index,'completeOriginalStream':True,'bothOriginalPipeEOF':True,'failure':None,'exit':0})
class UI:
 def __init__(self):self.success=0;self.actions=[]
 def get(self,*a):return {'ok':True,'result':{'ready':True,'parts':parts}},None,None
 def native(self,*a):return {'exportBudget':{'successCount':self.success}}
 def tap(self,key):self.actions.append(key)
 def save_dialog(self):self.success+=1
class Owner:
 digest=CANDIDATE
 def __init__(self):self.reportNames=[]
 def write(self,name,report):self.reportNames.append(name)
def main():
 device=Device();ui=UI();owner=Owner();probe=SimpleNamespace(saf_document=lambda stream,index:SimpleNamespace(stream=stream,index=index,uri='content://com.android.externalstorage.documents/document/MOCK-'+stream+'-'+str(index)));case={'uiDriver':ui,'native':probe,'device':device,'context':CONTEXT}
 def receiver_stub(raw,**kw):
  assert raw==original and kw['expected_context']==CONTEXT and kw['expected_candidate']==CANDIDATE
  for opener in[*kw['bundle_openers'],*kw['native_openers']]:
   with opener()as f:assert f.read(65536)==b'MEMORY_STUB'
  return {'RECEIVER_IS_MOCK_NOT_ACCEPTANCE':True}
 with patch('aeris_runtime.saf_receiver.verify_recipient',side_effect=receiver_stub),patch('aeris_runtime.once_reader.read_receipts',side_effect=lambda *a:device.rows):result=m.handoff(owner,case,{'manifestSHA256':digest},lambda:None)
 assert len(device.argv)==3 and all(a[1:6]==['-s','emulator-5582','exec-out','content','read']for a in device.argv);assert ui.actions==['beta-export-raw','raw-part-bundle-0','raw-part-native-closed-files-0'];assert owner.reportNames==['recipient-independent-byte-verification.json'];assert result['receiver']['RECEIVER_IS_MOCK_NOT_ACCEPTANCE']is True
 out=R/'evidence/betasim-integrated01/runtime/application09-handoff-trace01.json';assert not out.exists();report={'format':'aeris-development-application09-source-handoff-flow','status':'PASS_SELECTED_SOURCE_FLOW_MEMORY_STUBS_NOT_SAF_BYTE_OR_RECEIVER_ACCEPTANCE','scenarioSHA256':hashlib.sha256((T/'scenario-app09.py').read_bytes()).hexdigest(),'publicUIActions':ui.actions,'plannedContentReadArgv':device.argv,'streamsReached':[r['stream']for r in device.rows],'sourceReportHookReached':owner.reportNames,'sourceBooleanClaimsInsideMockAreNotAcceptance':True,'receiverStub':True,'genuineNativeReceiptURI':False,'actualSAFBytesVerified':False,'actorsStarted':False,'filesWrittenByMockOwner':0};out.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':main()
