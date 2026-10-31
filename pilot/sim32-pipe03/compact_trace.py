"""Reclaim only unused zero pages of CLOSED private traces; exact bytes unchanged."""
import ctypes,struct,hashlib,os,json,sys
from pathlib import Path
class Punch(ctypes.Structure):
    _fields_=[('flags',ctypes.c_uint),('reserved',ctypes.c_uint),('offset',ctypes.c_int64),('length',ctypes.c_int64)]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def compact(out):
    assert sys.platform=='darwin','Only documented Darwin F_PUNCHHOLE ABI admitted'
    assert(out/'closure.json').exists(),'No compaction before owned closure'
    receipts=[];lib=ctypes.CDLL(None,use_errno=True);lib.fcntl.argtypes=[ctypes.c_int,ctypes.c_int];lib.fcntl.restype=ctypes.c_int
    for name in ['ap-timing.bin','backend-stages.bin']:
        p=out/name
        if not p.exists():continue
        before=sha(p);st=p.stat()
        with p.open('rb')as f:
            header=f.read(40)
            if name=='ap-timing.bin':magic,cap,n,failed,size=struct.unpack('<8s4Q',header);assert magic==b'AERISD02'and failed==0 and size==64
            else:magic,cap,n,size=struct.unpack('<8s3Q',header[:32]);assert magic==b'AERISBH1'and size==88
            assert n<=cap;start=((4096+n*size+4095)//4096)*4096
            f.seek(start)
            for b in iter(lambda:f.read(1048576),b''):assert not any(b),'Nonzero trailing data never reclaimed'
        length=st.st_size-start
        if length>0:
            with p.open('r+b')as f:
                punch=Punch(0,0,start,length);ret=lib.fcntl(f.fileno(),99,ctypes.byref(punch))
                if ret:raise OSError(ctypes.get_errno(),'F_PUNCHHOLE failed')
                os.fsync(f.fileno())
        after=sha(p);assert after==before and p.stat().st_size==st.st_size
        receipts.append({'file':name,'sha256Before':before,'sha256After':after,'sizeUnchanged':st.st_size,'retainedEvents':n,'zeroTailStart':start,'allocatedBeforeBytes':st.st_blocks*512,'allocatedAfterBytes':p.stat().st_blocks*512})
    with(out/'trace-compaction.json').open('x')as f:json.dump({'status':'EXACT_BYTES_UNCHANGED_ZERO_TAIL_RECLAIMED','files':receipts,'scope':'Only current task closed traces; no frozen or ENDURE mutation'},f,indent=2);f.write('\n')
    return receipts
