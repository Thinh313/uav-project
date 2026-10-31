"""Finite future reservations, tiny ledger rows only; no actual payload/AP/UI."""
import importlib.util,tempfile,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];s=importlib.util.spec_from_file_location('g7future_test',R/'pilot/beta06g7/quota.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);E=m.E;rows=[]
with tempfile.TemporaryDirectory(prefix='codex-tmp-g7-future-20261022-',dir=E)as tmp:
 m.E=Path(tmp);m.check_native_future(4,2);assert not list(m.E.iterdir());rows.append('empty_readonly_future_no_ledger_creation')
 m.reserve_write(category='native',entries=48,bytes=0,claim_id='metadata:fixture-file-count');assert m.check_native_future(4,2)['normalFiles']['future']==464
 m.reserve_write(category='native',entries=1,bytes=0,claim_id='metadata:one-short')
 try:m.check_native_future(4,2);raise RuntimeError('EXPECTED_REFUSAL')
 except AssertionError as e:assert 'NATIVE_FUTURE512FILE_HEADROOM'in str(e)
 assert m.check_native_future(3,1)['normalFiles']['future']==336;rows.append('512_normal_file_future_exact_boundary_and_one_short')
 for p in m.E.iterdir():p.unlink()
 m.reserve_write(category='screenshots',entries=1,bytes=5*2**20,claim_id='png-direct:fixture')
 try:m.check_native_future(4,2);raise RuntimeError('EXPECTED_REFUSAL')
 except AssertionError as e:assert 'PNG_FUTURE_SUBTYPE_HEADROOM:direct'in str(e)
 m.check_native_future(4,1);rows.append('direct_subtype_32_initial_future_and_later_host_counter')
 ledger=m.E/'quota-native-ledger.jsonl';before=ledger.read_bytes();row=json.loads(before);row['entries']=True;row['hash']=hashlib.sha256(json.dumps({k:v for k,v in row.items()if k!='hash'},separators=(',',':'),sort_keys=True).encode()).hexdigest();ledger.write_text(json.dumps(row)+'\n')
 try:m.check_native_future(4,1);raise RuntimeError('EXPECTED_REFUSAL')
 except AssertionError:pass
 rows.append('readonly_future_uses_same_strict_no_boolean_hashchain_decoder');ledger.write_bytes(before)
 for p in m.E.iterdir():p.unlink()
 m.reserve_write(category='native',entries=1,bytes=96*2**20-4096,claim_id='metadata:normal');m.reserve_write(category='native',entries=1,bytes=16*2**20-4096,claim_id='closure:owned-stop',closure=True);rows.append('normal96_close16_reserved_bytes_still_usable')
 m.E=E
p=E/'builder-future-ledger-tests02.json'
with p.open('x')as f:json.dump({'status':'PASS_PURE_LEDGER_NOT_ACTUAL','groups':len(rows),'rows':rows,'policySha256':hashlib.sha256(m.P.read_bytes()).hexdigest(),'scratchRemoved':tmp},f,indent=2)
print(json.dumps({'status':'PASS','groups':len(rows)}))
