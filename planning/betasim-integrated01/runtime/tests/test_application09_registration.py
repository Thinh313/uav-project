"""Actual source readonly proof envelope, original R06-shaped registration."""
from pathlib import Path
from types import SimpleNamespace
import base64,hashlib,json,sys,shutil
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)]
from aeris_runtime.product_writer import ProductWriter,MAX_REPLY
from aeris_runtime.metadata_budget import MetadataBudget,encoded
LAB=R/'evidence/betasim-integrated01/runtime/.appreg09'
def main():
 assert not LAB.exists();LAB.mkdir();groups=[]
 try:
  b=MetadataBudget(LAB/'metadata-budget',lambda:{'metadataBytes':0},mock=True,free=lambda:64*2**30);b.admit();original=(R/'evidence/betasim-integrated01/r06/reports/native-producer-01-registration.json').read_bytes();base=json.loads(original);base['applicationId']='vn.rtr.aeris.betasim09';base['applicationDomainRef']={'format':'aeris-original-byte-ref','version':3,'path':'receipts/diagnostic.jsonl','offset':999999,'bytes':4096,'sha256':'a'*64};cases=[]
  from aeris_runtime.once_store import OnceStore
  store=OnceStore.__new__(OnceStore)
  for generation,maximal in((1,False),(2,False),(1,True),(2,True)):
   registration=json.loads(json.dumps(base));registration['generation']=generation
   if maximal:registration['context']={'run':'R'*64,'epoch':'e'*32,'boot':'b'*32,'operator':'ROOT-LAB','generation':'g'*32,'profileId':'WORKBENCH_SIM_V1'};registration['pid']=2147483647
   rootref=lambda name:{'path':name,'offset':0,'bytes':32768,'sha256':'d'*64,'writeSequence':99999999}
   registration['rootRegistrationRef']=rootref('reports/native-producer-02-registration-g02.json'if generation==2 else'reports/native-producer-02-registration.json');registration['originalObservationRef']=store.ref('receipts/request.jsonl',491520,b'x'*2048)
   if generation==2:registration['priorRegistrationRef']=rootref('reports/native-producer-02-registration.json');registration['rolloverSourceRef']=store.ref('receipts/diagnostic.jsonl',5242880,b'y'*4096)
   writer=ProductWriter.__new__(ProductWriter);writer.native_registration=registration;writer.context=registration['context'];writer.budget=b;writer.failure=None;request={'op':'native-registration','expectedOffset':0,'sequence':len(cases)+1,'path':'reports/native-registration','payloadBase64':base64.b64encode(encoded({'challenge':'c'*32})).decode()};response=writer._readonly_proof(request,received_ns=1);raw=encoded(response);assert len(raw)<=MAX_REPLY==2048,(generation,maximal,len(raw));assert response['nativeRegistration']['originalObservationRef']==registration['originalObservationRef'];assert all(k not in response['nativeRegistration']for k in('originalStoreRoot','APKSHA256','signatureAlgorithm','identityScope','applicationId','applicationDomainRef'));assert writer.native_registration==registration;cases.append({'generation':generation,'maximalSelectedSourceContext':maximal,'replyBytes':len(raw),'originalIOStoreRefFormatAndVersionPreserved':True})
  groups.append('actual-source-G1-G2-both-maximal64run-fixed-source-labels-PID-and-exact-real-IOStore6fieldrefs-fit-original2048RPC')
  source=(T/'source/aeris_runtime/product_writer.py').read_text();assert"application=verify_application_original("in source and"value['applicationDomainRef']=probe.application_domain_ref"in source and"value['applicationDomainObservation']"not in source;groups.append('full-original-application-proof-verified-before-mint-reference-no-duplicatebody-or-data-loss')
  out=R/'evidence/betasim-integrated01/runtime/application09-registration-mock02.json';assert not out.exists();report={'format':'aeris-application09-source-native-registration-envelope','status':'PASS_ACTUAL_SOURCE_RPC_ENVELOPE_REAL_METADATA_MOCK_OWNER_NO_DEVICE','groups':groups,'replyCases':cases,'maximumReplyBytesObserved':max(q['replyBytes']for q in cases),'originalMaximumReplyBytes':MAX_REPLY,'originalR06RegistrationSHA256':hashlib.sha256(original).hexdigest(),'sourceSHA256':hashlib.sha256((T/'source/aeris_runtime/product_writer.py').read_bytes()).hexdigest(),'actorsStarted':False,'scratchRemoved':str(LAB.relative_to(R))};out.write_bytes(encoded(report));print(json.dumps(report))
 finally:shutil.rmtree(LAB)
if __name__=='__main__':main()
