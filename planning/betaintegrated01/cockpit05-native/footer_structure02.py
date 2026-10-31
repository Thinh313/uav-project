from pathlib import Path
from html.parser import HTMLParser
import hashlib,json
R=Path(__file__).resolve().parents[3];N=R/'native/betaintegrated01/cockpit05';E=R/'evidence/betaintegrated01-cockpit05-native/asset-revision02';tests=[]
class Tree(HTMLParser):
 def __init__(self):super().__init__();self.stack=[];self.nodes=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);node={'tag':tag,'attrs':a,'parent':self.stack[-1]if self.stack else None,'children':[]};self.nodes.append(node)
  if self.stack:self.stack[-1]['children'].append(node)
  if tag not in ('meta','link','input','br','hr','img','use','path','circle','rect','line','polyline','polygon','ellipse'):self.stack.append(node)
 def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs);self.handle_endtag(tag)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,-1,-1):
   if self.stack[i]['tag']==tag:self.stack=self.stack[:i];break
p=Tree();p.feed((N/'assets/index.html').read_text());errors=[n for n in p.nodes if n['attrs'].get('id')=='draft-error'];assert len(errors)==1;error=errors[0];assert error['attrs'].get('role')=='status';tests.append('same_unique_id_role');assert error['parent']['tag']=='footer';tests.append('direct_footer_child');assert error['parent']['children'][0]is error and error['parent']['children'][1]['attrs'].get('id')=='draft-save';tests.append('immediately_above_Save');parent=error['parent']
while parent:assert'panel-scroll'not in parent['attrs'].get('class','').split();parent=parent['parent']
tests.append('outside_scroll_ancestors');css=(N/'assets/cockpit.css').read_text();assert'.inline-error:empty{display:none}'in css;tests.append('empty_hidden');assert'.work-panel>footer .inline-error{margin:0 0 10px}'in css;tests.append('footer_margin10');assert'border-left:2px solid var(--gold)'not in css;tests.append('no_gold_notice_stripe');prior=json.loads((R/'evidence/betaintegrated01-cockpit05-native/build-01.json').read_text());allowed={'native/betaintegrated01/cockpit05/assets/index.html','native/betaintegrated01/cockpit05/assets/cockpit.css'};assert all(hashlib.sha256((R/k).read_bytes()).hexdigest()==v for k,v in prior['sourcePins'].items()if k not in allowed);tests.append('all_request_model_native_core_and_other_inputs_unchanged');(E/'structure-tests.json').open('x').write(json.dumps({'status':'PASS_SOURCE_STRUCTURE_NOT_RENDERED','groups':len(tests),'cases':tests},indent=2)+'\n');print(json.dumps({'status':'PASS','groups':len(tests)}))
