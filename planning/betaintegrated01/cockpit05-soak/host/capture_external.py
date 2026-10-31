"""Root-only bounded outside-raw receipts for05. Import performs no IO/action."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,sys,time
from importlib import import_module
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
H='planning.betaintegrated01.cockpit05-soak.host'
contract=import_module(H+'.contract');receiver=import_module(H+'.receiver05')
E=R/contract.EVIDENCE


def read(path,bound=262144):
    p=Path(path)
    if p.stat().st_size>bound:raise ValueError('OUTSIDE_METADATA_BOUND')
    return json.loads(p.read_bytes())


def last_receipt(path):
    p=Path(path)
    if p.stat().st_size>262144:raise ValueError('LIVE_STDOUT_RECEIPT_BOUND')
    rows=[]
    for line in p.read_bytes().splitlines():
        try:value=json.loads(line)
        except(ValueError,UnicodeError):continue
        if type(value)is dict and all(k in value for k in('run','epoch','boot')):rows.append(value)
    if len(rows)!=1:raise ValueError('UNIQUE_PARENT_STDOUT_RECEIPT_REQUIRED')
    return rows[0]


def write_metadata(path,value):
    """Existing Root guardian protects this finite closure/cold metadata sequence.
    No new journal, DiskGuard or fresh admission is constructed after the run.
    """
    raw=(json.dumps(value,indent=2)+'\n').encode()
    if len(raw)>262144:raise ValueError('OUTSIDE_RECEIPT262KiB_BOUND')
    guardian=E/'emulator01'
    if not(guardian/'launch.json').is_file()or(guardian/'closure.json').exists():raise ValueError('ONGOING_OWNED_GUARDIAN_REQUIRED_FOR_METADATA')
    with(guardian/'guard.jsonl').open('rb')as f:
        f.seek(0,2);n=f.tell();f.seek(max(0,n-65536));lines=f.read().splitlines()
    row=json.loads(lines[-1]);age=time.monotonic_ns()-row['hostNs']
    if not 0<=age<=2_000_000_000:raise ValueError('ONGOING_GUARDIAN_OBSERVATION_STALE')
    if shutil.disk_usage(R).free<10*2**30+256*2**20+len(raw):raise ValueError('METADATA_LIVE_FLOOR_RESERVE')
    with Path(path).open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
    fd=os.open(Path(path).parent,os.O_RDONLY);os.fsync(fd);os.close(fd)


def capture(case='actual-combined01'):
    if case!='actual-combined01':raise ValueError('SELECTED05_CASE_ONLY')
    C=E/case/'control';binding=read(C/'launch-binding.json');context={k:binding[k]for k in('run','epoch','boot','generation','operator','profileId','binarySHA256','configSHA256')}
    package=read(C/'installed-package-observation.json')
    value=receiver.capture_outside_anchors(last_receipt(C/'backend-control-stdout.txt'),last_receipt(C/'container-control-stdout.txt'),read(C/'native-last-external-observation.json'),context,packageObservation=package)
    value.update(rootObservedHostNs=time.monotonic_ns(),closure=read(C/'closure.json'),outsideRawSourceSHA256=contract.sha(__file__))
    write_metadata(C/'external-anchors.json',value)
    return {'case':case,'backendAnchorRetained':True,'APAnchor':value['liveParentAP']['terminalSHA256'],'nativeAnchor':value['nativeClosedCheckpoint']['journal']['commitAnchor'],'scope':'OUTSIDE_ROOT_RECEIPTS_NOT_FLIGHT_ACCEPTANCE'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('case',nargs='?',default='actual-combined01');args=parser.parse_args();print(json.dumps(capture(args.case)))
