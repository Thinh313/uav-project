from pathlib import Path
import json,base64,struct,hashlib
R=Path(__file__).resolve().parents[2];E=R/'evidence/native98';source=R/'evidence/native96/runs/s096f2c41e36548be9071/android-raw.jsonl';rows=[json.loads(l)for l in source.read_bytes().splitlines()];meta=json.loads(base64.b64decode(rows[0]['dataBase64']));out=[]
for i in meta['document']['compiled']['plan']['compiled']['items']:
 b=struct.pack('<ffffiifHHBBBBBB',*[i[k]for k in ['param1','param2','param3','param4','x','y','z','seq','command']],42,1,i['frame'],i['current'],i['autocontinue'],i['mission_type']);out.append('ITEM\t'+b.hex())
start=rows[0]['elapsedMs'];counts={}
for r in rows:
 k={'RX':'RX','TX_INTENT':'TX','EXPLICIT_GRANT':'GRANT'}.get(r['kind'])
 if k:out.append(k+'\t'+str(r['elapsedMs']-start+1000)+('\t'+base64.b64decode(r['dataBase64']).hex()if k!='GRANT'else''));counts[k]=counts.get(k,0)+1
(E/'flight-replay98.tsv').open('x').write('\n'.join(out)+'\n');(E/'flight-replay-source.json').open('x').write(json.dumps({'source':str(source.relative_to(R)),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'counts':counts,'scope':'Previously captured AP data replayed with shared native gates; not a new SITL run'},indent=2))
