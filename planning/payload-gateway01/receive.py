"""Independent implementation receiver reused from BIG02; never imports gateway/sender."""
import argparse,hashlib,importlib.util,io,json,tarfile,sys
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('receiver',R/'planning/big02/qa-receiver.py');rx=importlib.util.module_from_spec(spec);spec.loader.exec_module(rx)

def unpack(blob):
 if len(blob)>5*2**20:raise ValueError('ARCHIVE_SIZE')
 with tarfile.open(fileobj=io.BytesIO(blob),mode='r:')as t:
  members=t.getmembers()
  if len(members)!=3 or set(m.name for m in members)!={'manifest.json','original.jpg','sidecar.json'}or any(not m.isfile()or m.size>4*2**20 or m.size<1 for m in members):raise ValueError('EXACT_SAFE_TAR_MEMBERS')
  return{m.name:t.extractfile(m).read()for m in members}

def main():
 p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--capture',required=True);p.add_argument('--package',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 if a.out.exists():raise ValueError('NEW_RECEIPT_REQUIRED')
 data=a.archive.read_bytes();files=unpack(data);m=rx.parse(files['manifest.json'])
 if m['captureId']!=a.capture or m['packageId']!=a.package or m['context']['cameraId']not in ['SYNTHETIC-RGB-01','SYNTHETIC-IR-01']or m['context']['aircraftId']!='SYNTHETIC-AIRCRAFT-01':raise ValueError('EXPECTED_UI_IDENTITY')
 transfers=set();captures=set();result=rx.verify_bytes(files,'rtr-host01-evaluator','aeris-gateway01-mock',transfers,captures)
 negative=[]
 for name,transform,receiver in [('wrong-receiver',lambda f:f,'wrong-receiver'),('corrupt-original',lambda f:{**f,'original.jpg':f['original.jpg']+b'X'},'rtr-host01-evaluator'),('missing-member',lambda f:{k:v for k,v in f.items()if k!='sidecar.json'},'rtr-host01-evaluator')]:
  try:rx.verify_bytes(transform(files),receiver,'aeris-gateway01-mock',set(),set())
  except Exception as e:negative.append({'case':name,'status':'REJECTED','reason':str(e)})
  else:raise AssertionError(name)
 try:rx.verify_bytes(files,'rtr-host01-evaluator','aeris-gateway01-mock',transfers,captures)
 except Exception as e:negative.append({'case':'replay','status':'REJECTED','reason':str(e)})
 else:raise AssertionError('replay')
 out={'source':'BROWSER_DOWNLOADED_TAR','archive':str(a.archive),'archiveSha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'receiverImplementationSha256':hashlib.sha256((R/'planning/big02/qa-receiver.py').read_bytes()).hexdigest(),'review':'IMPLEMENTATION_INDEPENDENT_NOT_INDEPENDENT_HUMAN_REVIEW','result':result,'negativeControls':negative}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 with a.out.open('x')as f:json.dump(out,f,ensure_ascii=False,indent=2)
 print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
