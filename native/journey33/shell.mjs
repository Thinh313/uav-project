import {DurableJourney,validateWorkspace} from './journey.mjs';
import {FIELDS,defaultForm,addMapVertex,restoreBody} from './editor.mjs';
import {localFrame,DEMO_ORIGIN} from './vendor/survey.mjs';

const $=id=>document.getElementById(id), pending=new Map();
const native=!!window.Native33Bridge, now=()=>Math.floor(performance.now());
let busy=false,draw=false,view='Plan';
window.native33Result=(id,raw)=>{
  const p=pending.get(id);if(!p)return;pending.delete(id);
  try{const d=JSON.parse(raw);d.ok?p.resolve(d):p.reject(Error(d.error));}catch(e){p.reject(e);}
};
async function storage(action,expected,body){
  if(native)return new Promise((resolve,reject)=>{
    const id=crypto.randomUUID(),timer=setTimeout(()=>{pending.delete(id);reject(Error('Native timeout; commit unknown'))},10000);
    pending.set(id,{resolve:d=>{clearTimeout(timer);resolve(d)},reject:e=>{clearTimeout(timer);reject(e)}});
    window.Native33Bridge.request(id,action,expected,body??'');
  });
  const r=await fetch('/workspace/'+action,{method:action==='load'?'GET':'POST',headers:action==='load'?{}:{'Content-Type':'application/json'},body:action==='load'?undefined:JSON.stringify({token:expected,body})});
  const d=await r.json();if(!r.ok||!d.ok)throw Error(d.error??'Storage refused');return d;
}
const journey=new DurableJourney(storage);
const message=x=>$('status').textContent=x;
function writeForm(){for(const k of FIELDS)$(k).value=journey.form[k];}
function navigate(v){view=v;document.querySelectorAll('[data-panel]').forEach(p=>p.hidden=p.dataset.panel!==v);document.querySelectorAll('[data-view]').forEach(p=>p.setAttribute('aria-current',String(p.dataset.view===v)));$('workspace').textContent={Plan:'Khảo sát',Preflight:'Preflight',Fly:'Fly mock',Review:'Review'}[v];render();}
function render(){
  const c=journey.bundle,w=journey.workspace,r=w?.current;
  $('mission-title').textContent=journey.form.name||'Draft chưa có tên';$('phase').textContent=journey.phase;
  for(const id of [...FIELDS,'draw','undo','compile','default','import'])$(id).disabled=busy||journey.blocked||!!journey.running;
  for(const id of ['save','inspect','home','datum','start','step','land','loss','ack','export'])$(id).disabled=busy||journey.blocked;
  $('reload').disabled=busy;$('map').classList.toggle('drawing',draw);
  $('storage').textContent=(journey.blocked?'Chưa xác nhận storage':journey.dirty?'Có thay đổi chưa lưu':'Checkpoint đã commit')+' · revision '+journey.revision+' · '+journey.token.slice(0,12);
  $('gates').textContent='Home: '+journey.home+' · Độ cao: '+journey.datum+' · Gate fresh: '+journey.ready(now());
  $('review-summary').textContent=r? r.phase==='COMPLETED_MOCK'?'Hoàn tất mock đã lưu; ảnh/video thực: 0':r.phase.startsWith('INTERRUPTED_')?'Phiên gián đoạn đã lưu; cần nhiệm vụ mới':'Phiên mock đang chuẩn bị/chạy; chưa kết luận hoàn tất':'Chưa có phiên mock';
  $('review').textContent=r?JSON.stringify(r,null,2):'Chưa có event';$('historical').textContent=JSON.stringify(w?.history??[],null,2);
  $('review-storage').textContent='Mọi bước được checkpoint cùng workspace · history '+(w?.history.length??0)+'/4 · không restore quyền';
  let polygon=[],route=[];
  try{const home=localFrame(DEMO_ORIGIN);polygon=journey.form.vertices.trim().split(/\r?\n/).map(l=>{const [lat,lon]=l.split(',').map(Number);if(!Number.isFinite(lat)||!Number.isFinite(lon))throw Error();return home.forward({lat,lon});});if(c){const frame=localFrame(c.geometry.origin);route=c.geometry.waypoints.map(p=>home.forward(frame.reverse(p)));}}catch{}
  const into=$('geometry');into.replaceChildren();
  const line=(points,stroke,fill)=>{const e=document.createElementNS('http://www.w3.org/2000/svg','polyline');e.setAttribute('points',points.map(p=>p.x+','+-p.y).join(' '));e.setAttribute('stroke',stroke);e.setAttribute('fill',fill);e.setAttribute('stroke-width','3');into.append(e);};
  if(polygon.length)line([...polygon,polygon[0]],'#fff','#ffffff08');if(route.length)line(route,'#939da7','none');
  $('stats').textContent=c?Math.round(c.geometry.area)+' m² · '+c.geometry.lineCount+' tuyến · '+c.geometry.photoCount+' ảnh ước tính · '+r.cursor+'/'+c.geometry.waypoints.length+' điểm mock':'Chưa có tuyến hiện tại · compile/preflight mới để chạy';
}
async function action(fn){if(busy)return;busy=true;render();try{await fn();}catch(e){message(e.message);}finally{try{await journey.finishBackground();}catch(e){message(e.message);}busy=false;render();}}
function edited(form){try{journey.edit(form);writeForm();draw=false;message('Draft đổi; tuyến/preflight đã thu hồi. Nhấn Lưu draft để giữ thay đổi.');}catch(e){writeForm();message(e.message);}render();}
for(const k of FIELDS)$(k).addEventListener('input',()=>edited(Object.fromEntries(FIELDS.map(f=>[f,$(f).value]))));
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>navigate(b.dataset.view));
$('compile').onclick=()=>action(async()=>{await journey.compile(now());message('Tuyến và provenance đã commit. Tiếp tục xác nhận Home/độ cao.');navigate('Preflight');});
$('save').onclick=()=>action(async()=>{await journey.save(now());message('Draft đã commit cùng hồ sơ; không lưu quyền điều khiển.');});
$('reload').onclick=()=>action(async()=>{await journey.load(now());writeForm();navigate('Plan');message('Đã đọc head đã commit; phiên chưa kết thúc được đánh dấu gián đoạn. Compile/preflight mới.');});
$('default').onclick=()=>edited(defaultForm());$('undo').onclick=()=>edited({...journey.form,vertices:journey.form.vertices.trim().split(/\r?\n/).slice(0,-1).join('\n')});
$('draw').onclick=()=>{draw=!draw;render();};
$('map').addEventListener('pointerdown',e=>{if(!draw||busy||journey.running||journey.blocked)return;const p=$('map').createSVGPoint();p.x=e.clientX;p.y=e.clientY;const at=p.matrixTransform($('map').getScreenCTM().inverse());try{edited(addMapVertex(journey.form,at.x,-at.y));draw=true;}catch(e){message(e.message);}});
for(const [id,kind]of [['inspect','PREFLIGHT_CHECK'],['home','HOME_CONFIRMED'],['datum','DATUM_CONFIRMED'],['start','MOCK_STARTED'],['ack','ACK_NOT_EXECUTION'],['step','POINT_OBSERVED'],['land','LANDING_OBSERVED'],['loss','INTERRUPTED_LINK']])$(id).onclick=()=>action(async()=>{await journey.transition(kind,now());message('Đã commit '+kind+' · không có lệnh bay thực');if(kind==='DATUM_CONFIRMED'&&journey.ready(now()))navigate('Fly');if(kind==='LANDING_OBSERVED'||kind==='INTERRUPTED_LINK')navigate('Review');});
$('export').onclick=()=>action(async()=>{const raw=JSON.stringify(journey.workspace);await validateWorkspace(raw);if(native){await storage('export',journey.token,raw);message('Đã mở đích xuất; chưa xác nhận provider ghi xong');return;}const u=URL.createObjectURL(new Blob([raw],{type:'application/json'})),a=document.createElement('a');a.href=u;a.download='aeris-native33-workspace.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});
$('import').onchange=()=>action(async()=>{const f=$('import').files[0];if(!f||f.size>262144)throw Error('Import byte bound');const raw=await f.text(),d=JSON.parse(raw),restored=d.format==='aeris-native33-workspace'?(await validateWorkspace(raw)).draft:JSON.parse(raw);const value=await restoreBody(JSON.stringify(restored));journey.edit(value.form);writeForm();navigate('Plan');message('Chỉ nhập draft; chưa lưu, không nhập quyền hoặc tiếp tục run');$('import').value='';});
function suspend(){draw=false;void journey.background(now()).catch(e=>message(e.message)).finally(render);render();message('Mất focus/background · gate thu hồi · không aircraft HOLD');}
window.addEventListener('blur',suspend);window.addEventListener('focus',()=>{journey.focus();render();});
window.addEventListener('offline',()=>{if(journey.bundle&&!journey.blocked)void action(()=>journey.transition('INTERRUPTED_LINK',now()));});
document.addEventListener('visibilitychange',()=>{if(document.hidden)suspend();});
window.native33Lifecycle=v=>v==='pause'?suspend():(journey.focus(),render());
$('environment').textContent=native?'Android offline · development mock':'Host preview · chưa phải nghiệm thu Android';
writeForm();navigate('Plan');await action(async()=>{await journey.load(now());writeForm();render();message('Workspace sẵn sàng; compile/preflight mới, không restore quyền');});
