"""Fresh cold legacy integrity. Root executes before/after actual actors.
Default hashes old467 IPC10 files +270HOSTDIAG11 originals +125held inputs.
--full-legacy additionally invokes immutable legacy verifier prefix once, with
no original output write and fresh Python namespace. New QA output only.
"""
from pathlib import Path
import argparse,sys,os,json,hashlib,zlib,base64,stat,time,re
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[3];E=R/'evidence/vidlife12/qa';H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();start=time.monotonic_ns()
a=argparse.ArgumentParser();a.add_argument('output');a.add_argument('--full-legacy',action='store_true');q=a.parse_args();assert re.fullmatch(r'FROZEN-[A-Z0-9-]+\.json',q.output);out=E/q.output;assert not out.exists()
ipcfile=R/'evidence/hostdiag11/qa/PRESERVATION-ENTRY01.json';ipc=json.loads(ipcfile.read_bytes());expected=ipc['ipc10EntryRows'];assert len(expected)==467
actual=[]
for root in[R/'planning/hosthealth-ipc10',R/'evidence/hosthealth-ipc10']:
 for p in sorted(root.rglob('*')):
  if p.is_symlink():actual.append({'path':str(p.relative_to(R)),'kind':'symlink','target':os.readlink(p)})
  elif p.is_file():
   s=p.stat();actual.append({'path':str(p.relative_to(R)),'bytes':s.st_size,'mode':stat.S_IMODE(s.st_mode),'mtimeNs':s.st_mtime_ns,'device':s.st_dev,'inode':s.st_ino,'sha256':H(p)})
assert actual==expected,'OLD_IPC10_467_BYTES_MODE_MTIME_INODE_OR_MEMBERSHIP_CHANGED'
s01file=R/'evidence/hostdiag11/qa/S01-ACTUAL-COLD-REVIEW01.json';f=json.loads(s01file.read_bytes())['originalFileBaseline'];assert f['encoding']=='ZLIB_BASE64_LOSSLESS_COMPACT_PATH_SIZE_MODE_SHA256_ROWS'and f['rows']==270
plain=zlib.decompress(base64.b64decode(f['data'],validate=True));assert len(plain)==f['originalJSONBytes']and hashlib.sha256(plain).hexdigest()==f['originalJSONSHA256'];s01=json.loads(plain);assert len(s01)==270
root=R/'evidence/hostdiag11/s01';nowfiles={str(p.relative_to(root))for p in root.rglob('*')if p.is_file()};assert nowfiles=={r[0]for r in s01},'OLD_S01_270_MEMBERSHIP_CHANGED'
for name,size,mode,sha in s01:
 p=root/name;s=p.lstat();assert stat.S_ISREG(s.st_mode)and s.st_size==size and stat.S_IMODE(s.st_mode)==mode and H(p)==sha,('OLD_S01_BYTES_MODE_CHANGED',name)
holdfile=R/'evidence/hostdiag11/BUILDER-HOLD02.json';held=json.loads(holdfile.read_bytes())['inputPins'];assert len(held)==125
for path,sha in held.items():assert H(R/path)==sha,('OLD_HELD_SOURCE_CHANGED',path)
legacy=None
if q.full_legacy:
 script=R/'planning/betasim-integrated01/qa/frozen_release08.py';assert H(script)=='8c045453f910d9bd251881210aa7f3a01fb4786742eced056b4c1d36b295f63b';text=script.read_text();marker="\nout=E/'qa/FROZEN-CANDIDATE-REVIEW08.json'";assert text.count(marker)==1;ns={'__file__':str(script)};exec(compile(text.split(marker)[0],str(script),'exec'),ns);proof=ns['report'];assert proof['status'].startswith('PASS_READONLY_');v=proof['legacyPreservation'];legacy={'status':proof['status'],'verifierSHA256':H(script),'legacyEntries':v['legacyEntries'],'sealedInventories':len(v['seals']),'ENDUREIdentities':v['endureIdentities'],'preexistingMissingSeparate':v['preexistingMissingSeparate'],'oldCandidateFullLoads':len(proof['oldCandidateFullLoads']),'sourceModuleOrigin':str(Path(sys.modules['aeris_runtime.candidate'].__file__).relative_to(R))}
 b=json.loads((R/'evidence/hosthealth-ipc10/qa/BASELINE-PRESERVATION01.json').read_bytes());er=R/'evidence/betasim-integrated01';assert H(er/'r07/metadata-budget/metadata-ledger.json')==b['r07LedgerSHA256'];r08=b.get('r08AllOriginalFiles',b.get('r08OriginalFilesBaseline'))
 if r08 is None:r08=json.loads((er/'qa/ACTUAL-R08-CAUSE01.json').read_bytes())['originalRowsBaseline']
 assert len(r08)==93
 for row in r08:
  p=er/'r08'/row['path'];s=p.stat();assert s.st_size==row['bytes']and stat.S_IMODE(s.st_mode)==row['mode']and H(p)==row['sha256']
 legacy['R07LedgerUnchanged']=True;legacy['R08All93OriginalsUnchanged']=True
report={'format':'aeris-vidlife12-fresh-frozen-integrity','status':'PASS_FRESH_OLD_467_270_125_NOT_RUNTIME_ACCEPTANCE','IPC10Entries467Exact':True,'HOSTDIAG11Original270BytesModesMembershipExact':True,'HOSTDIAG11Held125HashesExact':True,'fullLegacy':legacy,'baselineRefs':[{'path':str(p.relative_to(R)),'sha256':H(p)}for p in[ipcfile,s01file,holdfile]],'S01ExpandedBaselineSHA256':f['originalJSONSHA256'],'actualActorsStarted':False,'oldSourcesOrEvidenceMutated':False,'continuousOriginalPathPresenceClaim':False,'elapsedNs':time.monotonic_ns()-start};out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'out':str(out.relative_to(R)),'fullLegacy':legacy,'elapsedSeconds':report['elapsedNs']/1e9}))
