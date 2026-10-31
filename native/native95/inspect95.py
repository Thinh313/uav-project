from ui94 import *
owned()
run=sys.argv[1];label=sys.argv[2]
raw=adb('exec-out','cat','/data/user/0/'+P+'/files/direct95/'+run+'/raw.jsonl')
(E/(label+'-raw.jsonl')).open('xb').write(raw)
rows=[json.loads(x) for x in raw.splitlines()]
decoded=[]
for row in rows:
 if row['kind'] not in ['RX','TX_INTENT','TX_WRITTEN']:
  data=__import__('base64').b64decode(row['dataBase64']).decode(errors='replace')
  try:data=json.loads(data)
  except ValueError:pass
  decoded.append({'n':row['n'],'at':row['elapsedMs'],'kind':row['kind'],'data':data})
(E/(label+'-derived.json')).open('x').write(json.dumps(decoded,indent=2))
print(json.dumps({'records':len(rows),'kinds':dict(__import__('collections').Counter(r['kind'] for r in rows)),'last':decoded[-6:]},ensure_ascii=False)[-7000:])
capture(label)
