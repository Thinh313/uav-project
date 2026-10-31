"""Root-owned actual Android public-trust validity probes; no clock/key changes."""
from ui01 import *
import ssl
owned();original=(E/'admin-trust02.json').read_bytes();app='/data/user/0/'+P+'/files/crew02/'
def audit():
 raw=adb('exec-out','cat',app+'audit.jsonl');return raw,[json.loads(l)for l in raw.splitlines()]
def provision(path):
 adb('push',path,'/data/local/tmp/crew02-validity.json');adb('shell','cp','/data/local/tmp/crew02-validity.json',app+'admin-trust.json');uid=adb('shell','stat','-c','%u',app).decode().strip();assert uid.isdigit();adb('shell','chown',uid+':'+uid,app+'admin-trust.json');adb('shell','chmod','600',app+'admin-trust.json')
tap01('crew-stop');results=[]
try:
 for name in ['expired02','future01']:
  before,rows=audit();trust=[r for r in rows if r['kind']=='TRUST'];q=json.loads(original);der=ssl.PEM_cert_to_DER_cert((R/'.local/crew02/identity'/(name+'.cert.pem')).read_text());q.update(trustEpoch=3,peerCertDerBase64=base64.b64encode(der).decode(),peerCertSha256=hashlib.sha256(der).hexdigest(),peerSpkiSha256='c0a76f3ad3b77ac3e19ea9f16fdfc1a9f6817f5d28a87a4ce30b9727dbf13367');path=E/(name+'-admin-candidate03.json');path.open('x').write(json.dumps(q,separators=(',',':'))+'\n');provision(path);tap01('crew-listen');time.sleep(.3);control01('op-refresh',enabled=False);swipe94('up');after,rows2=audit();assert [r for r in rows2 if r['kind']=='TRUST']==trust,'INVALID_CERT_ADVANCED_TRUST';assert after.startswith(before),'AUDIT_REWRITE';capture('crew-'+name+'-refused03');(E/(name+'-audit03.jsonl')).open('xb').write(after);results.append({'candidate':name,'noTrustFrontierAdvance':True,'auditBeforeSHA256':hashlib.sha256(before).hexdigest(),'auditAfterSHA256':hashlib.sha256(after).hexdigest()})
finally:
 provision(E/'admin-trust02.json');assert adb('exec-out','cat',app+'admin-trust.json')==original
tap01('crew-listen');capture('crew-valid-trust-restored03');(E/'validity03.json').open('x').write(json.dumps({'scope':'Actual Android CrewTrust.load refusal of otherwise-pinned date-invalid client certificates, before TLS admission; not actual expired TLS handshake','results':results,'restoredExactOriginalPublicManifest':True},indent=2));print('VALIDITY_TRUST_FRONTIER_PRESERVED')
