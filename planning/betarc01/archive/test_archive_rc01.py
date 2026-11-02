"""Pure registry/receipt/owned offline-child faults, not Android qualification."""
from pathlib import Path
import ast,base64,copy,hashlib,json,os,struct,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT),str(ROOT/'planning/betarc01/runtime/source')]
from planning.betarc01.archive.archive_rc01 import _verify_original_index
from planning.betarc01.archive.common_rc01 import canonical,sha
from planning.betarc01.archive.receiver_rc01 import qualify_active
from planning.betarc01.archive.offline_capture import capture
from planning.betarc01.archive.maintenance_rc01 import _conserved
from planning.nativejournal17.receiver17 import MAGIC,aj02
ZERO='0'*64

def fixture():
    files={};head=ZERO;lines=[b'AERIS_JOURNAL_REGISTRY17_V1\n'];n=0;reports={}
    def emit(kind,parts):
        nonlocal head,n
        n+=1;pre='\t'.join([str(n),head,kind,base64.b64encode('\t'.join(parts).encode()).decode()]);head=sha(pre.encode());lines.append((pre+'\t'+head+'\n').encode());return head
    def original(g,raw,disposition,proof):return {'generation':g,'bytes':len(raw),'sha256':sha(raw),'disposition':disposition,'proofSHA256':proof}
    def group(rows):return [str(len(rows))]+[x for q in rows for x in [q['generation'],str(q['bytes']),q['sha256'],q['disposition'],q['proofSHA256']]]
    initial=[original(f'{i:032x}',MAGIC,'UNUSED','a'*64)for i in range(1,9)]
    ticket=emit('ENROLL_BEGIN',['d'*64,'e'*64,'f'*64]+group(initial));emit('ENROLL_COMMIT',[ticket]+[x for q in initial for x in[q['generation'],'0','1']])
    def batch(rows,nonce,first):
        request=emit('REQUEST_RESERVE',[nonce,'APPLY','1'if first else'0'])
        report={'format':'aeris-journal17-independent-full-byte-receiver','version':1,'status':'COMPLETE_COLD_BACKUP_AND_ORIGINAL_GENERATIONS_VERIFIED_NOT_FLIGHT','package':'vn.rtr.aeris.betasim09','oldAPKSHA256':'a'*64,'oldSourceSHA256':'b'*64,'newSourceSHA256':'b'*64,'backupSHA256':'d'*64,'backupBytes':10240,'coldProofSHA256':'f'*64,'expectedHostRegistryHead':'ROOT'if first else head,'originals':[{**q,'records':0 if first else 2,'sourceClosedStatusBound':not first}for q in rows],'authorityRestorable':False}
        raw=canonical(report)+b'\n';rh=sha(raw);reports[rh]=raw
        plan=('\n'.join(['AERIS_JOURNAL_LIFECYCLE17\t1','package\tvn.rtr.aeris.betasim09','oldAPK\t'+'a'*64,'oldSource\t'+'b'*64,'newSource\t'+'b'*64,'backup\t'+'d'*64+'\t10240','receiver\t'+rh,'cold\t'+'f'*64,'expectedHead\t'+report['expectedHostRegistryHead']]+['generation\t'+'\t'.join([q['generation'],str(q['bytes']),q['sha256'],q['disposition'],q['proofSHA256']])for q in rows]+['end',''])).encode()
        ph=sha(plan);ticket=emit('ARCHIVE_BEGIN',[ph]+group(rows));base='files/product-input-archives17/'+ph+'/'
        commit=('AERIS_JOURNAL17_COMMITTED\t'+ph+'\t'+rh+'\n').encode();files[base+'intent-0.record']=plan;files[base+'commit-0.record']=commit
        for q in rows:files[base+q['generation']+'.aj02']=files.pop('files/product-input01/'+q['generation']+'.aj02')
        emit('ARCHIVE_COMMIT',[ticket,'product-input-archives17/'+ph,'intent-0.record',ph,str(len(plan)),'commit-0.record',sha(commit),str(len(commit))])
        receipt=b'{}';name='product-input-lifecycle17/request-'+nonce+'.json';files['files/'+name]=receipt;emit('REQUEST_RECEIPT',[request,nonce,name,str(len(receipt)),sha(receipt)])
    for q in initial:files['files/product-input01/'+q['generation']+'.aj02']=MAGIC
    batch(initial,'a'*32,True)
    g=f'{9:032x}';ticket=emit('GEN_BEGIN',[g]);emit('GEN_COMMIT',[ticket,g,str(len(MAGIC)),ZERO,'0','9']);raw=MAGIC;prior=bytes(32)
    for number,kind,payload in [(1,1,b'{"synthetic":true}'),(2,2,b'200')]:
        body=struct.pack('!QQB',number,100+number,kind)+prior+payload;digest=hashlib.sha256(body).digest();row=struct.pack('!I',len(body)+32)+body+digest;ticket=emit('APPEND_BEGIN',[g,str(number),str(len(raw)),str(len(raw)+len(row)),sha(row),digest.hex()]);emit('APPEND_COMMIT',[ticket,str(100+number),str(number%2)]);raw+=row;prior=digest
    emit('CLOSE',[g,'2',str(len(raw)),prior.hex(),'CLOSED_VERIFIED',sha(raw),ZERO]);files['files/product-input01/'+g+'.aj02']=raw
    proof={**original(g,raw,'CLOSED_VERIFIED','e'*64),'records':2,'head':prior.hex(),'sourceClosedStatusBound':True,'authorityRestorable':False,'APKSHA256':'a'*64,'sourceSHA256':'b'*64}
    batch([original(g,raw,'CLOSED_VERIFIED',proof['proofSHA256'])],'b'*32,False)
    files['files/product-input-registry17/highwater.aj17']=b''.join(lines)
    scan={'inputOriginals':files,'files':{k:{'bytes':len(v),'sha256':sha(v)}for k,v in files.items()},'tarSHA256':'9'*64,'inputBytes':sum(map(len,files.values()))}
    return scan,head,reports,{g:proof}

class Archive(unittest.TestCase):
    def verify(self,scan,head,reports,proofs):return _verify_original_index(scan,head,source_candidate='c'*64,archive_receivers=reports,closed_proofs=proofs)
    def test_used_index_structural_positive(self):
        scan,head,reports,proofs=fixture();result=self.verify(scan,head,reports,proofs);self.assertEqual(result['archivedJournals'],9);self.assertEqual(result['activeJournals'],0);self.assertFalse(result['flightAcceptance'])
    def test_used_requires_proof(self):
        s,h,r,p=fixture()
        with self.assertRaisesRegex(ValueError,'ORIGINAL_ROOT_APPROVED'):self.verify(s,h,r,{})
    def test_wrong_proof_each_original_field(self):
        for field in ['sha256','head','records','bytes','proofSHA256','APKSHA256','sourceSHA256']:
            s,h,r,p=fixture();q=next(iter(p.values()));q[field]=0 if field in('records','bytes')else'0'*64
            with self.subTest(field=field),self.assertRaises(ValueError):self.verify(s,h,r,p)
    def test_closed_cannot_be_unused(self):
        s,h,r,p=fixture();next(iter(p.values()))['disposition']='UNUSED'
        with self.assertRaises(ValueError):self.verify(s,h,r,p)
    def test_zero_and_foreign_head(self):
        for h in [ZERO,'7'*64]:
            s,_,r,p=fixture()
            with self.assertRaisesRegex(ValueError,'EXTERNAL_HOST_HEAD'):self.verify(s,h,r,p)
    def test_missing_original_and_receipt(self):
        for kind in ['aj02','request']:
            s,h,r,p=fixture();name=next(n for n in s['inputOriginals']if(n.endswith('.aj02')if kind=='aj02'else'/request-'in n));del s['inputOriginals'][name]
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.verify(s,h,r,p)
    def test_original_receiver_required(self):
        s,h,r,p=fixture()
        with self.assertRaisesRegex(ValueError,'RECEIVER_ORIGINALS'):self.verify(s,h,{},p)
    def test_unresolved_active_cannot_rotate(self):
        g='9'*32;raw=MAGIC;body=struct.pack('!QQB',1,1,1)+bytes(32)+b'{}';raw+=struct.pack('!I',len(body)+32)+body+hashlib.sha256(body).digest();decoded={'raw':raw,'sha256':sha(raw),**aj02(raw)}
        with self.assertRaisesRegex(ValueError,'UNRESOLVED'):qualify_active({'journals':{g:decoded}},{'native':{}},{})
    def test_used_active_requires_current_full_proof(self):
        _,_,_,proofs=fixture();g,p=next(iter(proofs.items()));row={'raw':b'used','unresolvedIntent':None,**{k:p[k]for k in('bytes','sha256','head','records')}}
        with self.assertRaisesRegex(ValueError,'USED_CURRENT'):qualify_active({'journals':{g:row}},{'native':{'APK_SHA256':'a'*64,'sourceSHA256':'b'*64}}, {})
    def test_live_paths_have_no_process_creation(self):
        forbidden={'Popen','run','call','check_call','check_output','system','spawn','execv','execve'}
        for name in ['closed_sources.py','common_rc01.py','archive_rc01.py','receiver_rc01.py']:
            tree=ast.parse((Path(__file__).parent/name).read_text());calls={getattr(n.func,'attr','')for n in ast.walk(tree)if isinstance(n,ast.Call)};self.assertFalse(calls&forbidden,(name,calls&forbidden))
    def test_original_conservation_no_deletion(self):
        before={'files':{'files/workspace':{'bytes':1,'sha256':'a'},'files/product-input01/'+'1'*32+'.aj02':{'bytes':23,'sha256':'b'},'files/product-input-registry17/highwater.aj17':{'bytes':1,'sha256':'c'}},'inputOriginals':{'files/product-input-registry17/highwater.aj17':b'a'}}
        after={'files':{'files/workspace':{'bytes':1,'sha256':'a'},'files/product-input-archives17/p/'+'1'*32+'.aj02':{'bytes':23,'sha256':'b'}},'inputOriginals':{'files/product-input-registry17/highwater.aj17':b'ab'},'journals':{}}
        self.assertTrue(_conserved(before,after));del after['files']['files/workspace']
        with self.assertRaisesRegex(ValueError,'PRIOR_PRIVATE'): _conserved(before,after)

class OfflineCapture(unittest.TestCase):
    def test_complete_offline_child(self):
        q,out,err=capture([sys.executable,'-B','-c','import sys;print(sys.stdin.read())'],b'{}',cwd=ROOT,seconds=2);self.assertTrue(q['captureComplete']);self.assertTrue(q['ownedChildExited']);self.assertEqual(out,b'{}\n');self.assertEqual(err,b'')
    def test_timeout_and_overflow(self):
        for code,bound in [('import time;time.sleep(3)',.05),('import sys;sys.stdout.write("x"*40000);sys.stdout.flush()',2)]:
            q,out,err=capture([sys.executable,'-B','-c',code],b'{}',cwd=ROOT,seconds=bound);self.assertFalse(q['captureComplete']);self.assertTrue(q['ownedChildExited']);self.assertIsNotNone(q['failure']);self.assertLessEqual(len(out),32769)
    def test_capture_setup_failure_closes_owned_child(self):
        with patch('planning.betarc01.archive.offline_capture.os.set_blocking',side_effect=OSError('injected setup')):
            q,out,err=capture([sys.executable,'-B','-c','import time;time.sleep(3)'],b'{}',cwd=ROOT,seconds=2)
        self.assertFalse(q['captureComplete']);self.assertTrue(q['ownedChildExited']);self.assertIn('injected setup',q['failure']);self.assertFalse(q['cleanupErrors'])

if __name__=='__main__':unittest.main(verbosity=2)
