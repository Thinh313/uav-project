"""Independent native journal/prefix replay, no global clock ordering across guest boots."""
from pathlib import Path
import importlib.util
_writer_spec=importlib.util.spec_from_file_location('g15_bounded_proof_writer',Path(__file__).with_name('qa-proof-writer.py'));proof_writer=importlib.util.module_from_spec(_writer_spec);_writer_spec.loader.exec_module(proof_writer)
import json,hashlib,datetime,math,sys

def digest(b):return hashlib.sha256(b).hexdigest()
def journal_rows(raw):
 assert raw.endswith(b'\n'),'NATIVE_TORN_JOURNAL';head='ROOT';rows=[]
 for line in raw.splitlines():
  env=json.loads(line);assert isinstance(env['body'],str);body=env['body'].encode('utf-8');assert digest(body)==env['sha256'],'NATIVE_BODY_SHA_MISMATCH';row=json.loads(env['body']);assert row['seq']==len(rows)+1,'NATIVE_SEQ';assert row['previous']==head,'NATIVE_PREVIOUS';head=env['sha256'];rows.append(row)
 return rows,head

def native_prefix_replay(before_raw,after_raw,before_boot=None,after_boot=None):
 b,bh=journal_rows(before_raw);a,ah=journal_rows(after_raw);assert after_raw.startswith(before_raw),'NATIVE_PREFIX_CHANGED';assert len(a)>=len(b);new=a[len(b):]
 same=bool(before_boot and before_boot==after_boot)
 elapsed=[]
 if same:
  # Never compare the first new row against the prefix's historical last elapsedMs:
  # a before snapshot on a fresh guest may still contain only older-boot records.
  for row in new:
   t=row['elapsedMs'];assert isinstance(t,(int,float))and not isinstance(t,bool)and math.isfinite(t)and t>=0,'NATIVE_NEW_ELAPSED_INVALID';elapsed.append(t)
  assert all(x<=y for x,y in zip(elapsed,elapsed[1:])),'SAME_BOOT_NEW_APPEND_ELAPSED_REGRESSION'
 for row in new:
  if 'authorityRestored' in row.get('data',{}):assert row['data']['authorityRestored']is False,'NATIVE_AUTHORITY_RESTORE_DECLARED'
 return {'beforeRecords':len(b),'afterRecords':len(a),'beforeHead':bh,'afterHead':ah,'exactPrefix':True,'appendBytes':len(after_raw)-len(before_raw),'appendRecords':len(new),'beforeBootId':before_boot,'afterBootId':after_boot,'elapsedPolicy':'CHECKED_WITHIN_EXTERNALLY_BOUND_SAME_BOOT_APPEND_ONLY'if same else'NOT_CHECKED_BOOT_SEGMENT_UNKNOWN_OR_CHANGED','historicalGlobalElapsedOrder':'NOT_ASSERTED','firstNewElapsedMs':elapsed[0]if elapsed else None,'lastNewElapsedMs':elapsed[-1]if elapsed else None}

if __name__=='__main__':
 before,after,out=map(Path,sys.argv[1:]);assert all(str(p).startswith('evidence/beta06/')for p in [before,after,out]);assert str(out).startswith('evidence/beta06/generation15/qa');assert not out.exists();b=json.loads(before.read_text());a=json.loads(after.read_text());bp=Path(b['journalFile']);ap=Path(a['journalFile']);assert str(bp).startswith('evidence/beta06/')and str(ap).startswith('evidence/beta06/');br=bp.read_bytes();ar=ap.read_bytes();assert digest(br)==b['journalSha256']and digest(ar)==a['journalSha256'];proof=native_prefix_replay(br,ar,b.get('guestBootId'),a.get('guestBootId'));changed=[]
 for n,h in b['files'].items():
  assert n in a['files'],'OLD_NATIVE_FILE_MISSING'
  if not n.endswith('/journal.jsonl'):assert a['files'][n]==h,'OLD_NATIVE_ARTIFACT_CHANGED'
 r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_SELECTED_NATIVE_PREFIX_ARTIFACT_SHA_CHAIN','snapshots':{str(p):digest(p.read_bytes())for p in [before,after]},'journalInputs':{str(bp):digest(br),str(ap):digest(ar)},'snapshotBootField':'guestBootId','inputClassifications':[b.get('classification','ROOT_COLLECTED_SNAPSHOT'),a.get('classification','ROOT_COLLECTED_SNAPSHOT')],'proof':proof,'oldArtifactsUnchanged':len(b['files'])-1,'newFiles':sorted(set(a['files'])-set(b['files'])),'scope':'Read-only snapshot evidence replay. Native records have no embedded bootID; guest boot provenance comes only from separately root-collected snapshots. No global elapsed order, automatic authority restoration, mission replay, actual cold restart or SAF UI acceptance inferred from chain alone.'};proof_writer.write_proof(out,r,kind='campaign');print(json.dumps(r))
