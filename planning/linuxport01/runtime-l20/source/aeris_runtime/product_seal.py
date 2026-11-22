"""Cold byte-backed Root provider seal; not a browser-state acceptance claim."""
from pathlib import Path
import hashlib,json,re
from .product_native import verify_input_tar
from .product_types import is_product_probe,observation_reader
from .metadata_budget import encoded
MAX=64*2**20

def need(v,n):
 if not v:raise ValueError('PRODUCT_SEAL_'+n)
def unique(items):
 out={}
 for k,v in items:need(k not in out,'DUPLICATE_JSON_FIELD');out[k]=v
 return out

def original_rows(path,hash_key=None,previous_key=None,sequence_key=None,zero='0'*64):
 if type(path)is bytes:raw=path
 elif isinstance(path,list):
  from .semantic_journal import decode_files
  raw,_=decode_files(path)
 else:
  need(path.is_file()and not path.is_symlink()and path.stat().st_size<=MAX,'ORIGINAL_FILE_BOUND');raw=path.read_bytes()
 need(raw and raw.endswith(b'\n'),'COMPLETE_ORIGINAL_JOURNAL');rows=[];head=zero
 for line in raw.splitlines():
  need(len(rows)<32768 and len(line)<=65536,'RECORD_BOUND');row=json.loads(line,object_pairs_hook=unique)
  if hash_key:
   # Remove the root hash token while retaining EXACT original number/string
   # lexemes. Python and JavaScript serialize small/exponent floats differently.
   text=line.decode();decoder=json.JSONDecoder(object_pairs_hook=unique);i=1;span=None
   while i<len(text)-1:
    begin=i;key,end=decoder.raw_decode(text,i);need(text[end]==':','ROOT_KEY_COLON');_,value_end=decoder.raw_decode(text,end+1)
    if key==hash_key:span=(begin-1,value_end)if begin>1 else(begin,value_end+1)
    i=value_end+1
   need(span is not None,'ROOT_HASH_TOKEN');body=(text[:span[0]]+text[span[1]:]).encode();need(hashlib.sha256(body).hexdigest()==row[hash_key]and row[previous_key]==head,'ORIGINAL_HASH_CHAIN');head=row[hash_key]
  if sequence_key:need(type(row[sequence_key])is int and row[sequence_key]==len(rows)+1,'ORIGINAL_SEQUENCE')
  rows.append(row)
 return raw,rows,head

def verify_product_seal(owner,case,scenario):
 need(is_product_probe(case['native']) and case['writer'].failure is None and case['writer'].inflight is None,'GENUINE_SOURCE_PROBE_AND_NO_PENDING_ROOT_WRITE');context=case['context'];short={k:context[k]for k in('run','epoch','boot','operator','generation')};product=case['root']/'product';source=case.get('productSourceSeal');need(type(source)is dict and source.get('format')=='aeris-betasim-product-source-seal'and source.get('authorityRestorable')is False,'GENUINE_OWNED_COMPANION_SOURCE_SEAL_ACK');closed=source['product'];need(closed.get('closed')is True and closed.get('context')==short and closed.get('owner',{}).get('phase')=='CLOSED'and closed['owner'].get('owner')is None,'SOURCE_OWNER_CLOSED_STATE')
 wal,records,walhead=original_rows(product/'journal/workspace.jsonl','hash','previousHash','seq');reviews=[r['data']for r in records if r['kind']=='BETA_FLIGHT_REVIEW'];need(reviews,'ORIGINAL_REVIEW_WAL');review=reviews[-1];segments=review['flightClose']['journal']['segments'];need(1<=len(segments)<=8 and all(r.get('closed')is True for r in segments),'SOURCE_FLIGHT_CLOSED_SEGMENT_REFS');paths=[]
 for row in segments:
  name=row['file'];need(type(name)is str and re.fullmatch(r'journal/flight-[a-f0-9-]{36}-s[0-9]{2}\.ajz01',name)is not None,'EXACT_SOURCE_FLIGHT_FILE_NAME');path=product/name;need(path.stat().st_size==row['storedBytes'],'SOURCE_FLIGHT_SEGMENT_BYTES');paths.append(path)
 flight,rows,head=original_rows(paths,'sha256','previous','n',zero='');need(len([r for r in rows if r['kind']=='ROOT_WIRE_SESSION'and r['data']['context']['context']==short])==1 and rows[-1]['kind']=='LINK_CLOSE','EXACT_ROOT_SESSION_TERMINAL');need(rows[-1]['data']['failure']is None,'FAILURE_NOT_NOMINAL_SEAL');need(review['flightClose']['journal']['head']==head and review['flightClose']['journal']['records']==len(rows),'CLOSED_FLIGHT_RECEIPT_ORIGINAL_HEAD')
 owner_name=closed.get('ownerJournal');need(type(owner_name)is str and re.fullmatch(r'journal/product-owner-[a-f0-9]{16}\.jsonl',owner_name)is not None,'EXACT_SOURCE_OWNER_JOURNAL');owner_path=product/owner_name;ownerraw,owners,_=original_rows(owner_path,sequence_key='sequence');last=owners[-1];need(last['kind']=='PROVIDER_CLOSED'and last['body']['proof']['context']==short and last['body']['proof']['authorityRevoked']is True and last['body']['proof']['providerClosed']is True and last['body']['proof']['durablyDrained']is True,'GENUINE_OWNER_CLOSED_NO_AUTHORITY');need(review['run']==context['run']and review['boot']==context['boot']and review['missionSHA256']==last['body']['proof']['missionSHA256']==closed['owner']['missionSHA256'],'REVIEW_SOURCE_BINDING');snapshot=case['native'].latest;inp=snapshot['input'];need(inp['configured']is False and inp['pending']is False and inp['closed']is True and inp['failed']is False and inp['journal']['durablyDrained']is True,'SOURCE_NATIVE_INPUT_CLOSED');native=case['native'].closed_export;need(native is not None,'COLD_ORIGINAL_NATIVE_TAR_REQUIRED');native_journal=verify_input_tar(native['export'],snapshot,[r['snapshot']for r in case['native'].archived_lifecycles]);native_observations=observation_reader(owner.manifest)(case['device'].store.root,owner.manifest)
 crypto=case.get('nativeCryptoProof');need(type(crypto)is dict and crypto.get('format')=='aeris-native-signature-semantic-verification'and crypto.get('version')==1 and crypto.get('status')=='VERIFIED_SELECTED_NATIVE_SIGNATURES_AND_SEMANTIC_REFS'and crypto.get('physicalHIDAttested')is False and crypto.get('flightAcceptance')is False,'SOURCE_COLD_NATIVE_CRYPTO_RESULT_REQUIRED');ref=crypto.get('originalRef');need(type(ref)is dict and ref.get('offset')==0 and 0<ref.get('bytes',0)<=4096 and ref.get('path')==str((product/'reports/native-signature-semantic-verification.json').relative_to(owner.root)),'ORIGINAL_NATIVE_CRYPTO_REPORT_REF');proofpath=owner.root/ref['path'];proofraw=proofpath.read_bytes();need(not proofpath.is_symlink()and len(proofraw)==ref['bytes']and hashlib.sha256(proofraw).hexdigest()==ref['sha256']and json.loads(proofraw,object_pairs_hook=unique)=={k:v for k,v in crypto.items()if k!='originalRef'},'ORIGINAL_NATIVE_CRYPTO_REPORT_BYTES');need(crypto['descriptorSHA256']==case['nativeClosedDescriptor']['descriptorSHA256']and crypto['originalNativeTARSHA256']==native['export']['sha256']and crypto['selectedGenerations']==len(native_journal['generations']),'ALL_GENERATION_CRYPTO_TAR_DESCRIPTOR_JOIN');need(crypto['unresolvedIntentGenerations']==[]and crypto['unclosedGenerationPrefixes']==[]and native_journal['allSelectedGenerationsClosed']and not native_journal['anyUnresolvedIntent'],'UNRESOLVED_NATIVE_INPUT_NOT_NOMINAL_SEAL');need(crypto['matchedRootTransactions']>0,'ACTUAL_SIGNED_MANUAL_TRANSACTIONS_REQUIRED')
 nominal=bool(review.get('accepted')and rows[-1]['data']['completion'].get('complete')and native_journal['allSelectedGenerationsClosed']and not native_journal['anyUnresolvedIntent'])
 seal={'format':'aeris-root-verified-workbench-seal','version':1,'runtimeContext':context,'candidateSHA256':owner.digest,'authorityRevoked':True,'providerClosed':True,'journalClosed':True,'productJournalSHA256':hashlib.sha256(flight).hexdigest(),'productJournalHead':head,'productJournalEncoding':'AJZ01_EXACT_DECODED_ORIGINAL_UTF8_SHA256','productJournalFiles':[{'path':str(p.relative_to(case['root'])),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in paths],'workspaceJournalSHA256':hashlib.sha256(wal).hexdigest(),'workspaceHead':walhead,'ownerJournalSHA256':hashlib.sha256(ownerraw).hexdigest(),'ownerJournalPath':str(owner_path.relative_to(case['root'])),'missionSHA256':review['missionSHA256'],'nativeClosedExport':native,'nativeInputColdJournal':native_journal,'nativeOriginalObservations':{'count':native_observations['count'],'status':native_observations['status']},'nominalOutcomeEligible':nominal,'nativeSignatureSemanticVerification':crypto,'signedInputSemanticIndependentVerification':'SOURCE_COLD_CRYPTO_AND_REF_JOIN_VERIFIED_FINAL_INDEPENDENT_ACCEPTANCE_REQUIRED','flightAcceptance':False,'sourceDerivedNoUIBooleanAcceptance':True};owner.write('product-'+context['run']+'-seal.json',seal);return seal
