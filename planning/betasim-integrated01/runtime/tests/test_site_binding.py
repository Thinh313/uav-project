"""V4 dedup still binds every source module and exact write-call snippet."""
from pathlib import Path
import hashlib,json,shutil,sys
P=Path(__file__).resolve();R=P.parents[1];REPO=R.parents[2];sys.path[:0]=[str(R/'source'),str(REPO)]
from aeris_runtime.pipeline_contract import sites,source_pins
LAB=REPO/'evidence/betasim-integrated01/runtime/.sitebinding'
def main():
 assert not LAB.exists();LAB.mkdir(parents=True);checks=[]
 try:
  p=LAB/'small.py';original="from pathlib import Path\ndef work():\n Path('owned').write_bytes(b'abc')\n";p.write_text(original);sources=source_pins(LAB);full=sites(LAB);compact=sites(LAB,False);assert compact==[{k:v for k,v in x.items()if k!='sourceSHA256'}for x in full]and all(sources[x['module']]==x['sourceSHA256']for x in full);checks.append('v4-file-hash-derived-from-exact-global-module-map-with-identical-full-site-set')
  def matches():return source_pins(LAB)==sources and sites(LAB,False)==compact
  assert matches();p.write_text(original.replace("b'abc'","b'abd'"));assert not matches()and sites(LAB,False)!=compact;checks.append('changed-actual-write-snippet-refused')
  p.write_text(original+'# module-only drift\n');assert sites(LAB,False)==compact and source_pins(LAB)!=sources and not matches();checks.append('non-site-module-byte-drift-refused-by-source-map')
  p.write_text(original);tamper=json.loads(json.dumps(compact));tamper[0]['siteSHA256']='0'*64;assert sites(LAB,False)!=tamper and matches();checks.append('forged-snippet-metadata-refused-with-unchanged-source')
  assert all('sourceSHA256'in x for x in sites(LAB));checks.append('legacy-v3-default-site-format-unchanged')
  report={'status':'PASS_SOURCE_FILE_SITE_BINDING_MOCK','groups':checks,'artifactCapOrNumericGuardChanged':False,'actualRuntime':False}
 finally:shutil.rmtree(LAB)
 (REPO/'evidence/betasim-integrated01/runtime/site-binding-mock.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(checks))
if __name__=='__main__':main()
