"""Mock tests for the LINUXPORT01 m802 continuation contract. Read-only on evidence; mocks live in a temp dir.

Positive: the team m802 raw (both capture attempts, same bytes) and a re-packed copy in another
member order. Negative: the real earlier states (m801 83-file, 79-file, 75-file), the old
contract-l10 on the new state, missing third journal/new STATUS/m801-era STATUS, extra file,
registry rolled back to m801 or forged, wrong SHA/head/counter/prefix, changed mode/UID/GID/mtime
of an m801-era file, tampered tar or pin, and the content-only checks run without the pin.
"""
from pathlib import Path
import base64,copy,hashlib,importlib.util,io,json,sys,tarfile,tempfile,unittest
B=Path(__file__).resolve().parent;R=B.parents[2]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=module('continuation_l12',B/'continuation_l12.py');c10=module('continuation_l10',B.parent/'contract-l10/continuation_l10.py')
PIN=B/'m802-continuation-pin.json';PIN10=B.parent/'contract-l10/m801-continuation-pin.json'
M802=R/'evidence/betarc01/m802/sessions/beta-rc01-forensic-capture02/native-restart-metadata.tar'
ATTEMPT1=R/'evidence/linuxport01/failed/m802-attempt01/sessions/beta-rc01-forensic-capture02/native-restart-metadata.tar'
M801=R/'evidence/betarc01/m801/sessions/beta-rc01-forensic-capture01/native-restart-metadata.tar'
BASELINE=R/'evidence/betarc01/g105/sessions/beta-rc01-native01/native-restart-metadata.tar'
SESSION1=R/'evidence/betarc01/g105/sessions/beta-rc01-native01/native-journal17-after-first-close.tar'
sha=c.sha;HAVE=M802.is_file()and PIN.is_file()and M801.is_file()

def items(src):
 with tarfile.open(src)as t:return[(m,t.extractfile(m).read()if m.isfile()else None)for m in t]
def write(rows,dst):
 with tarfile.open(dst,'w',format=tarfile.GNU_FORMAT)as o:
  for m,b in rows:
   m=copy.copy(m)
   if b is not None:m.size=len(b)
   o.addfile(m,io.BytesIO(b)if b is not None else None)
 return dst
def forge_registry(raw,keep):
 """First `keep` rows of the real registry, re-chained so each row is self-consistent."""
 return raw[:len(c.INDEX_MAGIC)]+b''.join(l+b'\n'for l in raw[len(c.INDEX_MAGIC):].split(b'\n')[:keep])
def row(seq,head,kind,fields):
 p='%d\t%s\t%s\t%s'%(seq,head,kind,base64.b64encode('\t'.join(fields).encode()).decode());return(p+'\t'+sha(p.encode())+'\n').encode()

@unittest.skipUnless(HAVE,'team m802/m801 evidence and pin')
class Contract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.dir=Path(cls.tmp.name);cls.pin_raw=PIN.read_bytes();cls.pin=json.loads(cls.pin_raw);cls.pin_sha=sha(cls.pin_raw)
  cls.items=items(M802);cls.entries,cls.data=c.read_tar(M802,sha(M802.read_bytes()))
  s=c.semantics(cls.entries,cls.data);cls.new=s['state']['new']
  cls.base75=set(cls.pin['statusBaseline75']);cls.old_status=sorted(cls.base75)[0]
  cls.m801_status=cls.pin['statuses'][cls.new[0]][0];cls.newest_status=cls.pin['statuses'][cls.new[2]][0]
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def run_tar(self,path,pin=None,pin_sha=None):
  return c.verify(path,sha(Path(path).read_bytes()),pin or PIN,pin_sha or self.pin_sha,repo=R)
 def mock(self,name,mutate):return write(mutate([(copy.copy(m),b)for m,b in self.items]),self.dir/(name+'.tar'))
 def refused(self,code,path,**k):
  with self.assertRaises(c.ContractError)as e:self.run_tar(path,**k)
  self.assertTrue(str(e.exception).startswith('CONTINUATION_L12_'+code),str(e.exception));return str(e.exception)
 def drop(self,name):return lambda rows:[(m,b)for m,b in rows if m.name!=name]
 def edit(self,name,f):
  def g(rows):
   out=[]
   for m,b in rows:
    if m.name==name:m,b=f(m,b)
    out.append((m,b))
   return out
  return g
 def other_pin(self,change):
  p=copy.deepcopy(self.pin);change(p);raw=c.canonical(p);path=self.dir/('pin-%s.json'%sha(raw)[:8]);path.write_bytes(raw);return path,sha(raw)

 # Positive.
 def test_team_m802_passes_every_check(self):
  p=self.run_tar(M802);self.assertEqual(p['status'],'TEAM_CONTINUATION_STATE_MATCHES_PIN_NOT_AUTHORITY_NOT_G1');self.assertTrue(p['rawIdenticalToPinnedCapture'])
  self.assertEqual(len(p['checks']),10);self.assertIn('INDEX_EXACT_96',p['checks']);self.assertIn('STATUS_NINE_BOUND_TO_NEW_JOURNALS',p['checks'])
  self.assertEqual(p['counters']['committedGenerations'],11);self.assertEqual(p['lifetimeGenerations'],11)
  self.assertEqual((p['independentReceiver']['activeJournals'],p['independentReceiver']['archivedJournals'],p['independentReceiver']['pendingTransactions']),(3,8,0))
  for k in('authorityRestorable','archiveOrResumeAuthorized','G1AcceptanceClaimed','flightAcceptance','independentQA'):self.assertIs(p[k],False)
 def test_first_capture_attempt_is_the_same_raw(self):self.assertTrue(self.run_tar(ATTEMPT1)['rawIdenticalToPinnedCapture'])
 def test_repacked_other_member_order_passes_but_is_not_the_same_raw(self):
  def reorder(rows):d=[x for x in rows if x[1]is None];f=[x for x in rows if x[1]is not None];return d+f[::-1]
  p=self.run_tar(self.mock('reordered',reorder));self.assertFalse(p['rawIdenticalToPinnedCapture'])
 def test_contract_does_not_load_the_75_file_decoder(self):
  self.run_tar(M802);self.assertFalse([m for m in sys.modules if 'reconcile' in m])

 # Real earlier states, and the old contract on the new state.
 def test_m801_83_file_state_refused(self):self.refused('MISSING',M801)
 def test_79_file_session1_snapshot_refused(self):self.refused('MISSING',SESSION1)
 def test_75_file_snapshot_refused(self):self.refused('MISSING',BASELINE)
 def test_contract_l10_refuses_the_m802_state(self):
  with self.assertRaises(c10.ContractError)as e:c10.verify(M802,sha(M802.read_bytes()),PIN10,sha(PIN10.read_bytes()),repo=R)
  self.assertTrue(str(e.exception).startswith('CONTINUATION_L10_EXTRA'),str(e.exception))

 # Missing / extra.
 def test_missing_third_journal(self):self.refused('MISSING',self.mock('no-journal',self.drop(c.ACTIVE+self.new[2]+'.aj02')))
 def test_missing_newest_status(self):self.refused('MISSING',self.mock('no-newest-status',self.drop(self.newest_status)))
 def test_missing_m801_era_status(self):self.refused('MISSING',self.mock('no-m801-status',self.drop(self.m801_status)))
 def test_missing_baseline_status(self):self.refused('MISSING',self.mock('no-old-status',self.drop(self.old_status)))
 def test_missing_archived_journal(self):
  name=sorted(n for n in self.entries if n.startswith(c.ARCHIVES)and n.endswith('.aj02'))[0];self.refused('MISSING',self.mock('no-archived',self.drop(name)))
 def test_missing_workspace_head(self):self.refused('MISSING',self.mock('no-workspace',self.drop(c.WORKSPACE+'HEAD')))
 def add(self,name,data,directory=False):
  def g(rows):
   m=copy.copy(next(x for x,b in rows if(x.isdir()if directory else x.isfile())));m.name=name
   return rows+[(m,None if directory else data)]
  return g
 def test_extra_status_file(self):self.refused('EXTRA',self.mock('extra-status',self.add(c.STATUS+'status-'+'0'*32+'.json',self.data[self.old_status])))
 def test_extra_active_journal(self):self.refused('EXTRA',self.mock('extra-journal',self.add(c.ACTIVE+'f'*32+'.aj02',c.AJ)))
 def test_extra_directory(self):self.refused('EXTRA',self.mock('extra-dir',self.add('files/product-input-staging',None,directory=True)))

 # Wrong bytes / registry.
 def test_one_byte_changed_same_size(self):
  def flip(m,b):i=b.index(b'"pid":')+6;return m,b[:i]+bytes([b[i]^1])+b[i+1:]
  self.refused('BYTES',self.mock('flip',self.edit(self.m801_status,flip)))
 def test_registry_rolled_back_to_m801(self):self.refused('BYTES:'+c.REGISTRY,self.mock('rollback',self.edit(c.REGISTRY,lambda m,b:(m,forge_registry(b,12)))))
 def test_registry_with_forged_extra_row(self):
  def extra(m,b):rows,head=c.replay(b);return m,b+row(len(rows)+1,head,'GEN_BEGIN',['e'*32])
  self.refused('BYTES:'+c.REGISTRY,self.mock('forged',self.edit(c.REGISTRY,extra)))

 # Mode / UID / GID / mtime.
 def meta(self,name,**k):
  def f(m,b):
   for a,v in k.items():setattr(m,a,v)
   return m,b
  return self.mock('meta-'+'-'.join(k),self.edit(name,f))
 def test_file_mode_changed(self):self.refused('META',self.meta(c.WORKSPACE+'HEAD',mode=0o644))
 def test_uid_changed(self):self.refused('META',self.meta(self.m801_status,uid=10142))
 def test_gid_changed(self):self.refused('META',self.meta(self.m801_status,gid=10142))
 def test_directory_mode_changed(self):self.refused('META',self.meta('files/product-input01',mode=0o755))
 def test_mtime_of_m801_era_file_changed(self):self.refused('MTIME',self.meta(self.m801_status,mtime=self.entries[self.m801_status]['mtime']+1))

 # Tampered inputs and pins.
 def test_tar_digest_mismatch(self):
  with self.assertRaises(c.ContractError)as e:c.verify(M802,'0'*64,PIN,self.pin_sha,repo=R)
  self.assertEqual(str(e.exception),'CONTINUATION_L12_RAW_SHA')
 def test_pin_bytes_tampered(self):
  path=self.dir/'pin-tampered.json';path.write_bytes(self.pin_raw.replace(b'"rows":15',b'"rows":16'));self.refused('PIN_SHA',M802,pin=path)
 def test_pin_not_canonical(self):
  path=self.dir/'pin-indent.json';raw=json.dumps(self.pin,indent=1).encode();path.write_bytes(raw);self.refused('PIN_FORMAT',M802,pin=path,pin_sha=sha(raw))
 def test_l10_pin_refused_as_format(self):self.refused('PIN_FORMAT',M802,pin=PIN10,pin_sha=sha(PIN10.read_bytes()))
 def test_wrong_head_in_pin(self):
  p,h=self.other_pin(lambda p:p['registry'].update(head='1'*64));self.refused('REGISTRY_HEAD_ROWS_COUNTERS',M802,pin=p,pin_sha=h)
 def test_wrong_counter_in_pin(self):
  p,h=self.other_pin(lambda p:p['registry']['counters'].update(committedGenerations=10));self.refused('REGISTRY_HEAD_ROWS_COUNTERS',M802,pin=p,pin_sha=h)
 def test_wrong_m801_prefix_in_pin(self):
  p,h=self.other_pin(lambda p:p['registry']['prefixes'][2].update(sha256='2'*64));self.refused('REGISTRY_PREFIX',M802,pin=p,pin_sha=h)
 def test_wrong_receiver_in_pin(self):
  p,h=self.other_pin(lambda p:p['receiver'].update(sha256='3'*64));self.refused('EVIDENCE_SHA',M802,pin=p,pin_sha=h)

 # Content-only checks, without the pin.
 def state_with(self,name=None,data=None,entries=None):
  d=dict(self.data);e=copy.deepcopy(self.entries)
  if name is not None:d[name]=data
  if entries:entries(e)
  sem=c.semantics(e,d);c.check_state(e,d,sem);return sem
 def content_refused(self,code,**k):
  with self.assertRaises(c.ContractError)as e:self.state_with(**k)
  self.assertTrue(str(e.exception).startswith('CONTINUATION_L12_'+code),str(e.exception))
 def test_content_m802_passes(self):self.state_with()
 def test_content_registry_missing_last_close(self):self.content_refused('REGISTRY_ROW_TYPES',name=c.REGISTRY,data=forge_registry(self.data[c.REGISTRY],14))
 def test_content_registry_pending_generation(self):self.content_refused('REGISTRY_PENDING',name=c.REGISTRY,data=forge_registry(self.data[c.REGISTRY],13))
 def test_content_registry_row_hash(self):
  raw=self.data[c.REGISTRY];i=raw.rindex(b'\t')+1;bad=raw[:i]+(b'0'if raw[i:i+1]!=b'0'else b'1')+raw[i+1:];self.content_refused('REGISTRY_ROW_HASH',name=c.REGISTRY,data=bad)
 def test_content_registry_broken_chain(self):
  raw=self.data[c.REGISTRY];rows,head=c.replay(raw);self.content_refused('REGISTRY_SEQUENCE_CHAIN',name=c.REGISTRY,data=raw+row(len(rows)+1,'4'*64,'GEN_BEGIN',['e'*32]))
 def test_content_third_journal_not_empty(self):self.content_refused('NEW_JOURNAL_EMPTY',name=c.ACTIVE+self.new[2]+'.aj02',data=c.AJ+b'\0\0\0\0')
 def test_content_uid_and_mode(self):
  self.content_refused('UID_GID',entries=lambda e:e[self.m801_status].update(uid=0))
  self.content_refused('MODE',entries=lambda e:e[self.m801_status].update(mode=0o640))
 def test_content_m801_state(self):
  e,d=c.read_tar(M801,sha(M801.read_bytes()))
  with self.assertRaises(c.ContractError)as x:c.check_state(e,d,c.semantics(e,d))
  self.assertIn('INDEX_87_FILES_9_DIRS',str(x.exception))
 def statuses(self):
  sem=c.semantics(self.entries,self.data);return c.new_statuses(sem,self.data,self.base75)
 def test_content_nine_statuses_three_per_journal(self):
  g=self.statuses();self.assertEqual([len(v)for v in g.values()],[3,3,3]);self.assertEqual([[f['lifetime']for _,f in v]for v in g.values()],[[9]*3,[10]*3,[11]*3])
 def test_content_status_close_only_last(self):
  g=self.statuses();last=list(g)[2];g[last][2][1]['journalClosed']=False
  with self.assertRaises(c.ContractError)as e:c.check_statuses(g,self.pin['productSourceSHA256'])
  self.assertIn('STATUS_CLOSE_ONLY_LAST',str(e.exception))
 def test_content_status_missing_one(self):
  g=self.statuses();last=list(g)[2];g[last]=g[last][:2]
  with self.assertRaises(c.ContractError)as e:c.check_statuses(g,self.pin['productSourceSHA256'])
  self.assertIn('STATUS_THREE_PER_JOURNAL',str(e.exception))
 def test_content_status_other_source(self):
  with self.assertRaises(c.ContractError)as e:c.check_statuses(self.statuses(),'5'*64)
  self.assertIn('STATUS_UNUSED_JOURNAL',str(e.exception))
 def test_owner_receiver_refuses_unknown_head(self):
  recv=(R/self.pin['receiver']['path']).read_bytes()
  with self.assertRaises(ValueError):c.independent(M802,sha(M802.read_bytes()),'6'*64,recv,'0'*64)

 # The pin's own record of where this state comes from.
 def test_pin_lineage(self):
  p=self.pin;self.assertEqual((len(p['entries']),len(p['conserved']['files']),len(p['conserved']['directories'])),(96,82,9))
  self.assertEqual([x['rows']for x in p['registry']['prefixes']],[6,9,12]);self.assertEqual(p['registry']['rows'],15)
  self.assertEqual(p['previousPinnedState']['pin']['sha256'],sha(PIN10.read_bytes()));self.assertEqual(p['previousPinnedState']['tar']['sha256'],sha(M801.read_bytes()))
  self.assertEqual([(a['attempt'],a['emulatorExit'],a['usableAsContractBase'])for a in p['source']['captureAttempts']],[(1,-11,False),(2,0,True)])
  self.assertEqual(len(p['addedSinceM801']),4);self.assertEqual(set(p['conserved']['files'])|{c.REGISTRY},{n for n,e in json.loads(PIN10.read_bytes())['entries'].items()if e['type']=='regular'})

if __name__=='__main__':unittest.main()
