"""Exact installed TRANSPORT14 predecessor, separate from historical upgrade v2."""
import json
from .candidate import load,sha,CERT
from .paths import repository
DIGEST='e5528b90876cdf7496aa4ab0aa3ef703433e57f6153e8abe305495cc10287f8b'
APK='eb83d04026cc4b5da6962d7efb6578542b573758c4269969fc87dc53087fd9f1'
SOURCE='1620679e03ed043852deece0ca2bb96fb861c78274980999a2faa8fa97132347'
def proof():
 p=repository()/'evidence/runtime-transport14/candidates'/DIGEST
 if any(v.is_symlink()for v in[p,*p.parents]):raise ValueError('STATUS15_PREDECESSOR_IMMUTABLE_PATH')
 m=load(p,DIGEST);b=json.loads((p/'native-build-receipt.json').read_bytes())
 if m['native']['sourceSHA256']!=SOURCE or m['native']['APK_SHA256']!=APK or b.get('certificateSHA256')!=CERT or b.get('productionSigning')is not False or b.get('sourceCount')!=51:raise ValueError('STATUS15_PREDECESSOR_EXACT_E552_EB83_SOURCE_CERT')
 return {'format':'aeris-immutable-upgrade-predecessor','version':1,'candidateDir':str(p),'candidateSHA256':DIGEST,'nativeSourceSHA256':SOURCE,'APKSHA256':APK,'certificateSHA256':CERT,'nativeBuildReceiptSHA256':sha(p/'native-build-receipt.json')}
