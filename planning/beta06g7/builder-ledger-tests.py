"""Tiny reservations only. No large payload is written or preallocated."""
import importlib.util,tempfile,json,hashlib,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('g7quota_test',R/'pilot/beta06g7/quota.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);E=m.E;rows=[]
with tempfile.TemporaryDirectory(prefix='codex-tmp-g7-ledger-20261022-',dir=E)as tmp:
 m.E=Path(tmp);p=m.load_policy();M=2**20
 m.reserve_write(category='native',entries=1,bytes=96*M-4096,claim_id='metadata:normal')
 m.reserve_write(category='native',entries=1,bytes=16*M-4096,claim_id='closure:owned-stop',closure=True);rows.append('normal96_reserved16_close_usable_without_payload_allocation')
 for kwargs in [dict(category='native',entries=1,bytes=8192,claim_id='normal:over'),dict(category='native',entries=1,bytes=8192,claim_id='closure:over',closure=True),dict(category='native',entries=True,bytes=0,claim_id='bool'),dict(category='native',entries=0,bytes=0,claim_id='metadata:normal'),dict(category='native',entries=0,bytes=0,claim_id='arbitrary',closure=True)]:
  try:m.reserve_write(**kwargs);raise RuntimeError('EXPECTED_REFUSAL')
  except AssertionError:pass
 rows.append('overflow_boolean_duplicate_and_arbitrary_closure_refused')
 ledger=m.E/'quota-native-ledger.jsonl';lines=ledger.read_text().splitlines();bad=json.loads(lines[0]);bad['bytes']=-1;ledger.write_text(json.dumps(bad)+'\n'+'\n'.join(lines[1:])+'\n')
 try:m.reserve_write(category='native',entries=0,bytes=0,claim_id='after-tamper');raise RuntimeError('EXPECTED_REFUSAL')
 except AssertionError:pass
 rows.append('negative_or_changed_hashchain_failclosed')
 ledger.unlink();target=m.E/'foreign';target.write_text('retained');ledger.symlink_to(target)
 try:m.reserve_write(category='native',entries=0,bytes=0,claim_id='symlink');raise RuntimeError('EXPECTED_REFUSAL')
 except OSError:pass
 assert target.read_text()=='retained';rows.append('ledger_symlink_refused_without_foreign_append')
 m.E=E
r={'status':'PASS_BOUNDED_LEDGER_FIXTURES_NO_PAYLOAD_WRITES','groups':len(rows),'rows':rows,'scratchRemoved':tmp,'policySha256':hashlib.sha256(m.P.read_bytes()).hexdigest()};(E/'builder-ledger-tests01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
