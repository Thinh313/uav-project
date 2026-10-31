"""Only receipt observation may wait for freshness; no tap/command retries."""
from pathlib import Path
import importlib.util,json
s=importlib.util.spec_from_file_location('ui05',Path(__file__).with_name('qa-ui.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);cases=[]
t=[0];calls=[0]
def wait(v):t[0]+=v
def reader():
 calls[0]+=1
 if calls[0]<=2:raise AssertionError('STALE_OBSERVATION')
 return {'receipt':'ACK'}
assert m.receipt_observation(.3,reader,lambda:t[0],wait)=={'receipt':'ACK'};assert calls[0]==3 and t[0]<=.3;cases.append('two_stale_then_exact_fresh_receipt_without_reinput')
t[0]=0
def stale():raise AssertionError('STALE_OBSERVATION')
try:m.receipt_observation(.2,stale,lambda:t[0],wait);raise RuntimeError('MUST_FAIL')
except AssertionError as e:assert str(e)=='STALE_UNTIL_EXISTING_RECEIPT_DEADLINE_NO_REINPUT';assert t[0]<=.2;cases.append('stale_until_original_deadline_stops_no_extend')
def other():raise AssertionError('UI_OBSERVATION_REQUIRED')
try:m.receipt_observation(.5,other,lambda:0,wait);raise RuntimeError('MUST_FAIL')
except AssertionError as e:assert str(e)=='UI_OBSERVATION_REQUIRED';cases.append('other_failures_not_retried')
t[0]=0
def deferred_reader():t[0]=.5;return {'receipt':'ACK'}
try:m.receipt_observation(.2,deferred_reader,lambda:t[0],wait);raise RuntimeError('MUST_FAIL')
except AssertionError as e:assert str(e)=='RECEIPT_AFTER_EXISTING_DEADLINE_NO_REINPUT'and e.late_observation=={'receipt':'ACK'};cases.append('fresh_ACK_returning_after_original_deadline_rejected_preserved')
o={k:k+'01'for k in['documentId','clientId','clientEpoch','clientInstance','modelSha256','planSha256','configId','boot','run']};m.receipt_context(o,o,o,'field-tab-flight');cases.append('exact_receipt_context')
for k in['boot','clientId','clientEpoch','clientInstance','modelSha256','planSha256','configId']:
 try:m.receipt_context(o,{**o,k:'wrong'},o,'field-tab-flight');raise RuntimeError('MUST_FAIL')
 except AssertionError:cases.append('post_tap_wrong_'+k+'_refused')
try:m.receipt_context(o,o,{**o,'boot':'wrong'},'field-gimbal');raise RuntimeError('MUST_FAIL')
except AssertionError:cases.append('wrong_receipt_boot_refused')
css=Path('pilot/clockvideo05/ui.css').read_text();assert 'height:44px;min-height:44px;max-height:44px;flex:0 0 44px'in css and 'grid-template-rows:14px 22px'in css and css.rfind('#field-flight-context{min-height:80px}')>css.rfind('#field-flight-context{min-height:96px}');cases.append('explicit_header_strut_and_80px_context')
height=716-106-108;inner=height-2-16;fixed=44+44+32+15+4*4;flight=inner-fixed;dock=32+3*44+44+4*6+9;context=flight-dock;assert context==92 and context>=80 and context-6>=73;cases.append('exact_css_budget_context92_content86_connection73')
print(json.dumps({'status':'PASS_MOCK_NOT_NATIVE_PIXEL_ACCEPTANCE','checks':len(cases),'cases':cases,'budget':{'panel':height,'inner':inner,'flight':flight,'dock':dock,'context':context,'contextContent':context-6},'adbCalls':0,'inputRetries':0},indent=2))
