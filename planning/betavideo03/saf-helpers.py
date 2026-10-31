"""SAF UI only on task-owned emulator5582. Read observed picker before each tap."""
import importlib.util,time,json,hashlib
from pathlib import Path
sp=importlib.util.spec_from_file_location('native',Path(__file__).with_name('native-ui.py'));n=importlib.util.module_from_spec(sp);sp.loader.exec_module(n);q=n.q
sha=lambda b:hashlib.sha256(b).hexdigest()
def picker():
 try:return n.dump()
 except Exception:
  time.sleep(2);return n.dump() # bounded read-only retry, no repeated write

def export_document(button,filename):
 assert filename.endswith('.json') and all(c.isalnum()or c in '-.' for c in filename),'SAFE_FILENAME'
 q.tap(button)
 return finish_open_export(filename)

def finish_open_export(filename):
 assert filename.endswith('.json') and all(c.isalnum()or c in '-.' for c in filename),'SAFE_FILENAME'
 r=picker();edit=[x for x in r.iter('node')if x.attrib.get('class')=='android.widget.EditText'];assert len(edit)==1,n.summary(r)
 n.tap(r,**{'class':'android.widget.EditText','bounds':edit[0].attrib['bounds']});q.adb('shell','input','keycombination','KEYCODE_CTRL_LEFT','KEYCODE_A');q.adb('shell','input','text',filename);q.adb('shell','input','keyevent','KEYCODE_BACK');r=picker();n.tap(r,**{'resource-id':'android:id/button1'});time.sleep(1)
 data=q.adb('exec-out','cat','/sdcard/Download/'+filename);assert data,'SAF_EMPTY'
 return data

def select_review(run):
 q.tap('beta-review-select');r=picker();nodes=[x for x in r.iter('node')if x.attrib.get('text','').startswith(run)];assert len(nodes)==1,n.summary(r)
 n.tap(r,**{'text':nodes[0].attrib['text'],'bounds':nodes[0].attrib['bounds']});time.sleep(.8)

def save_receipt(name,value):
 with(q.E/name).open('x')as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();__import__('os').fsync(f.fileno())
