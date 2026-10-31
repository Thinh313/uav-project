"""Read-only SHA validation; writes one exclusive new task receipt."""
from pathlib import Path
import json,hashlib,datetime,sys,shutil
R=Path(__file__).resolve().parents[2];E=R/'evidence/field02/cockpitvideo04'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()if p.is_file()else None
def verify(name):
 assert name.replace('-','').isalnum()
 b=json.loads((E/'preservation-before.json').read_text());groups={'protected1486':json.loads((R/b['protectedBaseline']).read_text())['files'],'native7':json.loads((R/b['nativeBaseline']).read_text())['files'],'oldEvidence':b['oldEvidenceFiles'],'frozenCurrentSources':b['frozenCurrentSources']};out={}
 for k,files in groups.items():out[k]={'files':len(files),'differences':[{'path':n,'expected':h,'actual':sha(R/n)}for n,h in files.items()if sha(R/n)!=h]}
 current=[str(p.relative_to(R))for p in sorted((R/'evidence/field02/flight/runs').glob('s*'))];added=[n for n in current if n not in b['existingSITLRunDirectories']]
 result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'integrity':out,'newSITLDirectories':added,'oldSITLDirectoriesRetained':all((R/n).is_dir()for n in b['existingSITLRunDirectories']),'freeBytes':shutil.disk_usage(R).free,'scopeNotWholeRepository':True,'preexistingGitDeletedCount':len(b['gitDeletedBefore']),'historicalBaselineSemantics':'DEREFERENCED_SHA_INCLUDES_SEVEN_NEGATIVE_TEST_SYMLINK_FIXTURES_NOT_LINK_TARGET_STRING_AUTHENTICATION'}
 result['pass']=not any(v['differences']for v in out.values())and result['oldSITLDirectoriesRetained']and len(added)<=2
 with(E/(name+'.json')).open('x')as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({'pass':result['pass'],'counts':{k:v['files']for k,v in out.items()},'differences':sum(len(v['differences'])for v in out.values()),'newSITL':added,'freeGiB':result['freeBytes']/2**30}))
 assert result['pass']
if __name__=='__main__':assert len(sys.argv)==2;verify(sys.argv[1])
