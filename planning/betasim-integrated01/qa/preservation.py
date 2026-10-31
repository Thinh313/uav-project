"""Read-only legacy original checks and task-entry current-byte baseline. No restore."""
from pathlib import Path
import datetime,hashlib,json,os,stat,time
REPO=Path(__file__).resolve().parents[3]
OUT=REPO/'evidence/betasim-integrated01/qa'
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def rows(root):
 result=[]
 for p in sorted(Path(root).rglob('*')):
  s=p.lstat()
  if stat.S_ISLNK(s.st_mode):result.append([str(p.relative_to(root)),'symlink',os.readlink(p),oct(stat.S_IMODE(s.st_mode))])
  elif stat.S_ISREG(s.st_mode):result.append([str(p.relative_to(root)),s.st_size,oct(stat.S_IMODE(s.st_mode)),digest(p)])
 return result
def main():
 os.chdir(REPO);start=time.monotonic_ns();prefix=(REPO/'evidence/runtime-pipeline06/root-preservation01.py').read_text().split("\nwith(outroot/")[0];ns={}
 try:exec(compile(prefix,'readonly-old-preservation-prefix','exec'),ns);original=ns['result']
 except Exception as e:original={'status':'FAIL_ORIGINAL_CHECK','error':type(e).__name__+':'+str(e)}
 oldroot=REPO/'evidence/runtime-transport15';seal=json.loads((oldroot/'reports/handoff-final01.json').read_bytes());expected=seal['rows'];bad=[]
 for row in expected:
  p=oldroot/row[0]
  if not p.is_file():bad.append({'expected':row,'actual':'MISSING'});continue
  s=p.stat();actual=[row[0],s.st_size,oct(stat.S_IMODE(s.st_mode)),digest(p)]
  if actual!=row:bad.append({'expected':row,'actual':actual})
 atomic=REPO/'evidence/runtime-transport15-atomic-prep';current=rows(atomic)
 result={'format':'aeris-betasim-integrated01-entry-preservation','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsedNs':time.monotonic_ns()-start,'originalLegacyChecks':original,'oldR15Seal':{'path':str(oldroot/'reports/handoff-final01.json'),'sha256':digest(oldroot/'reports/handoff-final01.json'),'entries':len(expected),'drift':bad},'atomicCurrentEntryBaseline':{'scope':str(atomic),'rows':current,'rowsSHA256':hashlib.sha256((json.dumps(current,separators=(',',':'),sort_keys=True)+'\n').encode()).hexdigest(),'historicalAcceptance':False,'previousReferenceForAllAtomicPathsAvailable':False},'restorationPerformed':False,'oldLedgerReset':False,'continuousPathPresenceClaim':False,'missionOrENDUREAcceptance':False}
 OUT.mkdir(exist_ok=True);target=OUT/'preservation-entry01.json'
 with target.open('x')as f:json.dump(result,f,ensure_ascii=False,separators=(',',':'));f.write('\n')
 print(json.dumps({'oldStatus':original['status'],'oldR15Drift':len(bad),'atomicEntries':len(current),'output':str(target),'elapsedSeconds':(time.monotonic_ns()-start)/1e9}))
if __name__=='__main__':main()
