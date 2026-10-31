"""Bounded in-memory adversaries; original raw bytes never rewritten."""
import copy
import hashlib
import json
import pathlib
import struct
import verify

R=pathlib.Path(__file__).resolve().parents[2];E=R/'evidence/simsitl76'
original=(E/'run03/wire.jsonl').read_bytes();base=[json.loads(line) for line in original.splitlines()]


class MemoryTrace:
    def __init__(self,b):self.b=b
    def read_bytes(self):return self.b


def reseal(rows):
    previous='0'*64;output=[]
    for i,r in enumerate(rows):
        r.pop('sha256',None);r['n']=i+1;r['prev']=previous
        b=json.dumps(r,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
        previous=hashlib.sha256(b).hexdigest();r['sha256']=previous
        output.append(json.dumps(r,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode())
    return b'\n'.join(output)+b'\n'


def frame_mutation(rows,id,mutator):
    for row in rows:
        if row['kind']!='TX_INTENT':continue
        b=bytearray.fromhex(row['rawHex'])
        if b[0]!=253 or int.from_bytes(b[7:10],'little')!=id:continue
        if mutator(b):
            old=row['rawHex'];extra=verify.DEFS[str(id)]['crc'];b[-2:]=verify.crc(bytes(b[1:-2]),extra).to_bytes(2,'little');row['rawHex']=b.hex()
            for returned in rows:
                if returned['kind']=='TX_WRITE_RETURN' and returned['rawHex']==old:returned['rawHex']=b.hex();break
            return
    raise AssertionError('Fixture message not found')


results=[]


def reject(name,fn):
    try:fn()
    except (AssertionError,KeyError,ValueError) as e:
        results.append({'id':name,'rejected':True,'exception':type(e).__name__,'detail':str(e)})
    else:raise AssertionError('Did not bite: '+name)


rows=copy.deepcopy(base);rows.pop(20)
reject('unsealed-missing-row',lambda:verify.analyze(MemoryTrace(b'\n'.join(json.dumps(r,separators=(',',':')).encode() for r in rows))))
rows=copy.deepcopy(base)
for row in rows:
    if row['kind']=='RX':
        b=bytearray.fromhex(row['rawHex']);i=b.find(253)
        if i>=0 and len(b)>i+15:b[i+10]^=1;row['rawHex']=b.hex();break
reject('resealed-rx-crc-fault',lambda:verify.analyze(MemoryTrace(reseal(rows))))
rows=copy.deepcopy(base)
def wrongtarget(b):b[40]=99;return True
frame_mutation(rows,76,wrongtarget)
reject('resealed-wrong-target-valid-crc',lambda:verify.analyze(MemoryTrace(reseal(rows))))
rows=copy.deepcopy(base)
def avoidset(b):struct.pack_into('<f',b,10,7.);return True
frame_mutation(rows,23,avoidset)
wrong_param=verify.analyze(MemoryTrace(reseal(rows))) # raw integrity MUST pass, then semantic gate must bite
reject('resealed-wrong-avoid-param',lambda:verify.verify_behavior(wrong_param))
rows=[copy.deepcopy(r) for r in base if not(r['kind']=='MARK' and r['name']=='LANDED_DISARMED')]
reject('resealed-no-landing-marker',lambda:verify.verify_behavior(verify.analyze(MemoryTrace(reseal(rows)))))
rows=copy.deepcopy(base)
for row in rows:
    if row['kind']=='RX' and b'Init Gyro' in bytes.fromhex(row['rawHex']):
        row['rawHex']=(b'InjectedText'+bytes.fromhex(row['rawHex'])).hex();break
reject('resealed-unexpected-boot-ascii',lambda:verify.analyze(MemoryTrace(reseal(rows))))
data=verify.analyze(MemoryTrace(original));altered=copy.deepcopy(data)
start=data['marks']['PITCH_YAW_1_1_START']['at'];end=data['marks']['PITCH_YAW_1_1_END']['at']
for f in altered['frames']:
    if f['id']==30 and start<=f['at']<=end:f['fields']['pitch']=0.;f['fields']['yawspeed']=0.
reject('semantic-no-response-despite-acks',lambda:verify.verify_behavior(altered))
altered=copy.deepcopy(data);start=data['marks']['AVOID_ENABLED_START']['at'];end=data['marks']['AVOID_ENABLED_END']['at']
for f in altered['frames']:
    if f['id']==32 and start<=f['at']<=end:f['fields']['x']=13.
reject('semantic-penetration-despite-acks',lambda:verify.verify_behavior(altered))
receipt={'status':'PASS_NEGATIVE_BITES','passed':len(results),'total':len(results),'rows':results,
         'rawSha256':hashlib.sha256(original).hexdigest(),'originalUnchanged':hashlib.sha256((E/'run03/wire.jsonl').read_bytes()).hexdigest()==hashlib.sha256(original).hexdigest(),
         'scope':'Six raw/chain/CRC/evidence mutations; two post-decode semantic fixtures. No copied raw files or flight commands.'}
with (E/'bites-run03-v2.json').open('x') as f:json.dump(receipt,f,indent=2)
print(json.dumps({'passed':len(results),'total':len(results),'status':receipt['status']}))
