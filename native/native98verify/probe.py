from ui98 import *
from collections import Counter
owned();run=sys.argv[1];rows=rows98(run);print('KINDS',dict(Counter(r['kind']for r in rows)))
for r in rows:
 if r['kind']in ['JS_TRANSPORT_FAILURE98','CLOSED','PREFLIGHT','PAYLOAD_ATTACH','PAYLOAD_JOIN_INTENT','NATIVE_ERROR']:
  print(r['n'],r['elapsedMs'],r['kind'],json.loads(base64.b64decode(r['dataBase64'])))
print('PAYLOAD',json.dumps(state98(run),ensure_ascii=False))
