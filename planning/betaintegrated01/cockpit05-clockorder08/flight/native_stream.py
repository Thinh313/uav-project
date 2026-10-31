"""Indexed read-only native tar; ≤1 MiB segment working set, no extraction.

The frozen chain/input-to-wire receiver runs against lazy segment paths. Its
bounded causality maps are retained during verification, but no full raw table
or full row list is built. Subsequent fact passes recheck every segment against
its already verified seal. Whole tar SHA is also pinned between passes.
"""
from pathlib import Path
import base64,hashlib,importlib.util,json,re,tarfile
ROOT=Path(__file__).resolve().parents[4]
MIB=2**20
TAR_LIMIT=168*MIB
RUN_LIMIT=160*MIB
MEMBER_LIMIT=1024
SEGMENT_LIMIT=MIB


def file_sha(path):
    h=hashlib.sha256()
    with open(path,'rb')as f:
        for block in iter(lambda:f.read(MIB),b''):h.update(block)
    return h.hexdigest()


class IndexedNative:
    def __init__(self,path,prefix):
        self.path=Path(path);self.prefix=prefix;self.members={};self.expected={}
        if self.path.stat().st_size>TAR_LIMIT:raise ValueError('NATIVE_TAR_168MIB_BOUND')
        self.tar_sha=file_sha(self.path);total=0
        with tarfile.open(self.path,mode='r:')as archive:
            count_all=0
            for member in archive:
                count_all+=1
                if count_all>2048:raise ValueError('NATIVE_TAR_GLOBAL_MEMBERS_BOUND')
                if not member.isfile()or not member.name.startswith(prefix):continue
                name=member.name[len(prefix):]
                if not(re.fullmatch(r'(?:session|manifest)\.json|writer\.lock|(?:seal-\d{6}\.json)|(?:segment-\d{6}\.jsonl)',name)):
                    raise ValueError('NATIVE_RUN_MEMBER_ALLOWLIST')
                bound=SEGMENT_LIMIT if name.startswith('segment-')else(0 if name=='writer.lock'else 65536)
                if name in self.members or member.size>bound:raise ValueError('NATIVE_MEMBER_DUPLICATE_OR_BOUND')
                self.members[name]=member;total+=member.size
                if len(self.members)>MEMBER_LIMIT or total>RUN_LIMIT:raise ValueError('NATIVE_SELECTED_RUN_160MIB_BOUND')
        terminal_raw=self.read('session.json');self.terminal=json.loads(terminal_raw)
        count=self.terminal.get('segments')
        if type(count)is not int or not 1<=count<=256:raise ValueError('NATIVE_SEGMENTS_BOUND')
        required={'session.json'}|({'manifest.json'}if'manifest.json'in self.members else set())|({'writer.lock'}if'writer.lock'in self.members else set())|{f'{kind}-{n:06}.{suffix}'for n in range(count)for kind,suffix in [('seal','json'),('segment','jsonl')]}
        if set(self.members)!=required:raise ValueError('NATIVE_EXACT_SEGMENT_SET')
        for n in range(count):
            seal=json.loads(self.read(f'seal-{n:06}.json'))
            self.expected[f'segment-{n:06}.jsonl']=seal['sha256']
        self.total=total

    def read(self,name):
        if self.path.stat().st_size>TAR_LIMIT:raise ValueError('NATIVE_TAR_CHANGED_BOUND')
        with tarfile.open(self.path,mode='r:')as archive:
            member=self.members[name]
            body=archive.extractfile(member).read(member.size+1)
        if len(body)!=member.size:raise ValueError('NATIVE_MEMBER_SHORT')
        if name in self.expected and hashlib.sha256(body).hexdigest()!=self.expected[name]:raise ValueError('NATIVE_BODY_NOT_VERIFIED_SEAL')
        return body

    def unchanged(self):
        if file_sha(self.path)!=self.tar_sha:raise ValueError('NATIVE_TAR_CHANGED_DURING_READ')

    def rows(self):
        for n in range(self.terminal['segments']):
            body=self.read(f'segment-{n:06}.jsonl')
            for line in body.splitlines(keepends=True):yield json.loads(line)
        self.unchanged()


class LazyPath:
    def __init__(self,source,name=''):self.source,self.name=source,name
    def __truediv__(self,name):return LazyPath(self.source,self.name+'/'+name if self.name else name)
    def read_bytes(self):return self.source.read(self.name)


def closed_native(path,prefix,external_anchor):
    source=IndexedNative(path,prefix)
    from . import native_chain as module
    # Exact previously exercised SHA/chain/seal, input age/axes and wire mapping.
    cold=module.native_cold(LazyPath(source),external_anchor)
    source.unchanged()
    # Do not publish huge per-record arrays as duplicated evidence. Every record
    # was inspected above; raw remains in the original immutable tar.
    report={k:v for k,v in cold.items()if k not in('normalRC','RX')}
    report.update(normalRCCount=len(cold['normalRC']),RXCount=len(cold['RX']),
                  nativeTarSHA256=source.tar_sha,selectedRunBytes=source.total,
                  reader='INDEXED_SINGLE_SEGMENT_NO_EXTRACTION',maximumTarBytes=TAR_LIMIT,
                  maximumSelectedRunBytes=RUN_LIMIT)
    del cold
    return report,source.rows()
