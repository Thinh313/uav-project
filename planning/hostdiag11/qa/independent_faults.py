"""Independent synthetic counter/fault checks. Never probes the actual host.

Old RAM transport fixtures are reused as explicitly synthetic inputs, loaded
without their main/output paths. The implementation under test is HOSTDIAG11.
"""
from pathlib import Path
from types import SimpleNamespace
import base64,hashlib,json,os,struct,sys,threading,time,traceback,zlib
import ctypes

R=Path(__file__).resolve().parents[3]
S=R/'planning/hostdiag11/runtime/source'
sys.path[:0]=[str(S),str(R)]
os.environ['AERIS_REPOSITORY_ROOT']=str(R)
from aeris_runtime import darwin_disk11 as disk,guardian_cause11 as cause

H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Clock:
    def __init__(self):self.ns=1_000_000_000
    def now(self):self.ns+=1000;return self.ns
    def advance(self,n=1_000_000_000):self.ns+=n

class FakeProbe:
    def __init__(self):
        self.free=30*2**30;self.swap=0;self.ids=[];self.process_rows={};self.files={};self.truncated=False
    def volume_free(self):return self.free
    def volume_device(self):return 9
    def volume_inode(self):return 1
    def swap_used(self):return self.swap
    def pids(self):return list(self.ids),self.truncated
    def process(self,pid):
        v=self.process_rows[pid]
        if isinstance(v,BaseException):raise v
        return dict(v)
    def physical(self,path):return self.files.get(str(path),(disk.F_MISSING,2,0,0,0))

def process(pid,written,*,start=100,uuid=b'A'*16,name=b'QA'):
    return {'pid':pid,'start':start,'uuid':uuid,'written':written,'footprint':4096,'name':name}

def observer(probe=None,paths=()):
    p=probe or FakeProbe();c=Clock()
    return disk.HostDiskObserver('/EXPLICIT_QA',list(paths),candidate='a'*64,source='b'*64,probe=p,now=c.now),p,c

def decoded(o):return disk.decode(o.export(),candidate='a'*64,source='b'*64)

def freeze(o):
    fn=getattr(o,'retire',None)
    assert callable(fn),'MISSING_NONBLOCKING_FIRST_FAILURE_FREEZE'
    return fn()

def replace_header(raw,change):
    magic,n=disk.FILE.unpack_from(raw);h=json.loads(raw[disk.FILE.size:disk.FILE.size+n]);change(h)
    b=json.dumps(h,separators=(',',':')).encode()
    return disk.FILE.pack(magic,len(b))+b+raw[disk.FILE.size+n:]

def need_reject(fn):
    try:fn()
    except (ValueError,RuntimeError,TypeError,struct.error):return
    raise AssertionError('MALFORMED_OR_FOREIGN_INPUT_ACCEPTED')

def disk_tests():
    o,p,c=observer();p.ids=[7];p.process_rows[7]=process(7,1000);o.sample();c.advance();p.process_rows[7]=process(7,1400);o.sample()
    v=decoded(o);a=v['rows'][0]['processes'][0];b=v['rows'][1]['processes'][0]
    assert a['writeDelta']is None and b['writeDelta']==400 and b['previousWritten']==1000 and b['currentWritten']==1400
    assert v['authority']is False and v['causalProcess']=='UNKNOWN'
    yield 'exact_before_current_counters_cold_delta_no_authority_or_causal_claim'

    c.advance();p.process_rows[7]=process(7,900);o.sample();assert decoded(o)['rows'][-1]['processes'][0]['writeDelta']is None
    c.advance();p.process_rows[7]=process(7,999999,start=200);o.sample();q=decoded(o)['rows'][-1]['processes'][0];assert q['writeDelta']is None and q['flags']&disk.P_REUSED
    c.advance();p.process_rows[7]=process(7,1999999,start=200,uuid=b'B'*16);o.sample();assert decoded(o)['rows'][-1]['processes'][0]['writeDelta']is None
    yield 'counter_reset_pid_start_and_uuid_reuse_never_lifetime_as_interval_bytes'

    o,p,c=observer();p.ids=list(range(1,21));p.process_rows={pid:process(pid,1000)for pid in p.ids};o.sample();c.advance()
    p.process_rows={pid:process(pid,1000+pid)for pid in p.ids};o.sample();v=decoded(o)['rows'][-1]
    assert [x['pid']for x in v['processes']]==list(range(20,4,-1))
    assert v['allDelta']==210 and v['otherDelta']==10 and sum(x['writeDelta']for x in v['processes'])==200
    yield 'top16_exact_ranked_intervals_and_explicit_unretained_other_aggregate'

    o,p,c=observer();p.ids=[1,2];p.process_rows={1:PermissionError(1,'QA_DENIED'),2:process(2,10,name=b'')};p.process_rows[2]['nameUnavailable']=True;p.truncated=True;o.sample();v=decoded(o)['rows'][0]
    assert v['unreadable']==1 and v['truncated']==1 and v['probed']==1 and v['flags']&disk.S_TRUNCATED
    flag=getattr(disk,'P_NAME_UNAVAILABLE',getattr(disk,'P_NAME_UNKNOWN',None))
    assert flag is not None and v['processes'][0]['flags']&flag,'MISSING_EXPLICIT_NAME_UNKNOWN'
    yield 'permission_enumeration_cap_and_missing_name_are_observed_unknowns'

    a=Path('/EXPLICIT_QA/a');b=Path('/EXPLICIT_QA/b');o,p,c=observer(paths=[a,b]);p.files={str(a):(disk.F_PRESENT,0,9,99,4096),str(b):(disk.F_PRESENT,0,9,99,4096)};o.sample();c.advance();p.free-=1000;p.swap+=500;p.files={str(a):(disk.F_PRESENT,0,9,99,4608),str(b):(disk.F_PRESENT,0,9,99,4608)};o.sample();v=decoded(o);d=v['changes'][-1]
    assert d['observedPositiveSameInodeGrowthBytes']==512,'DUPLICATE_INODE_DOUBLE_COUNTED'
    assert d['globalFreeDeclineBytes']==1000 and d['unexplainedDifferenceBytes']==488 and v['causalProcess']=='UNKNOWN'
    c.advance();p.files[str(a)]=(disk.F_PRESENT,0,9,123,8192);p.files[str(b)]=(disk.F_MISSING,2,0,0,0);o.sample();d=decoded(o)['changes'][-1]
    assert d['observedPositiveSameInodeGrowthBytes']==0 and all(x['replacementDeletionOrUnknown']for x in d['physicalPathDeltas'])
    yield 'same_inode_physical_growth_deduplicates_aliases_replacement_and_deletion_unknown'

    o,p,c=observer();p.free=disk.UNKNOWN;p.swap=disk.UNKNOWN;o.sample();c.advance();o.sample();v=decoded(o)
    assert v['changes'][-1]['globalFreeDeclineBytes']is None and v['changes'][-1]['unexplainedDifferenceBytes']is None
    yield 'unavailable_global_volume_and_swap_do_not_become_zero_loss'

    fake=disk.DarwinProbe.__new__(disk.DarwinProbe)
    def zero_error(_buffer,_size):ctypes.set_errno(13);return 0
    fake.lib=SimpleNamespace(proc_listallpids=zero_error)
    try:fake.pids();raise AssertionError('ZERO_ERROR_MISREPRESENTED_AS_COMPLETE_EMPTY_PROCESS_LIST')
    except OSError as e:assert e.errno==13
    assert ctypes.sizeof(disk.RUsageV2)==160 and disk.PROCESS.size==64 and disk.PHYSICAL.size==32
    yield 'exact_sdk_layout_and_real_wrapper_zero_with_errno_is_unknown_failure'

    o,p,c=observer()
    for _ in range(40):o.sample();c.advance()
    v=decoded(o);assert len(v['rows'])==32 and v['header']['total']==40 and v['header']['overwritten']==8
    raw=o.export();assert len(raw)<=65536 and disk.WORST_BYTES<=65536
    changed=bytearray(raw);changed[-1]^=1;need_reject(lambda:disk.decode(bytes(changed)))
    for mutate in [lambda h:h.update(rows=True),lambda h:h.update(paths='bad'),lambda h:h.update(rows=-1),lambda h:h.update(rows=33),lambda h:h.update(candidateSHA256='c'*64)]:
        need_reject(lambda m=mutate:disk.decode(replace_header(raw,m),candidate='a'*64,source='b'*64))
    need_reject(lambda:disk.decode(raw+b'x'));need_reject(lambda:disk.decode(raw[:-1]))
    yield 'ring32_exact_overwrite_crc_partial_trailing_and_external_identity_rejection'

    o,p,c=observer();o.sample();c.advance();o.sample();freeze(o);before=decoded(o)['rows']
    for _ in range(40):
        c.advance()
        try:o.sample()
        except RuntimeError:pass
    after=decoded(o)['rows'];assert before==after,'CLEANUP_OVER32_SECONDS_MUTATED_FAILURE_VIEW'
    yield 'first_failure_freeze_survives_more_than32_seconds_cleanup_without_backdating'

    entered=threading.Event();release=threading.Event()
    class BlockingProbe(FakeProbe):
        block=False
        def process(self,pid):
            if self.block:entered.set();assert release.wait(1),'QA_RELEASE_TIMEOUT'
            return super().process(pid)
    p=BlockingProbe();p.ids=[8];p.process_rows[8]=process(8,100);o,p,c=observer(p);o.sample();before=decoded(o)['rows'];p.block=True;o.start()
    try:
        assert entered.wait(1),'QA_INFLIGHT_NOT_ENTERED';began=time.perf_counter_ns();freeze(o);elapsed=time.perf_counter_ns()-began
        assert elapsed<100_000_000,'RETIRE_WAITED_FOR_PROCESS_PROBE';release.set();o.stop();v=decoded(o)
        assert v['rows']==before and v['header']['inflightDiscardedAfterRetirement']>=1
    finally:release.set();o.stop()
    yield 'inflight_probe_retirement_nonblocking_and_frozen_rows_never_mutated'

def guardian_tests():
    old=R/'planning/hosthealth-ipc10/qa/independent_ipc.py'
    text=old.read_text().split('\ndef tests():')[0]
    text=text.replace("S=R/'planning/hosthealth-ipc10/runtime/source'","S=R/'planning/hostdiag11/runtime/source'")
    ns={'__file__':str(old)};exec(compile(text,'synthetic_ram_fixture_reused_no_main','exec'),ns)
    ex=ns['exchange'];require=ns['require_error']
    def changed(mutate=None):
        def apply(v):
            b={k:v[k]for k in ns['binding']()};q=v['challenge'];at=v['responseHostNs'];fault=json.loads(cause.fault_envelope(b,q,'DiskGuardError:EXPLICIT_QA_FAILURE',at))
            if mutate:mutate(fault)
            v.clear();v.update(fault)
        return apply
    x=ex(change=changed());require(x,ValueError,'HOST_HEALTH_TYPED_RESPONSE');d=cause.diagnostic(x.error)
    assert d['status']=='SOURCE_BOUND_DIAGNOSTIC_ONLY'and d['failure']=='DiskGuardError:EXPLICIT_QA_FAILURE'and d['authority']is False
    assert x.result is None
    yield 'authentic_failure_shown_separately_original_schema_error_class_message_and_order_intact'

    for mutate in [lambda f:f.update(challenge='e'*32),lambda f:f.update(processStart='FOREIGN'),lambda f:f.update(version=True),lambda f:f.update(responseHostNs=-1),lambda f:f.update(extra=True),lambda f:f.update(failure='x'*641)]:
        x=ex(change=changed(mutate));require(x,ValueError,'HOST_HEALTH_TYPED_RESPONSE');d=cause.diagnostic(x.error);assert d is None or d['status']=='UNTRUSTED_DIAGNOSTIC'and d['failure']is None and d['authority']is False
    x=ex(elapsed=100_000_001,change=changed());require(x,ValueError,'HOST_HEALTH_TYPED_RESPONSE');assert cause.diagnostic(x.error)['status']=='UNTRUSTED_DIAGNOSTIC'
    yield 'late_wrong_nonce_campaign_typed_binding_causality_extra_fields_and_overbound_fault_never_trusted'

    x=ex(peer_bad=True,change=changed());require(x,RuntimeError,'HOST_HEALTH_KERNEL_PID_BINDING');assert cause.diagnostic(x.error)is None
    x=ex(raw=b'{"failure":"LEGACY_SHORT_FAULT"}\n');require(x,ValueError,'HOST_HEALTH_TYPED_RESPONSE');assert cause.diagnostic(x.error)is None
    forged=RuntimeError('QA_FORGED_CALLER_ATTRIBUTE');forged.guardian_cause={'status':'SOURCE_BOUND_DIAGNOSTIC_ONLY','authority':True};assert cause.diagnostic(forged)is None
    x=ex();assert x.error is None and x.result['alive']is True
    yield 'real_peer_order_legacy_envelope_and_forged_exception_attribute_never_authority_valid_health_unchanged'

def main():
    out=R/sys.argv[1];assert out.is_relative_to(R/'evidence/hostdiag11/qa')and not out.exists()
    paths=[S/'aeris_runtime/darwin_disk11.py',S/'aeris_runtime/guardian_cause11.py',S/'aeris_runtime/host_health.py'];pins={str(p.relative_to(R)):H(p)for p in paths};passed=[];error=None
    try:
        for group in [disk_tests,guardian_tests]:
            for item in group():passed.append(item)
    except BaseException:error=traceback.format_exc()
    end={str(p.relative_to(R)):H(p)for p in paths};v={'format':'aeris-hostdiag11-independent-fault-qa','status':'PASS_SYNTHETIC_SOURCE_FAULTS_NOT_ACTUAL_HOST_OR_RUNTIME'if error is None and pins==end else'FAIL_OR_SOURCE_DRIFT','passed':passed,'failure':error,'sourceSHA256':pins,'sourceStable':pins==end,'qaSourceSHA256':H(Path(__file__)),'hostQueryOrActualCollectorStarted':False,'AndroidOrSITLStarted':False,'fixture':'EXPLICIT_SYNTHETIC_COUNTERS_AND_REUSED_RAM_SOCKET_CLOCK_NO_MAIN','scratchCreated':False}
    with out.open('x')as f:json.dump(v,f,indent=2);f.write('\n')
    print(json.dumps({'status':v['status'],'passedGroups':len(passed),'failure':error,'path':str(out.relative_to(R)),'sha256':H(out)}),flush=True)
    if error is not None or pins!=end:raise SystemExit(1)

if __name__=='__main__':main()
