"""Read-only complete app-files SHA manifest, no full private-directory duplicate."""
from android_qa import *
import sys
owned();label=sys.argv[1];assert re.fullmatch('(before|after)03',label)
base='/data/user/0/'+P+'/files/'
raw=adb('shell','find',base,'-type','f','-exec','sha256sum','{}','+',timeout=90).decode();files={}
for line in raw.splitlines():
 sha,name=line.split(None,1);name=name.strip();assert re.fullmatch('[a-f0-9]{64}',sha)and name.startswith(base);rel=name[len(base):];assert rel not in files;files[rel]=sha
assert files and len(files)<10000
q={'atHostMonoNs':str(time.monotonic_ns()),'scope':'Every regular file under CREW02 private files, app force-stopped before both observations, coldboot before activity start','files':files,'count':len(files),'keysExported':False,'automaticAuthorityRestored':False}
if label.startswith('after'):
 b=json.loads((E/'coldboot-private-before03.json').read_text());q['failures']=[k for k in sorted(set(b['files'])|set(files))if b['files'].get(k)!=files.get(k)];q['pass']=not q['failures']
(E/('coldboot-private-'+label+'.json')).open('x').write(json.dumps(q,indent=2));print(json.dumps({k:v for k,v in q.items()if k!='files'}));assert q.get('pass',True)
