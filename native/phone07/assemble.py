from pathlib import Path
import json,hashlib,importlib.util,sys,shutil
R=Path(__file__).resolve().parents[2];N=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def one(s,a,b):
 if s.count(a)!=1:raise RuntimeError('PHONE07_DERIVATION_CONTEXT:'+a[:100])
 return s.replace(a,b)
def source():
 pins=json.loads((N/'dependencies.json').read_text())['files']
 for p,h in pins.items():
  if sha((R/p).read_bytes())!=h:raise RuntimeError('FROZEN_DRIFT:'+p)
 own={str(p.relative_to(R)):sha(p.read_bytes())for p in N.rglob('*')if p.is_file()and not any(x.startswith('.')or x in ['dist','__pycache__']for x in p.relative_to(N).parts)}
 return {**pins,**own}
def stage(t):
 source();sys.path.insert(0,str(R/'native/phone06'))
 spec=importlib.util.spec_from_file_location('overlay',R/'native/phone06/overlay.py');old=importlib.util.module_from_spec(spec);sys.modules['overlay']=old;spec.loader.exec_module(old);old.stage(t);sys.path.pop(0)
 for p in (t/'src').glob('*.java'):p.write_text(p.read_text().replace('vn.rtr.aeris.phone06','vn.rtr.aeris.phone07').replace('phone06.aeris.invalid','phone07.aeris.invalid'))
 for p in (t/'assets').rglob('*'):
  if p.is_file()and p.suffix in ['.html','.mjs','.css']:p.write_text(p.read_text().replace('phone06.aeris.invalid','phone07.aeris.invalid'))
 def write(p,s):
  f=t/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s)
 for p in (N/'src').glob('*.java'):write('src/'+p.name,p.read_text())
 for p in (N/'assets').rglob('*'):
  if p.is_file():write('assets/'+str(p.relative_to(N/'assets')),p.read_text())
 for name in ['geotag.mjs','relay-core.mjs','media.css']:
  write('assets/gateway/'+name,(R/'media/big02'/name).read_text())
 write('assets/gateway/profiles.mjs','export default '+(R/'media/big02/profile01.json').read_text()+';')
 primitive=(t/'assets/workflow/preflight/sha256.mjs').read_text();primitive=one(primitive,"export function sha256Text(text){if(typeof text!=='string')throw Error('SHA_TEXT');const src=new TextEncoder().encode(text);if(src.length>1048576)","export function hashBytes(src){if(!(src instanceof Uint8Array)||src.length>4194304)")
 write('assets/gateway/sha.mjs',primitive)
 pkg=(R/'media/big02/capture-package.mjs').read_text().replace("import { createHash } from 'node:crypto';","import {Buffer} from './portable.mjs';import {hashBytes}from'./sha.mjs';").replace("createHash('sha256').update(bytes).digest('hex')","hashBytes(bytes)");write('assets/gateway/capture-package.mjs',pkg)
 core=(R/'payload/gateway01/core.mjs').read_text().replace("import {randomUUID,randomBytes}from'node:crypto';","import{Buffer,randomUUID,randomBytes}from'./portable.mjs';").replace('../../media/big02/capture-package.mjs','./capture-package.mjs');core=one(core,'authorize(q){','authorize(q){this.store.guard();');core=one(core,'grant(q){','grant(q){this.store.guard();');write('assets/gateway/core.mjs',core)
 write('assets/gateway/mock-adapter.mjs',(R/'payload/gateway01/mock-adapter.mjs').read_text().replace("import {randomUUID} from 'node:crypto';","import {randomUUID}from'./portable.mjs';"))
 preview=(R/'media/big02/pipeline.mjs').read_text();preview="import profiles07 from './profiles.mjs';import{mediaPost07}from'./local-media.mjs';\n"+preview
 preview=one(preview,'const $=s=>',"let mockPose={pitchDeg:-45,yawDeg:0};export function setMockPose(v){mockPose={...v};}\nconst $=s=>")
 start=preview.index("for(const b of document.querySelectorAll('button'))b.disabled=true;");end=preview.index('const canvas=',start);preview=preview[:start]+preview[end:]
 start=preview.index('async function post(');end=preview.index('async function json(',start);preview=preview[:start]+"async function post(route,q,binary=false){return mediaPost07(route,q,binary);}\n"+preview[end:]
 preview=preview.replace('draw.rotate(-.22);','draw.rotate(-.22+mockPose.yawDeg*Math.PI/180);').replace("$('#shot-count').textContent=captureCount+' ảnh tổng hợp';",'').replace("$('#shutter').disabled=!running||age>1000;",'')
 start=preview.index("for(const id of['media-close','media-start'])");end=preview.index("$('#media-start').onclick=safe(start);",start);preview=preview[:start]+"$('#media-close').onclick=()=>panel.hidden=true;"+preview[end:]
 start=preview.index("for(const b of document.querySelectorAll('.nav-item[data-view]'))");end=preview.index("document.addEventListener('visibilitychange'",start);preview=preview[:start]+preview[end:]
 preview=one(preview,"const q=await(await fetch('/api/bootstrap')).json();nonce=q.nonce;profiles=q.profile;","profiles=profiles07;")
 preview=one(preview,'panel.hidden=false;}','panel.hidden=true;}');preview=one(preview,'init().catch(fail);',"await init().catch(fail);export{start,stop,switchFeed};export function getPreview(){return{running,feed,lastDisplay:lastDisplay?structuredClone(lastDisplay):null,ageMs:performance.now()-lastDisplayAt};}")
 preview=preview.replace('NODE_HRTIME_SEPARATE_NOT_SUBTRACTED_FROM_BROWSER','SAME_BROWSER_IN_PROCESS_RELAY').replace('HOST_SINGLE_BROWSER_SINGLE_VIEWER_NOT_ANDROID_OR_PRODUCTION_TRANSPORT','LOCAL_SYNTHETIC_CODEC_NOT_RF_OR_ANDROID_QUALIFICATION').replace('HOST01 · nguồn tổng hợp','PHONE07 · nguồn tổng hợp')
 write('assets/gateway/preview.mjs',preview)
 # The old SITL history/unknown-telemetry painter must not own the mock journey.
 p=t/'assets/fly87.mjs';p.write_text(one(p.read_text(),"function paint(){const v=model.view(performance.now()),review=document.body.dataset.view==='review';","function paint(){if(offline94){history.hidden=true;map.hidden=true;for(const el of document.querySelectorAll('[data-live]'))el.textContent='—';for(const id of['flight-time','battery-value','satellite-value','link-label'])document.getElementById(id).textContent='—';document.querySelector('#mode-name').textContent='MOCK · không kết nối UAV';return;}const v=model.view(performance.now()),review=document.body.dataset.view==='review';"))
 # Keep the original direct-mode module. Offline mock has a separate policy/store/UI.
 legacy=(t/'assets/operator01.mjs').read_text();write('assets/operator-legacy07.mjs',legacy)
 write('assets/operator01.mjs',"const e=JSON.parse(window.Native82Bridge.environment86());if(e.source==='direct')await import('./operator-legacy07.mjs');else await import('./gateway/cockpit07.mjs');")
 for name in ['index.html','sitl.html']:
  p=t/'assets'/name;p.write_text(p.read_text().replace('PHONE06 · SIMULATION','PHONE07 · SIMULATION').replace('</head>','<link rel="stylesheet" href="gateway/media.css"><link rel="stylesheet" href="gateway/cockpit07.css"></head>'))
 shell=(t/'src/ShellActivity.java').read_text();shell=one(shell,'private PhoneObserver06 observer06;','private PayloadBridge07 payload07;private PhoneObserver06 observer06;')
 shell=one(shell,'web.addJavascriptInterface(new Bridge(),"Native82Bridge");','try{payload07=new PayloadBridge07(this,()->trusted95&&foreground&&!dead&&source87.equals("mock")&&!direct95.isOpen(),()->payloadBinding07(),(id,value)->main.post(()->{if(trusted95&&foreground&&!dead)web.evaluateJavascript("window.native07Result&&window.native07Result("+JSONObject.quote(id)+","+value+")",null);}),io);}catch(Exception e){throw new IllegalStateException("PAYLOAD07_INIT",e);}web.addJavascriptInterface(payload07,"Native07Bridge");web.addJavascriptInterface(new Bridge(),"Native82Bridge");')
 shell=one(shell,'super.onActivityResult(request,result,data);','super.onActivityResult(request,result,data);if(request==9707){payload07.result(request,result,data);return;}')
 shell=one(shell,'saf91.busy()||raw96.busy()||phoneSaf06.busy()', 'saf91.busy()||raw96.busy()||phoneSaf06.busy()||payload07.busy()')
 shell=one(shell,'foreground=false;observer06.close();','foreground=false;if(payload07!=null)payload07.lifecycle(false);observer06.close();')
 shell=one(shell,'foreground=true;if(phoneSaf06!=null)','foreground=true;if(payload07!=null)payload07.lifecycle(true);if(phoneSaf06!=null)')
 shell=one(shell,'observer06.destroy();','if(payload07!=null)payload07.close();observer06.destroy();')
 shell=one(shell,'private RawSaf96 raw96;', 'private RawSaf96 raw96;') if False else shell
 shell=one(shell,'public final class ShellActivity extends Activity {','public final class ShellActivity extends Activity {') if False else shell
 method='''private JSONObject payloadBinding07()throws Exception{if(spaces.store().pending())throw new IOException("MISSION_JOURNAL_PENDING");DraftStore.Snapshot s=spaces.store().load();if(s==null)throw new IOException("COMMITTED_MISSION_REQUIRED");JSONObject d=new JSONObject(new String(s.bytes,StandardCharsets.UTF_8));JSONObject m=d.getJSONObject("mission"),c=d.optJSONObject("compiled"),p=c==null?null:c.optJSONObject("plan");return new JSONObject().put("workspaceHead",s.token).put("modelSha256",m.getString("sha256")).put("planSha256",p==null?"":p.getString("sha256"));}\n'''
 pos=shell.index(' private final class Bridge') if ' private final class Bridge' in shell else shell.index(' private class Bridge') if ' private class Bridge'in shell else shell.index(' public final class Bridge')
 shell=shell[:pos]+method+shell[pos:];shell=shell.replace("default-src 'self';media-src 'self';", "default-src 'self';img-src 'self' blob: data:;media-src 'self' blob:;")
 write('src/ShellActivity.java',shell)
 paths=['/'+str(p.relative_to(t/'assets'))for p in (t/'assets/gateway').rglob('*')if p.is_file()]+['/operator-legacy07.mjs'];p=t/'src/ResourcePolicy.java';p.write_text(one(p.read_text(),'Arrays.asList(','Arrays.asList('+','.join(json.dumps(x)for x in paths)+','))
 return source()
