"""Visible UI operator boundary; actual input events, no authority bypass/API flight command."""
import re,time,xml.etree.ElementTree as ET
from .proofs import need
class OperatorUI:
 def __init__(self,session):self.session=session;self.device=session.device;self.bridge=session.supervisor.native;self.last=None
 def snapshot(self):
  self.session.monitor.check();self.last=self.bridge.status(context=self.session.supervisor.context.value());return self.last
 def layout(self):return self.snapshot()['layout']
 def _nodes(self):
  deadline=min(self.session.supervisor._deadline(),time.monotonic_ns()+10_000_000_000);raw=self.device.command(['shell','uiautomator','dump','/dev/tty'],deadline_ns=deadline).decode();start=raw.find('<?xml');end=raw.rfind('</hierarchy>');need(start>=0 and end>=start,'ACTUAL_UIAUTOMATOR_TREE');return list(ET.fromstring(raw[start:end+12]).iter('node')),deadline
 def tap(self,identifier):
  snapshot=self.snapshot();layout=snapshot['layout'];node=layout.get('buttons',{}).get(identifier,{})
  need(node.get('visible') is True and node.get('enabled') is True and node.get('currentaction')==identifier,'SOURCE_BOUND_VISIBLE_ENABLED_NATIVE_BUTTON')
  bounds=node.get('bounds');need(type(bounds)is list and len(bounds)==4 and all(type(x)is int and 0<=x<8192 for x in bounds),'ACTUAL_NATIVE_LAYOUT_BOUNDS');x1,y1,x2,y2=bounds;need(x1<x2 and y1<y2,'NONZERO_VISIBLE_NODE')
  before=time.monotonic_ns();need(0<=before-self.bridge.trace[-1]['hostReceivedNs']<=200_000_000,'OPERATOR_CURRENT_LAYOUT_DISPATCH');deadline=min(self.session.supervisor._deadline(),before+2_000_000_000)
  self.device.command(['shell','input','tap',str((x1+x2)//2),str((y1+y2)//2)],deadline_ns=deadline);return {'identifier':identifier,'beforeActionHostNs':before,'afterActionHostNs':time.monotonic_ns(),'actualBounds':bounds,'sourceRevision':snapshot['revision'],'processEpoch':snapshot['processEpoch'],'viewEpoch':snapshot['viewEpoch'],'UIAutomatorDuringActiveTap':False}
 def navigate(self,view):
  need(view in ('survey','preflight','fly','review'),'PRODUCT_VIEW');name={'survey':'Khảo sát','preflight':'Trước bay','fly':'Bay','review':'Hồ sơ'}[view];nodes,deadline=self._nodes();matches=[n for n in nodes if n.get('package')=='vn.rtr.aeris.mission' and n.get('enabled')=='true' and (n.get('content-desc')==name or n.get('text')==name)];need(len(matches)==1,'ONE_ACTUAL_NAVIGATION_NODE');b=re.fullmatch(r'\[([0-9]+),([0-9]+)\]\[([0-9]+),([0-9]+)\]',matches[0].get('bounds',''));need(b is not None,'NAVIGATION_BOUNDS');x1,y1,x2,y2=map(int,b.groups());self.device.command(['shell','input','tap',str((x1+x2)//2),str((y1+y2)//2)],deadline_ns=deadline)
  while time.monotonic_ns()<=deadline:
   s=self.snapshot()
   if s['state'].get('chosenView')==view and s['state'].get('presentedView')==view and s['state'].get('viewReady') is True:return s
  raise TimeoutError('CURRENT_VISIBLE_PRODUCT_VIEW')
 def stick_event(self,action,side,horizontal,vertical):
  need(action in ('DOWN','MOVE','UP') and side in ('left','right') and all(type(v)in(int,float) and -1<=v<=1 for v in (horizontal,vertical)),'NORMALIZED_OPERATOR_STICK_EVENT')
  if action=='DOWN':self.last=self.snapshot()
  need(self.last is not None and self.last['state'].get('chosenView')=='fly' and self.last['state'].get('ownerActive') is True,'CURRENT_FLY_STICK_LAYOUT')
  node=self.last['layout'].get('sticks',{}).get('control01-'+side+'-stick',{});b=node.get('bounds');need(node.get('visible') is True and type(b)is list and len(b)==4 and all(type(v)is int for v in b) and b[0]<b[2] and b[1]<b[3],'SOURCE_BOUND_STICK_BOUNDS')
  x=round((b[0]+b[2])/2+horizontal*(b[2]-b[0])*.4);y=round((b[1]+b[3])/2+vertical*(b[3]-b[1])*.4);self.session.monitor.check();before=time.monotonic_ns();self.device.command(['shell','input','touchscreen','motionevent',action,str(x),str(y)],deadline_ns=min(self.session.supervisor._deadline(),before+2_000_000_000));return {'action':action,'side':side,'x':x,'y':y,'beforeHostNs':before,'afterHostNs':time.monotonic_ns(),'HIDAttested':False,'nativeOwnsSamplerAndAuthority':True}
 def confirm_home(self):
  s=self.snapshot();f=s['state'].get('native',{}).get('flight',{});before=self.session.supervisor.begin_home_confirmation(f.get('homeHash'));action=self.tap('control01-confirm-home');receipt=self.session.supervisor.observed_home_confirmation(before);return {'action':action,'confirmation':receipt}
 def land(self):
  self.session.supervisor.landing_requested(time.monotonic_ns());return self.tap('control01-land')
