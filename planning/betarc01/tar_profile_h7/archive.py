"""H7 selected framing; unchanged original index/used-source semantics."""
from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[3];sys.path[:0]=[str(R),str(R/'planning/nativejournal17')]
from planning.betarc01.tar_profile_h7.reader import native_tar,PROFILE,hash_file
from planning.betarc01.archive.archive_rc01 import verify_archive_index_rc01
from planning.betarc01.archive.common_rc01 import decode,canonical,need
from planning.nativejournal17.archive_verifier17 import verify_archive_index

def verify_storage(backup_path,backup_sha,expected_head,*,source_candidate,archive_receivers,approved_sources,node,require_selected_closed=()):
 scan=native_tar(backup_path,backup_sha,allow_empty_active=True);v=verify_archive_index_rc01(scan,expected_head,source_candidate=source_candidate,archive_receivers=archive_receivers,approved_sources=approved_sources,node=node,require_selected_closed=require_selected_closed);v.update(sourceTarVerifierSHA256=hash_file(Path(__file__).with_name('reader.py')),tarTransportProfile=scan['transportProfile']);return v
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--backup',required=True);p.add_argument('--backup-sha',required=True);p.add_argument('--expected-head',required=True);p.add_argument('--candidate-sha',required=True);p.add_argument('--node');p.add_argument('--receiver',action='append',default=[]);p.add_argument('--receiver-ref',action='append',default=[]);p.add_argument('--approved-source',action='append',default=[]);p.add_argument('--selected-closed',action='append',default=[]);a=p.parse_args()
 if a.receiver:
  need(not a.receiver_ref and not a.approved_source,'INITIAL_EXACT_RECEIVER_MODE');reports={}
  for name in a.receiver:
   raw=Path(name).read_bytes();need(len(raw)<=32768,'RECEIVER32K');reports[hashlib.sha256(raw).hexdigest()]=raw
  scan=native_tar(a.backup,a.backup_sha,allow_empty_active=True);v=verify_archive_index(scan,a.expected_head,source_candidate=a.candidate_sha,archive_receivers=reports,require_selected_closed=a.selected_closed);v.update(sourceVerifierSHA256=hash_file(R/'planning/nativejournal17/archive_verifier17.py'),sourceTarVerifierSHA256=hash_file(Path(__file__).with_name('reader.py')),tarTransportProfile=scan['transportProfile'])
 else:v=verify_storage(a.backup,a.backup_sha,a.expected_head,source_candidate=a.candidate_sha,archive_receivers=[decode(x)for x in a.receiver_ref],approved_sources=[decode(x)for x in a.approved_source],node=a.node,require_selected_closed=a.selected_closed)
 raw=canonical(v)+b'\n';need(len(raw)<=65536,'ARCHIVE_PROOF64K');sys.stdout.buffer.write(raw)
