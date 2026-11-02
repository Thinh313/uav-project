"""Same raw fixtures through independent Python/Node selected profile, no SDK actors."""
from pathlib import Path
import hashlib,io,json,os,subprocess,sys,tarfile,tempfile,unittest
B=Path(__file__).resolve().parent;R=B.parents[2];os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(B/'source'),str(R)]
from planning.betarc01.tar_profile_h7 import reader as c
from planning.nativejournal17.receiver17 import validate_tar_shape as old_strict
from aeris_runtime.reconcile_h7 import reconcile
RAW=R/'evidence/betarc01/m501/sessions/beta-rc01-sdk-reconcile01/native-restart-metadata.tar';SHA='1963cd4a2cf2658bd9f55384c1a6bca54f6bbe77e62955e19d02a82d08a911e1';C=R/'evidence/nativejournal17/candidates/c297542deab30c49ad528db1df8dc34cc9e4954ac0065d616afcfbc1e50df6b4'
def patch_header(raw,at,changes):
 out=bytearray(raw);h=bytearray(raw[at:at+512])
 for start,data in changes:h[start:start+len(data)]=data
 h[148:156]=b' '*8;h[148:156]=('%06o'%sum(h)).encode()+b'\0 ';out[at:at+512]=h;return bytes(out)
def node(paths):
 script="""import{scanNativeTarFile}from'./planning/betarc01/tar_profile_h7/native-tar.mjs';const out=[];for(const p of JSON.parse(process.argv[1])){try{out.push({accepted:true,result:await scanNativeTarFile(p)});}catch(e){out.push({accepted:false,error:String(e)});}}console.log(JSON.stringify(out));"""
 p=subprocess.run(['/usr/local/bin/node','--input-type=module','-e',script,json.dumps([str(x)for x in paths])],cwd=R,capture_output=True,timeout=10);assert p.returncode==0 and not p.stderr,p.stderr;return json.loads(p.stdout)
class Wire(unittest.TestCase):
 def test_actual_direct_raw_parity_full_semantics_and_old_failure_preserved(self):
  before=(c.hash_file(RAW),RAW.stat().st_ino,RAW.stat().st_size,RAW.stat().st_mode)
  self.assertEqual(before[0],SHA)
  with self.assertRaisesRegex(ValueError,'TAR_NO_LINK_OR_EXTENSION'):old_strict(RAW)
  py=c.scan(RAW);js=node([RAW])[0];self.assertTrue(js['accepted']);j=js['result']['transportProfile'];self.assertEqual((j['logicalMembers'],j['physicalHeaders'],j['longnameMetadataCarriers'],j['rawSHA256'],j['logicalBytes']),(84,94,10,SHA,161406));self.assertEqual(py['transportHeaders'],j['physicalHeaders']);self.assertEqual(py['logicalBytes'],j['logicalBytes'])
  m=json.loads((C/'candidate.json').read_bytes());v=reconcile(RAW,SHA,source_candidate=C.name,native_apk_sha=m['native']['APK_SHA256'],native_source_sha=m['native']['sourceSHA256']);self.assertEqual(v['pendingTransactions'],0);self.assertEqual(v['registryProof']['archivedJournals'],8);self.assertFalse(v['flightAcceptance']);self.assertFalse(v['tarTransportProfile']['derivedViewCreated'])
  with self.assertRaisesRegex(ValueError,'TAR_NO_LINK_OR_EXTENSION'):old_strict(RAW)
  self.assertEqual(before,(c.hash_file(RAW),RAW.stat().st_ino,RAW.stat().st_size,RAW.stat().st_mode))
 def test_joint_negative_corpus(self):
  raw=RAW.read_bytes();e=next(x for x in c.scan(RAW)['entries']if x['longname']);L=e['longname'];at=L['headerOffset'];regular=e['headerOffset'];end=at+512+((L['payloadBytes']+511)//512)*512;cases={'empty':bytes(1024)}
  for label,kind in [('K',b'K'),('pax',b'x'),('globalPax',b'g'),('sparse',b'S'),('device',b'3'),('fifo',b'6'),('symlink',b'2'),('hardlink',b'1')]:cases[label]=patch_header(raw,at,[(156,kind)])
  cases['chain']=raw[:at]+raw[at:end]+raw[at:];cases['orphan']=raw[:end]+bytes(1024);cases['prefix']=patch_header(raw,regular,[(0,b'X')]);cases['checksum']=bytes([raw[0]^1])+raw[1:];bad=bytearray(raw);bad[end-1]=1;cases['padding']=bytes(bad);cases['truncated']=raw[:at+520];cases['tail']=raw+b'X';cases['missingEOA']=raw[:-1024];cases['nonzeroLink']=patch_header(raw,regular,[(157,b'files/secret\0')]);cases['Ldirectory']=patch_header(raw,regular,[(156,b'5')]);bad=bytearray(raw);bad[at+512+L['payloadBytes']-1]=88;cases['noNUL']=bytes(bad);cases['octalHighBit']=patch_header(raw,regular,[(108,b'\xb0')]);cases['reserved']=patch_header(raw,regular,[(500,b'X')]);cases['BOMpath']=patch_header(raw,0,[(0,b'\xef\xbb\xbffiles\0')]);cases['magic']=patch_header(raw,regular,[(257,b'BADMAGIC')]);cases['deviceMetadata']=patch_header(raw,regular,[(329,b'0000001\0')])
  for label,prefix in [('traversal',b'files/../'),('absolute',b'/etc/../'),('emptycomponent',b'files//')]:
   name=prefix+b'a'*(L['payloadBytes']-1-len(prefix));bad=bytearray(raw);bad[at+512:at+512+len(name)]=name;cases[label]=patch_header(bad,regular,[(0,name[:100])])
  d=next(x for x in c.scan(RAW)['entries']if x['type']=='regular'and not x['longname']);cases['duplicate']=raw[:-1024]+raw[d['headerOffset']:d['bodyOffset']+((d['bytes']+511)//512)*512]+bytes(1024)
  with tempfile.TemporaryDirectory(prefix='wire-',dir=B)as tmp:
   paths=[]
   for name,data in cases.items():
    p=Path(tmp)/(name+'.tar');p.write_bytes(data);paths.append(p)
    with self.subTest(name=name),self.assertRaises(c.CodecError):c.scan(p)
   result=node(paths)
   for name,row in zip(cases,result):self.assertFalse(row['accepted'],(name,row))
 def test_receiver192_stat_bound_and_producer_unchanged(self):
  with tempfile.TemporaryDirectory(prefix='wire-',dir=B)as tmp:
   p=Path(tmp)/'over-limit.tar'
   with p.open('wb')as f:f.truncate(192*2**20+1)
   with self.assertRaises(c.CodecError):c.scan(p)
   self.assertFalse(node([p])[0]['accepted'])
  H6=R/'planning/betarc01/runtime-h6/source/aeris_runtime'
  for n in ['android.py','metadata_budget.py','inventory.py','guest_sync_h4.py','emulator.py','candidate.py','assets/resource-policy.json']:self.assertEqual((B/'source/aeris_runtime'/n).read_bytes(),(H6/n).read_bytes())
if __name__=='__main__':unittest.main(verbosity=2)
