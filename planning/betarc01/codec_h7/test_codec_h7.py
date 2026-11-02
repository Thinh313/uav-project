"""Offline prototype adversaries. Old m501 remains failed; no SDK/device actors."""
from pathlib import Path
import copy,hashlib,io,json,os,subprocess,sys,tarfile,tempfile,unittest
B=Path(__file__).resolve().parent;R=B.parents[2];sys.path.insert(0,str(B));import native_tar_view_h7 as c
RAW=R/'evidence/betarc01/m501/sessions/beta-rc01-sdk-reconcile01/native-restart-metadata.tar';RAW_SHA='1963cd4a2cf2658bd9f55384c1a6bca54f6bbe77e62955e19d02a82d08a911e1'
C=R/'evidence/nativejournal17/candidates/c297542deab30c49ad528db1df8dc34cc9e4954ac0065d616afcfbc1e50df6b4';os.environ.update(AERIS_REPOSITORY_ROOT=str(R),AERIS_CANDIDATE_DIR=str(C),AERIS_CANDIDATE_SHA256=C.name);sys.path[:0]=[str(C/'source'),str(R)]
from planning.nativejournal17.receiver17 import validate_tar_shape,native_tar
from aeris_runtime.reconcile_h6 import reconcile

def independent_table(p):
 result={}
 with tarfile.open(p,'r:')as t:
  for m in t:
   name=m.name.rstrip('/');result[name]={'type':'directory'if m.isdir()else'regular','mode':m.mode,'uid':m.uid,'gid':m.gid,'mtime':m.mtime,'bytes':m.size,'sha256':c.sha(t.extractfile(m).read())if m.isfile()else c.sha(b'')}
 return result

def fixed_header(raw,offset,changes):
 out=bytearray(raw);h=bytearray(raw[offset:offset+512])
 for start,data in changes:h[start:start+len(data)]=data
 h[148:156]=b' '*8;h[148:156]=('%06o'%sum(h)).encode()+b'\0 ';out[offset:offset+512]=h;return bytes(out)
class Codec(unittest.TestCase):
 def test_actual_raw_strict_refusal_and_derived_independent_views(self):
  before=(c.hash_file(RAW),RAW.stat().st_size,RAW.stat().st_ino,RAW.stat().st_mode)
  self.assertEqual(before[0],RAW_SHA)
  with self.assertRaisesRegex(ValueError,'TAR_NO_LINK_OR_EXTENSION'):validate_tar_shape(RAW)
  with tempfile.TemporaryDirectory(prefix='codec-',dir=B)as tmp:
   view=Path(tmp)/'derived.tar';proof=c.convert(RAW,view);self.assertEqual(proof['longnameCarrierCount'],10);self.assertEqual(proof['entryCount'],84);self.assertLessEqual(proof['view']['bytes'],proof['raw']['bytes']);validate_tar_shape(view);self.assertEqual(independent_table(RAW),independent_table(view));self.assertEqual(len(native_tar(view,c.hash_file(view),allow_empty_active=True)['files']),75)
   script="import fs from'node:fs';import{scanNativeTar}from'./planning/nativejournal17/native-tar17.mjs';console.log(JSON.stringify(await scanNativeTar(fs.createReadStream(process.argv[1]))));";r=subprocess.run(['/usr/local/bin/node','--input-type=module','-e',script,str(view)],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10);self.assertEqual(r.returncode,0,r.stderr);self.assertFalse(r.stderr);self.assertEqual(json.loads(r.stdout)['archivedJournals'],8)
   m=json.loads((C/'candidate.json').read_bytes());p=reconcile(view,c.hash_file(view),source_candidate=C.name,native_apk_sha=m['native']['APK_SHA256'],native_source_sha=m['native']['sourceSHA256']);self.assertEqual(p['pendingTransactions'],0);self.assertEqual(p['registryProof']['activeJournals'],0);self.assertEqual(p['registryProof']['archivedJournals'],8);self.assertFalse(proof['m501Acceptance'])
   with self.assertRaisesRegex(ValueError,'TAR_NO_LINK_OR_EXTENSION'):validate_tar_shape(RAW)
  self.assertEqual(before,(c.hash_file(RAW),RAW.stat().st_size,RAW.stat().st_ino,RAW.stat().st_mode))
 def test_exact_longname_and_file_safety_adversaries(self):
  raw=RAW.read_bytes();scan=c.scan(RAW);e=next(x for x in scan['entries']if x['longname']is not None);L=e['longname'];at=L['headerOffset'];regular=e['headerOffset'];end=at+512+((L['payloadBytes']+511)//512)*512;cases={}
  for label,kind in [('K',b'K'),('pax',b'x'),('globalPax',b'g'),('sparse',b'S'),('device',b'3'),('symlink',b'2'),('hardlink',b'1')]:cases[label]=fixed_header(raw,at,[(156,kind)])
  cases['chain']=raw[:at]+raw[at:end]+raw[at:];cases['orphan']=raw[:end]+bytes(1024);cases['prefix']=fixed_header(raw,regular,[(0,b'X')]);cases['checksum']=bytes([raw[0]^1])+raw[1:];bad=bytearray(raw);bad[end-1]=1;cases['padding']=bytes(bad);cases['truncated']=raw[:at+520];cases['tail']=raw+b'X';cases['missingEOA']=raw[:-1024];cases['nonzeroLink']=fixed_header(raw,regular,[(157,b'files/secret\0')]);cases['Ldirectory']=fixed_header(raw,regular,[(156,b'5')]);bad=bytearray(raw);bad[at+512+L['payloadBytes']-1]=88;cases['noNUL']=bytes(bad)
  # Same-length safe-looking malicious override, including matching truncated header.
  for label,prefix in[('traversal',b'files/../'),('absolute',b'/etc/../'),('emptycomponent',b'files//')]:
   name=prefix+b'a'*(L['payloadBytes']-1-len(prefix));bad=bytearray(raw);bad[at+512:at+512+len(name)]=name;cases[label]=fixed_header(bad,regular,[(0,name[:100])])
  duplicate=next(x for x in scan['entries']if x['type']=='regular'and x['longname']is None);start=duplicate['headerOffset'];stop=duplicate['bodyOffset']+((duplicate['bytes']+511)//512)*512;cases['duplicate']=raw[:-1024]+raw[start:stop]+bytes(1024)
  with tempfile.TemporaryDirectory(prefix='codec-',dir=B)as tmp:
   for label,data in cases.items():
    p=Path(tmp)/(label+'.tar');p.write_bytes(data)
    with self.subTest(label=label),self.assertRaises(c.CodecError):c.convert(p,Path(tmp)/(label+'.view'))
 def test_no_overwrite_or_unsupported_limits(self):
  with tempfile.TemporaryDirectory(prefix='codec-',dir=B)as tmp:
   p=Path(tmp)/'exists';p.write_bytes(b'kept')
   with self.assertRaises(c.CodecError):c.convert(RAW,p)
   self.assertEqual(p.read_bytes(),b'kept')
  for name in['files/'+('x'*101),'files/a/../b','files//b']:
   with self.assertRaises(c.CodecError):
    if '..'in name or'//'in name:c.pathname(name.encode(),False)
    else:c.split_ustar(name)
 def test_logical_headers_preserve_all_metadata(self):
  for e in c.scan(RAW)['entries']:
   h=c.header(e);self.assertIn(h[156],(0,48,53));self.assertEqual(c.octal(h[100:108]),e['mode']);self.assertEqual(c.octal(h[108:116]),e['uid']);self.assertEqual(c.octal(h[116:124]),e['gid']);self.assertEqual(c.octal(h[136:148]),e['mtime']);self.assertEqual(c.octal(h[124:136]),e['bytes']);self.assertEqual(c.octal(h[148:156]),sum(h[:148])+8*32+sum(h[156:]))
if __name__=='__main__':unittest.main(verbosity=2)
