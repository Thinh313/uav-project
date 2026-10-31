"""Explicit small-module derivation, no whole-project copy or frozen writes."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];H=R/'pilot/pace58';E=R/'evidence/pace58';origins=[]
def derive(src,dst,edits):
 p=R/src;text=p.read_text()
 for before,after in edits:
  if before not in text and (before,after) in common:continue
  assert before in text,(src,before);text=text.replace(before,after)
 dest=H/dst
 with dest.open('x') as f:f.write(text)
 origins.append({'source':src,'sourceSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'derived':str(dest.relative_to(R)),'derivedSha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'replacements':edits})
common=[('evidence/simtrain53','evidence/pace58'),('aeris-simtrain53','aeris-pace58'),("aeris.task=simtrain53","aeris.task=pace58"),('ACTUAL_SIMTRAIN53','ACTUAL_PACE58')]
def main():
 E.mkdir(exist_ok=True)
 derive('pilot/simtrain53/backend.py','backend.py',common+[
  ("configuration = json.loads((out/'request.json').read_text()); model", "configuration = json.loads((out/'request.json').read_text()); mode=configuration['mode']; assert mode in ['baseline','optimized']; tuning=configure(mode); model"),
  ("from epoch import Epoch", "from epoch import Epoch\n    from tuning import configure, encoder"),
  ("mock = out.parent", "if mode=='optimized': encode=lambda value:encoder.encode(value).encode()\n    mock = out.parent"),
  ("s.bind(('127.0.0.1', 9002)); s.settimeout(.1)","s.bind(('127.0.0.1', 9002)); s.settimeout(.1)\n            if mode=='optimized':\n                s.setblocking(True);s.setsockopt(socket.SOL_SOCKET,socket.SO_RCVTIMEO,struct.pack('@ll',0,100000))"),
  ("except socket.timeout: continue","except (socket.timeout,BlockingIOError): continue"),
  ("'port': 9002}","'port': 9002, 'mode':mode, 'tuning':tuning}"),
  ("payload = ('\\n'+json.dumps(model.step(pwm, 1/rate), separators=(',', ':'), allow_nan=False)+'\\n').encode()", "sensors=model.step(pwm,1/rate)\n                payload=('\\n'+(encoder.encode(sensors) if mode=='optimized' else json.dumps(sensors,separators=(',',':'),allow_nan=False))+'\\n').encode()\n                aux=model.snapshot() if mode=='optimized' else None"),
  ("'modelAux': model.snapshot()", "'modelAux': aux if mode=='optimized' else model.snapshot()"),
  ("snapshot={**model.snapshot()", "snapshot={**(aux if mode=='optimized' else model.snapshot())"),
  ("'frames': frames, 'activeReceiveWallSeconds'", "'mode':mode,'tuning':tuning,'frames': frames, 'activeReceiveWallSeconds'")])
 derive('pilot/simtrain53/runtime.py','runtime.py',common+[
  ("def launch(rid, load, wind):","def launch(rid, load, wind, mode, request_id):\n    assert mode in ['baseline','optimized'];assert request_id.isalnum() and len(request_id)<=40\n    reservation=json.loads((R/'evidence/pace58/reservations'/f'{request_id}.json').read_text())\n    assert reservation=={'requestId':request_id,'mode':mode,'load':load,'wind':wind}\n    assert not(R/'evidence/pace58/started'/f'{request_id}.json').exists()\n    save(R/'evidence/pace58/started'/f'{request_id}.json',{'requestId':request_id,'run':rid,'mode':mode})"),
  ("(5870,socket.SOCK_STREAM)","(5871,socket.SOCK_STREAM)"),
  ("'seed':32}","'seed':32,'mode':mode,'requestId':request_id}"),
  ("127.0.0.1:5870:5760","127.0.0.1:5871:5760"),
  ("127.0.0.1:5870'","127.0.0.1:5871'"),
  ("'backendPid':proc.pid", "'mode':mode,'requestId':request_id,'backendPid':proc.pid"),
  ("launch(*sys.argv[1:4])","launch(*sys.argv[1:6])")])
 derive('pilot/simtrain53/link.mjs','link.mjs',common+[
  ("port:5870","port:5871"),("!=='simtrain53'","!=='pace58'"),("!=='5870'","!=='5871'"),('/pilot/simtrain53/backend.py ','/pilot/pace58/backend.py '),
  ("from './authority.mjs'","from '../simtrain53/authority.mjs'"),("from './rc.mjs'","from '../simtrain53/rc.mjs'")])
 derive('pilot/simtrain53/server.mjs','ap-server.mjs',[
  ("from './finalize.mjs'","from './finalize.mjs'"),("from './history.mjs'","from '../simtrain53/history.mjs'"),("from './storage.mjs'","from '../simtrain53/storage.mjs'"),
  ("pilot/simtrain53","pilot/pace58"),("evidence/simtrain53","evidence/pace58"),('8807','8811'),
  ("async function start(load,wind)","async function start(load,wind,mode,requestId)"),
  ("const run='r'", "if(!['baseline','optimized'].includes(mode)||!/^p58[a-zA-Z0-9]{1,32}$/.test(requestId??''))throw Error('RESERVED_EXPERIMENT_REQUIRED');const run='r'"),
  ("run,load,wind],{cwd:R", "run,load,wind,mode,requestId],{cwd:R"),
  ("start(d.load,d.wind)","start(d.load,d.wind,d.mode,d.requestId)")])
 derive('pilot/simtrain53/readback.py','readback.py',common+[("config['load']","config['load']")])
 derive('pilot/simtrain53/finalize.mjs','finalize.mjs',[("pilot/simtrain53/readback.py","pilot/pace58/readback.py")])
 derive('pilot/aeris57/backend.mjs','backend.mjs',[("127.0.0.1:8807","127.0.0.1:8811")])
 derive('pilot/aeris57/server.mjs','server.mjs',[
  ("from './store.mjs'","from '../aeris57/store.mjs'"),("from './domain.mjs'","from '../aeris57/domain.mjs'"),("from './catalog.mjs'","from '../aeris57/catalog.mjs'"),
  ("'pilot/aeris57'","'pilot/pace58'"),("'evidence/aeris57'","'evidence/pace58'"),("port=8809","port=8810"),("server.listen(8809","server.listen(8810"),("http://127.0.0.1:8809","http://127.0.0.1:8810"),
  ("evidence/simtrain53/runs","evidence/pace58/runs"),
  ("{load:d.load,wind:d.wind}","{load:d.load,wind:d.wind,mode:d.mode,requestId:d.requestId}"),
  ("path.join(HOME,'index.html')","path.join(ROOT,'pilot/aeris57/index.html')"),
  ("'/style.css':'style.css'","'/style.css':'../aeris57/style.css'")])
 derive('pilot/aeris57/ui.mjs','ui.mjs',[
  ("$('loading').hidden=true;", "$('loading').hidden=true;const startButton=document.getElementById('start');if(startButton){startButton.disabled=true;startButton.title='PACE58: chỉ mở phiên đã đăng ký từ bộ đo';}document.title='AERIS · PACE58 đối chứng 1×';"),
  ("backend8807","backend8811")])
 with(E/'derivation.json').open('x') as f:json.dump({'method':'Small explicit textual derivatives; originals read-only','modules':origins},f,indent=2);f.write('\n')
if __name__=='__main__':main()
