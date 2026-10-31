from pathlib import Path
import ctypes,errno,hashlib,json,os,struct,sys,threading,zlib
R=Path(__file__).resolve().parents[4];S=R/'planning/hostdiag11/runtime/source';os.environ['AERIS_REPOSITORY_ROOT']=str(R);sys.path[:0]=[str(S),str(R)]
from aeris_runtime import darwin_disk11 as d,guardian_cause11 as cause

class Clock:
 def __init__(self):self.n=1_000_000_000
 def __call__(self):self.n+=1000;return self.n
 def advance(self,n):self.n+=n
class Probe:
 def __init__(self,clock,count=20):
  self.clock=clock;self.values={p:{'pid':p,'start':100+p,'uuid':bytes([p%255+1])*16,'written':1000,'footprint':2000,'name':('p'+str(p)).encode(),'nameTruncated':False,'nameUnavailable':False}for p in range(1,count+1)};self.free=20*2**30;self.swap=0;self.files={};self.denied=set();self.truncated=False;self.hook=None
 def volume_free(self):return self.free
 def volume_device(self):return 7
 def volume_inode(self):return 8
 def swap_used(self):return self.swap
 def pids(self):return list(self.values),self.truncated
 def process(self,pid):
  if self.hook:self.hook(pid)
  if pid in self.denied:raise PermissionError(errno.EACCES,'mock')
  return dict(self.values[pid])
 def physical(self,path):return self.files.get(str(path),(d.F_MISSING,errno.ENOENT,0,0,0))
def observer(count=20,paths=None):
 clock=Clock();probe=Probe(clock,count);o=d.HostDiskObserver('/synthetic',paths or [],candidate='d'*64,source='e'*64,probe=probe,now=clock,cpu=clock);return o,probe,clock
def decoded(o):return d.decode(o.export(),candidate='d'*64,source='e'*64)
def fail(fn):
 try:fn()
 except Exception:return
 raise AssertionError('invalid accepted')
def header_rewrite(raw,change):
 magic,n=d.FILE.unpack_from(raw);h=json.loads(raw[d.FILE.size:d.FILE.size+n]);change(h);b=json.dumps(h,separators=(',',':')).encode();return d.FILE.pack(magic,len(b))+b+raw[d.FILE.size+n:]
def run():
 groups=[]
 o,p,c=observer();o.sample()
 for pid,v in p.values.items():v['written']+=pid
 o.sample();x=decoded(o);row=x['rows'][-1];assert len(row['processes'])==16 and row['allDelta']==210 and row['otherDelta']==10 and all(v['writeDelta']==v['pid']for v in row['processes']);groups.append('selected_previous_current_counter_exact_top16_otheraggregate_not_full_history')
 p.values[20]['start']+=1;p.values[19]['written']=1;p.values[18]['uuid']=b'\0'*16;p.values[17]['name']=b'';p.values[17]['nameUnavailable']=True;o.sample();row=decoded(o)['rows'][-1];by={v['pid']:v for v in row['processes']};assert by.get(20,{'writeDelta':None})['writeDelta']is None and row['first']>=2 and row['resets']==1;groups.append('pid_start_uuid_reuse_reset_and_missing_name_not_zero_interval')
 paths=[Path('/physical/a'),Path('/physical/b'),Path('/physical/c')];o,p,c=observer(1,paths);p.files={str(paths[0]):(1,0,7,11,100),str(paths[1]):(1,0,7,11,100),str(paths[2]):(1,0,9,20,500)};o.sample();p.free-=100
 p.files={str(paths[0]):(1,0,7,11,200),str(paths[1]):(1,0,7,11,200),str(paths[2]):(1,0,9,20,1500)};o.sample();x=decoded(o);assert x['changes'][-1]['observedPositiveSameInodeGrowthBytes']==100 and x['changes'][-1]['unexplainedDifferenceBytes']==0 and x['causalProcess']=='UNKNOWN';p.files[str(paths[0])]=(1,0,7,12,1000);o.sample();assert decoded(o)['changes'][-1]['physicalPathDeltas'][0]['sameInodeAllocatedDelta']is None;groups.append('samevolume_inode_physical_alias_dedup_and_replacement_no_refund_no_process_causality')
 o,p,c=observer(2,[Path('/denied')]);p.denied={2};p.files['/denied']=(3,errno.EACCES,0,0,0);p.truncated=True;o.sample();p.swap=2**30;o.sample();x=decoded(o);assert x['rows'][-1]['unreadable']==1 and x['rows'][-1]['truncated']==1 and x['rows'][-1]['physical'][0]['errno']==errno.EACCES and x['causalProcess']=='UNKNOWN';groups.append('permission_truncation_sparsecoverage_and_swapusage_not_allocated_disk')
 o,p,c=observer(1)
 for _ in range(40):o.sample()
 o.retire();frozen=o.export()
 for _ in range(40):o.sample()
 x=decoded(o);assert x['header']['total']==40 and x['header']['overwritten']==8 and x['rows'][0]['sequence']==9 and x['rows'][-1]['sequence']==40
 o2,p2,c2=observer(1);o2.sample();p2.hook=lambda pid:o2.retire();assert o2.sample()is None;assert decoded(o2)['header']['total']==1 and decoded(o2)['header']['inflightDiscardedAfterRetirement']==1;groups.append('firstretire_freezes32_context_through40cleanup_calls_and_inflight_append_race')
 o,p,c=observer(2,[Path('/timeout')]);p.hook=lambda pid:c.advance(600_000_000);o.sample();row=decoded(o)['rows'][0];assert row['flags']&d.S_OVERRUN and row['end']-row['begin']>d.SAMPLE_NS and row['physical'][0]['errno']==errno.ETIMEDOUT;groups.append('actual_sample_overrun_not_retimed_or_silently_complete')
 o,p,c=observer(16,[Path('/worst/'+str(n))for n in range(24)])
 for _ in range(32):o.sample()
 raw=o.export();assert len(raw)<=d.WORST_BYTES<=65536 and len(decoded(o)['rows'])==32 and d.PROCESS.size==64 and d.PHYSICAL.size==32 and d.SAMPLE.size==104;groups.append('fixed_uncompressed_32x16x24_worst65036_bytes')
 bad=bytearray(raw);bad[-1]^=1;fail(lambda:d.decode(bytes(bad)));fail(lambda:d.decode(raw+b'x'));fail(lambda:d.decode(raw,candidate='f'*64))
 for change in [lambda h:h.update(rows=True),lambda h:h.update(rows=-1),lambda h:h.update(paths=['/a','/a']),lambda h:h.update(paths=[{}]),lambda h:h.update(sourceSHA256='bad'),lambda h:h.update(scope='FAKE')]:fail(lambda change=change:d.decode(header_rewrite(raw,change)))
 groups.append('codec_crc_trailing_foreignscope_badtypes_duplicatepaths_failclosed')
 o,p,c=observer(2);o.sample()
 for v in p.values.values():v['written']=d.UNKNOWN-1
 fail(o.sample);groups.append('aggregate_uint64_overflow_rejected_not_wrap_or_zero')
 q=d.DarwinProbe.__new__(d.DarwinProbe)
 class Lib:
  def proc_listallpids(self,*args):ctypes.set_errno(errno.EPERM);return 0
 q.lib=Lib();fail(q.pids);assert ctypes.sizeof(d.RUsageV2)==160 and ctypes.sizeof(d.SwapUsage)==32;groups.append('actual_wrapper_zero_errno_and_localSDK160_32B_ABI')
 b={'version':1,'instance':'1'*32,'pid':123,'processStart':'synthetic','guardianSourceSHA256':'2'*64,'healthSourceSHA256':'3'*64,'budgetSourceIdentity':'4'*64,'budgetRoot':'/mock/budget','evidenceRoot':'/mock'};nonce='5'*32;r=json.loads(cause.fault_envelope(b,nonce,'DiskGuardError:MOCK',1100));primary=ValueError('HOST_HEALTH_TYPED_RESPONSE');cause.annotate(primary,r,b,nonce,1000,1200,123);v=cause.diagnostic(primary);assert v['status']=='SOURCE_BOUND_DIAGNOSTIC_ONLY'and v['authority']is False and str(primary)=='HOST_HEALTH_TYPED_RESPONSE'and type(primary)is ValueError
 for key,value in [('challenge','6'*32),('guardianSourceSHA256','7'*64),('responseHostNs',1300),('diagnosticOnly',False),('pid',True)]:
  other=ValueError('HOST_HEALTH_TYPED_RESPONSE');rr={**r,key:value};v=cause.annotate(other,rr,b,nonce,1000,1200,123);assert v is None or v['status']=='UNTRUSTED_DIAGNOSTIC'
 other=ValueError('HOST_HEALTH_TYPED_RESPONSE');cause.annotate(other,r,b,nonce,0,100_000_001,123);assert cause.diagnostic(other)['status']=='UNTRUSTED_DIAGNOSTIC';forged=ValueError('same');forged.guardianCause={'failure':'forged'};assert cause.diagnostic(forged)is None;groups.append('authentic_fault_annotation_neverauthority_wrongpeer_source_nonce_time_and_forgedattribute_rejected')
 return groups
if __name__=='__main__':
 out=R/sys.argv[1];groups=run();files=[S/'aeris_runtime/darwin_disk11.py',S/'aeris_runtime/guardian_cause11.py'];v={'format':'aeris-hostdiag11-builder-pure-mock','status':'PASS','groups':groups,'passed':len(groups),'sourceSHA256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files},'actualHostCollectorOrAndroidAPStarted':False,'scratchCreated':False,'worstBinaryBytes':d.WORST_BYTES}
 with out.open('x')as f:json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps({'status':'PASS','groups':len(groups),'path':str(out)}))
