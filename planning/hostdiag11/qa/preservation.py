"""Read-only legacy verification plus exact IPC10 entry baseline.

Only exclusive new QA evidence is written. Runtime and simulation actors are
never started. Hardlink count may grow for immutable artifact reuse; bytes,
inode, mode and mtime must remain exact.
"""
from pathlib import Path
import datetime,hashlib,json,os,stat,sys,time

R=Path(__file__).resolve().parents[3]
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def rows(root):
    result=[]
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            result.append({'path':str(p.relative_to(R)),'kind':'symlink','target':os.readlink(p)})
        elif p.is_file():
            s=p.stat()
            result.append({'path':str(p.relative_to(R)),'bytes':s.st_size,'mode':stat.S_IMODE(s.st_mode),'mtimeNs':s.st_mtime_ns,'device':s.st_dev,'inode':s.st_ino,'sha256':H(p)})
    return result

def main():
    started=time.monotonic_ns();out=R/sys.argv[1]
    assert out.is_relative_to(R/'evidence/hostdiag11/qa') and not out.exists()
    script=R/'planning/betasim-integrated01/qa/frozen_release08.py'
    source=script.read_text();marker="\nout=E/'qa/FROZEN-CANDIDATE-REVIEW08.json'"
    assert source.count(marker)==1
    namespace={'__file__':str(script)}
    exec(compile(source.split(marker)[0],str(script),'exec'),namespace)
    legacy=namespace['report'];assert legacy['status'].startswith('PASS_READONLY_')
    baseline=R/'evidence/hosthealth-ipc10/qa/BASELINE-PRESERVATION01.json'
    b=json.loads(baseline.read_bytes());er=R/'evidence/betasim-integrated01'
    assert H(er/'r07/metadata-budget/metadata-ledger.json')==b['r07LedgerSHA256']
    expected=b.get('r08AllOriginalFiles',b.get('r08OriginalFilesBaseline'))
    if expected is None:
        # The prior standalone cause carries the same complete 93-file list.
        expected=json.loads((er/'qa/ACTUAL-R08-CAUSE01.json').read_bytes())['originalRowsBaseline']
    assert len(expected)==93
    for row in expected:
        p=er/'r08'/row['path'];s=p.stat()
        assert s.st_size==row['bytes'] and stat.S_IMODE(s.st_mode)==row['mode'] and H(p)==row['sha256']
    current=[]
    for root in [R/'planning/hosthealth-ipc10',R/'evidence/hosthealth-ipc10']:
        current.extend(rows(root))
    compared=None
    if len(sys.argv)>2:
        prior=R/sys.argv[2];old=json.loads(prior.read_bytes())
        assert current==old['ipc10EntryRows'],'OLD_IPC10_SCOPE_DRIFT'
        compared={'path':str(prior.relative_to(R)),'sha256':H(prior),'entries':len(current)}
    report={'format':'aeris-hostdiag11-readonly-preservation','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_LEGACY_AND_IPC10_BYTES_MODES_INODES_MTIME_NOT_RUNTIME_ACCEPTANCE','legacyProof':legacy,'legacyVerifierSource':{'path':str(script.relative_to(R)),'sha256':H(script)},'r08All93OriginalsUnchanged':True,'r07LedgerUnchanged':True,'ipc10EntryRows':current,'comparedBaseline':compared,'actualActorsStarted':False,'sourceMutated':False,'preexistingMissing':legacy['preexistingMissingNotRestored'],'elapsedNs':time.monotonic_ns()-started}
    with out.open('x')as f:json.dump(report,f,separators=(',',':'));f.write('\n')
    print(json.dumps({'status':report['status'],'path':str(out.relative_to(R)),'sha256':H(out),'ipc10Entries':len(current),'elapsedSeconds':report['elapsedNs']/1e9}),flush=True)

if __name__=='__main__':main()
