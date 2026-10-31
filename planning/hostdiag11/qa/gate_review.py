"""Independent source gate and lean original-byte preservation proof.

No runtime actors, slot, candidate, ledger, signing or source mutations. Full
legacy checks execute read-only in memory; the existing entry rows remain the
auditable baseline instead of duplicating them into the admission domain.
"""
from pathlib import Path
import ast,datetime,hashlib,json,os,stat,sys,time

R=Path(__file__).resolve().parents[3];S=R/'planning/hostdiag11/runtime/source'
sys.path[:0]=[str(S),str(R)];os.environ['AERIS_REPOSITORY_ROOT']=str(R)
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def ref(p):return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':H(p)}

def check_ipc_entry():
    p=R/'evidence/hostdiag11/qa/PRESERVATION-ENTRY01.json';v=json.loads(p.read_bytes())
    assert v['status'].startswith('PASS_LEGACY_')
    for x in v['ipc10EntryRows']:
        f=R/x['path']
        if x.get('kind')=='symlink':assert f.is_symlink()and os.readlink(f)==x['target'];continue
        s=f.stat();assert not f.is_symlink()
        assert [s.st_size,stat.S_IMODE(s.st_mode),s.st_mtime_ns,s.st_dev,s.st_ino,H(f)]==[x[k]for k in ['bytes','mode','mtimeNs','device','inode','sha256']],x['path']
    return {'baseline':ref(p),'entries':len(v['ipc10EntryRows']),'drift':[]}

def full_legacy():
    f=R/'planning/betasim-integrated01/qa/frozen_release08.py';text=f.read_text();marker="\nout=E/'qa/FROZEN-CANDIDATE-REVIEW08.json'";assert text.count(marker)==1
    ns={'__file__':str(f)};exec(compile(text.split(marker)[0],str(f),'exec'),ns);v=ns['report'];assert v['status'].startswith('PASS_READONLY_')
    p=R/'evidence/hosthealth-ipc10/qa/BASELINE-PRESERVATION01.json';b=json.loads(p.read_bytes());e=R/'evidence/betasim-integrated01'
    assert H(e/'r07/metadata-budget/metadata-ledger.json')==b['r07LedgerSHA256']
    for x in b['r08AllOriginalFiles']:
        f=e/'r08'/x['path'];s=f.stat();assert s.st_size==x['bytes']and stat.S_IMODE(s.st_mode)==x['mode']and H(f)==x['sha256']
    return {'verifier':ref(R/'planning/betasim-integrated01/qa/frozen_release08.py'),'entryProofReference':ref(R/'evidence/hostdiag11/qa/PRESERVATION-ENTRY01.json'),'fullLegacyFreshReadOnlyStatus':v['legacyPreservation']['status'],'legacyEntries':v['legacyPreservation']['legacyEntries'],'seals':len(v['legacyPreservation']['seals']),'ENDUREIdentities':v['legacyPreservation']['endureIdentities'],'oldCandidateFullLoads':len(v['oldCandidateFullLoads']),'R08OriginalFiles':len(b['r08AllOriginalFiles']),'R07LedgerUnchanged':True,'preexistingMissing':v['preexistingMissingNotRestored'],'drift':[]}

def main():
    started=time.monotonic_ns();out=R/sys.argv[1];hold=R/sys.argv[2]
    assert out.is_relative_to(R/'evidence/hostdiag11/qa')and not out.exists()
    hv=json.loads(hold.read_bytes())
    for n,h in hv['inputPins'].items():assert H(R/n)==h,n
    from aeris_runtime.pipeline_contract import require_closed_contract
    from aeris_runtime.product_inputs import validate
    from aeris_runtime.metadata_budget import observer_envelope
    proof=require_closed_contract();graph=validate()
    base=R/'evidence/hosthealth-ipc10/candidates/8e6b9a467f97776247b45e6cfaf88357e566c17b079416921aff19d0ee49e9ef'
    old=json.loads((base/'candidate.json').read_bytes());oldpins=json.loads((base/'source/aeris_runtime/assets/pipeline-writer-pins.json').read_bytes());assert observer_envelope()==oldpins['envelope']
    for n,h in old['sourceSHA256'].items():
        if n in ['aeris_runtime/policy.py','aeris_runtime/admission.py']or n.startswith('aeris_runtime/foundation/'):assert H(S/n)==h,n
    def named(path):return {x.name:ast.dump(x,include_attributes=False)for x in ast.parse(path.read_text()).body if isinstance(x,(ast.ClassDef,ast.FunctionDef))}
    a=named(base/'source/aeris_runtime/host_health.py');b=named(S/'aeris_runtime/host_health.py')
    for k in a:
        if k not in ['HealthServer','GuardianClient']:assert a[k]==b[k],'ORIGINAL_HEALTH_GUARD_CHANGED:'+k
    payload={str(Path('aeris_runtime')/p.relative_to(S/'aeris_runtime')):H(p)for p in sorted((S/'aeris_runtime').rglob('*'))if p.is_file()and '__pycache__'not in p.parts and p.suffix in('.py','.json','.txt','.parm')}
    receipt=R/'evidence/betasim-integrated01/product/native-application09-build01.json';assert H(receipt)=='e3585254a05626ff10deeab86359a92a43f15828b213fd77dcd70e00e6ba48b0';nr=json.loads(receipt.read_bytes());assert H(R/nr['apk'])==nr['sha256']and H(R/nr['inputArchive'])==nr['inputArchiveSHA256']
    prior=R/'evidence/hostdiag11/qa/INDEPENDENT-FAULTS02.json';iv=json.loads(prior.read_bytes());assert iv['status'].startswith('PASS_')
    for n,h in iv['sourceSHA256'].items():assert H(R/n)==h
    passive=R/'evidence/hostdiag11/qa/PASSIVE-COLD-REVIEW01.json';assert json.loads(passive.read_bytes())['status'].startswith('PASS_REAL_HOST_')
    legacy=full_legacy();ipc=check_ipc_entry()
    result={'format':'aeris-hostdiag11-independent-source-gate','version':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','sourceSHA256':payload,'nativeBuildReceiptSHA256':H(receipt),'productSourceSHA256':graph['pins'],'sourceWriterContract':proof,'HOLD':ref(hold),'heldPlanningPinsUnchanged':len(hv['inputPins']),'guards':'ORIGINAL_POLICY_ADMISSION_FOUNDATION_AND_ALL_HEALTH_GUARDS_UNCHANGED','mockIndependent':ref(prior),'passiveColdReview':ref(passive),'legacyPreservation':legacy,'IPC10Preservation':ipc,'sourceMutableAssetsOnly':False,'actorsStarted':False,'candidateFrozen':False,'actualShortAcceptance':False,'scope':'SOURCE_MOCK_PASSIVE_ONLY_FRESH_RUNTIME_ADMISSION_AND_NATIVE_COUNTERS_STILL_REQUIRED','knownLimits':['Processunreadablecounterdoesnotretainindividualerrnoorpermission/exitclassification.','CausalprocessremainsUNKNOWNwithoutanobservedallocationjoin.','Terminal/reportcauseannotationdoesnotchangeheldnativeUI.'],'elapsedNs':time.monotonic_ns()-started}
    with out.open('x')as f:json.dump(result,f,separators=(',',':'));f.write('\n')
    print(json.dumps({'status':'PASS','path':str(out.relative_to(R)),'sha256':H(out),'sourceFiles':len(payload),'productFiles':len(graph['pins']),'elapsedSeconds':result['elapsedNs']/1e9}),flush=True)

if __name__=='__main__':main()
