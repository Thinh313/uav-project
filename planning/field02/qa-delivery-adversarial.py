#!/usr/bin/env python3
"""Independent Contractor-generated adversarial inputs for the delivery CLI.

No exporter is called. Seed is a readonly retained delivery; every changed byte
is written only beneath a new FIELD02 qa directory. Positive seed acceptance
does not prove Android SAF, FIELD02 flight or hardware. Reuses the receiver
under test as an oracle but generates/re-hashes malformed inputs separately.
"""
import sys
sys.dont_write_bytecode = True
import argparse, copy, hashlib, io, json, os, subprocess, tarfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def canonical(o): return json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def need(v, message):
    if not v: raise AssertionError(message)
def unpack(b):
    with tarfile.open(fileobj=io.BytesIO(b), mode='r:') as t:
        return {m.name: t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
def tar(entries):
    # Strict ustar generated independently, no exporter or receiver helper.
    out = bytearray()
    for name, data in entries:
        h = bytearray(512)
        def put(a, raw): h[a:a+len(raw)] = raw
        put(0, name.encode('ascii'));put(100,b'0000600\0');put(108,b'0000000\0');put(116,b'0000000\0')
        put(124, ('%011o\0' % len(data)).encode());put(136,b'00000000000\0');put(148,b'        ')
        h[156] = ord('0');put(257,b'ustar\0');put(263,b'00');put(148,('%06o\0 ' % sum(h)).encode())
        out.extend(h);out.extend(data);out.extend(bytes((-len(data)) % 512))
    out.extend(bytes(1024));return bytes(out)
def recapture(b, mutate):
    files = unpack(b); side=json.loads(files['sidecar.json']); m=json.loads(files['manifest.json'])
    mutate(side,m)
    files['sidecar.json']=canonical(side)
    m['files'][1]={'path':'sidecar.json','sizeBytes':len(files['sidecar.json']),'sha256':sha(files['sidecar.json'])}
    m.pop('packageId');m['packageId']=sha(canonical(m));files['manifest.json']=canonical(m)
    return tar([(n,files[n]) for n in ('original.jpg','sidecar.json','manifest.json')])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed',default='evidence/field01/http-receiver-set01')
    p.add_argument('--index-sha256',default='0bc99d4bc10c84603ad13c16c7b583b6e72f44e9694ab83bd8b6ea526276336c')
    p.add_argument('--cli',default='pilot/field01/evidence/receive-set.py')
    p.add_argument('--out',required=True)
    a=p.parse_args(); seed=(ROOT/a.seed).resolve(); cli=(ROOT/a.cli).resolve();out=(ROOT/a.out).resolve()
    need(str(out).startswith(str(ROOT/'evidence/field02/qa')),'NEW_QA_OUTPUT_ONLY')
    need(cli in [(ROOT/'pilot/field01/evidence/receive-set.py'),(ROOT/'pilot/field02/evidence/receive-set.py')],'DECLARED_CLI_ONLY')
    need(not out.exists(),'EXCLUSIVE_OUTPUT_REQUIRED');need(os.statvfs(ROOT).f_bavail*os.statvfs(ROOT).f_frsize>20*2**30+32*2**20,'DISK_FLOOR')
    raw=(seed/'index.json').read_bytes();need(sha(raw)==a.index_sha256,'SEED_INDEX_SHA')
    idx=json.loads(raw); names=['index.json',idx['flight']['path']]+[d['path'] for d in idx['captures']]
    base={n:(seed/n).read_bytes() for n in names};need(sum(map(len,base.values()))<64*2**20,'SEED_BOUND')
    before={str(seed/n):sha(b) for n,b in base.items()};out.mkdir(parents=True); own=out/'seed';own.mkdir()
    for n,b in base.items():(own/n).write_bytes(b)
    results=[]
    def test(name, f):
        at=time.monotonic()
        try: detail=f();results.append({'name':name,'status':'PASS','elapsedMs':(time.monotonic()-at)*1000,**(detail or {})})
        except Exception as e: results.append({'name':name,'status':'FAIL','elapsedMs':(time.monotonic()-at)*1000,'error':str(e)})
    def receive(folder,digest,state=None,receiver=None,sender=None):
        cmd=['python3','-B',str(cli),str(folder),'--index-sha256',digest,'--receiver',receiver or idx['receiverId'],'--sender',sender or idx['senderId']]
        cmd+=['--state',str(state)] if state else ['--check-only']
        r=subprocess.run(cmd,capture_output=True,timeout=60)
        need(len(r.stdout)<131072 and len(r.stderr)<131072,'CLI_OUTPUT_BOUND')
        try: body=json.loads(r.stdout)
        except Exception: raise AssertionError('MALFORMED_CLI_RECEIPT:'+r.stderr.decode(errors='replace')[:500])
        return r.returncode,body
    def variant(name, change):
        folder=out/name;folder.mkdir(); i=copy.deepcopy(idx);files={};change(i,files)
        for n,b in base.items():
            if n=='index.json':continue
            if n in files:(folder/n).write_bytes(files[n])
            else:os.link(own/n,folder/n) # only links to our own immutable seed copy
        for n,b in files.items():
            if n not in base:(folder/n).write_bytes(b)
            d=i['flight'] if n==i['flight']['path'] else next((d for d in i['captures'] if d['path']==n),None)
            if d:d.update(sizeBytes=len(b),sha256=sha(b))
        b=canonical(i);(folder/'index.json').write_bytes(b);return folder,sha(b)
    def refusal(name,change,expected=None,receiver=None):
        folder,h=variant(name,change);state=out/(name+'-state');code,body=receive(folder,h,state,receiver=receiver)
        need(code!=0 and body.get('status')=='QUARANTINE','MUST_REFUSE')
        need(body.get('restoredAuthority')=='NONE' and body.get('authorityRestorable') is False,'NO_AUTHORITY')
        need(not state.exists(),'REFUSAL_MUST_NOT_CREATE_LEDGER_STATE')
        if expected:need(expected in body.get('reason',''),'REFUSAL_REASON:'+str(body))
        (out/(name+'-receipt.json')).write_bytes(canonical(body));return {'reason':body['reason']}
    test('seed readonly accepted, exact hashes and no authority',lambda: positive(receive(own,a.index_sha256)))
    def replay():
        state=out/'durable-state';code,body=receive(own,a.index_sha256,state)
        need(code==0 and body['status']=='ACCEPTED_DURABLE_DELIVERY','DURABLE_ACCEPT')
        ledger=state/'delivery-receipts.jsonl';b=ledger.read_bytes();code,r=receive(own,a.index_sha256,state)
        need(code!=0 and r['status']=='QUARANTINE' and 'REPLAY' in r['reason'],'REPLAY_REJECT')
        need(ledger.read_bytes()==b,'REPLAY_NO_LEDGER_ADVANCE');need(not (state/'delivery-receiver.lock').exists(),'LOCK_CLOSED')
        return {'receiptSha256':sha(b),'acceptedCaptureCount':body['captureCount']}
    test('durable acceptance then independent process restart rejects replay without ledger change',replay)
    test('wrong receiver refused before state creation',lambda:refusal('wrong-receiver',lambda i,f:None,'INDEX_SCHEMA_OR_RECEIVER',receiver='qa-other-receiver'))
    for k,v in [('flightRun','s'+'0'*20),('flightBoot','qa-prior-flight-boot'),('modelSha256','1'*64),('planSha256','2'*64)]:
        def case(k=k,v=v):
            def change(i,f):
                def mod(s,m):s['context'][k]=v;m['context'][k]=v;m['link'][k]=v
                f['capture-01.tar']=recapture(base['capture-01.tar'],mod)
            return refusal('integrity-valid-'+k,change,'CAPTURE_FLIGHT_CONTEXT_LINK_MISMATCH')
        test('fully rehashed '+k+' cannot cross flight boundary',case)
    def coords(i,f):
        def mod(s,m):s['position']['latitudeDeg']+=0.001
        f['capture-01.tar']=recapture(base['capture-01.tar'],mod)
    test('fully rehashed coordinate fiction refused against raw',lambda:refusal('coordinate-fiction',coords,'CAPTURE_RAW_HOST_REFERENCE_MISMATCH'))
    def tamper(i,f):
        # rehash outer index deliberately, leave inner JPEG hash stale
        b=bytearray(base['capture-01.tar']);b[1024]^=1;f['capture-01.tar']=bytes(b)
    test('outer rehashed image corruption refused by inner hashes',lambda:refusal('image-corrupt',tamper,'FILE_HASH_SIZE_OR_PATH'))
    def duplicate(i,f):
        b=base['capture-01.tar'];x=unpack(b);f['capture-01.tar']=tar([(n,x[n]) for n in ('original.jpg','sidecar.json','manifest.json','original.jpg')])
    test('duplicate archive member refused',lambda:refusal('duplicate-member',duplicate,'TAR_EXACT_THREE_MEMBERS'))
    test('aligned nonzero trailing archive bytes refused',lambda:refusal('trailing-bytes',lambda i,f:f.update({'capture-01.tar':base['capture-01.tar']+b'x'*512}),'TAR_EXACT_THREE_MEMBERS'))
    def size(i,f):
        b=bytearray(base['capture-01.tar']);b[124:136]=b'77777777777\0';b[148:156]=b'        ';b[148:156]=('%06o\0 '%sum(b[:512])).encode();f['capture-01.tar']=bytes(b)
    test('valid-checksum oversized TAR header refused without allocation',lambda:refusal('oversized-header',size,'TAR_MEMBER_SIZE'))
    test('truncated archive refused',lambda:refusal('truncated',lambda i,f:f.update({'capture-01.tar':base['capture-01.tar'][:-1024]}),'TAR_EXACT_THREE_MEMBERS'))
    def duplicate_capture(i,f):f['capture-02.tar']=base['capture-01.tar']
    test('duplicate transfer disguised as second capture refused',lambda:refusal('duplicate-transfer',duplicate_capture,'DELIVERY_DUPLICATE_CAPTURE_PACKAGE_OR_TRANSFER'))
    after={str(seed/n):sha((seed/n).read_bytes()) for n in names};need(before==after,'OLD_SEED_CHANGED')
    report={'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'scope':'CONTRACTOR_ADVERSARIAL_RECEIVER_INPUTS_RETAINED_SITL_SEED_NOT_FIELD02_ANDROID_SAF_OR_NEW_FLIGHT','cli':str(cli.relative_to(ROOT)),'cliSha256':sha(cli.read_bytes()),'seedFingerprints':before,'protectedSeedUnchanged':True,'results':results,'passed':sum(x['status']=='PASS' for x in results),'failed':sum(x['status']=='FAIL' for x in results),'actualImages':0,'authorityRestorable':False}
    (out/'results.json').write_bytes(canonical(report));print(json.dumps(report,indent=2));return int(report['failed']>0)
def positive(value):
    code,b=value;need(code==0 and b.get('status')=='VALIDATED_NO_LEDGER_WRITE','POSITIVE_SEED_REQUIRED');need(b.get('acceptedSimulatorExecution') is True and b.get('captureCount')==2,'KNOWN_SEED_CONTENT');need(b.get('actualImages')==0 and b.get('restoredAuthority')=='NONE','TRUTHFUL_SEED');return {'captureCount':b['captureCount'],'acceptedSimulatorExecution':True}
if __name__=='__main__':sys.exit(main())
