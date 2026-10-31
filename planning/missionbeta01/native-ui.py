"""UIAutomator helpers for user-authorized, owned emulator-5582 only."""
import importlib.util,re,xml.etree.ElementTree as ET,time
from pathlib import Path
s=importlib.util.spec_from_file_location('q',Path(__file__).with_name('android-journey.py'));q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
def dump():
 q.adb('shell','uiautomator','dump','/sdcard/missionbeta01-window.xml');raw=q.adb('exec-out','cat','/sdcard/missionbeta01-window.xml');root=ET.fromstring(raw);return root
def summary(root):
 return [{k:n.attrib.get(k)for k in ['text','resource-id','class','content-desc','bounds','enabled']}for n in root.iter('node')if n.attrib.get('text')or n.attrib.get('resource-id')or n.attrib.get('content-desc')]
def tap(root,**attrs):
 nodes=[n for n in root.iter('node')if all(n.attrib.get(k)==v for k,v in attrs.items())];assert len(nodes)==1,(attrs,len(nodes));n=nodes[0];assert n.attrib['enabled']=='true';x1,y1,x2,y2=map(int,re.findall(r'\d+',n.attrib['bounds']));q.log('NATIVE_UI_INTENT',{'attrs':attrs,'observedNode':n.attrib});q.adb('shell','input','tap',(x1+x2)//2,(y1+y2)//2);time.sleep(.8)
if __name__=='__main__':print(summary(dump()))
