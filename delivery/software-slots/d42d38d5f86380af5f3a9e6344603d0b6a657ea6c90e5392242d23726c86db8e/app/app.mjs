import { DEFAULT_SURVEY, DEMO_CAMERA, localFrame, planPolygonSurvey, surveyPackage, importSurvey } from './core/survey.mjs';
import { MissionLibrary, MissionSession, planDigest } from './core/session.mjs';
import { capabilityProfile } from './core/device.mjs';
import { RehearsalFlight } from './core/flight.mjs';
const $ = id => document.getElementById(id);
const form = $('mission-form');
let plan = planPolygonSurvey(DEFAULT_SURVEY), workspace = 'plan', paused = false, videoLost = false, dirty = false;
let polygon = structuredClone(DEFAULT_SURVEY.polygon), drawing=false, dragging=null, draftDigest=null, digestRevision=0;
const library=new MissionLibrary(localStorage), device=capabilityProfile();
let missionSession=new MissionSession();
let flight = new RehearsalFlight({ sessionId: crypto.randomUUID() });
let telemetryMode = 'HOLD', clockStart = performance.now(), selectedTransect = 0, zoom = 1, footprintVisible = false;
let lastEventSequence = -1, noticeTimer;
const now = () => performance.now() - clockStart;
const fmt = (v, decimals = 0) => v===null||v===undefined?'—':new Intl.NumberFormat('vi-VN', { maximumFractionDigits: decimals }).format(v);
const duration = seconds => seconds===null?'—': `${Math.floor(Math.round(seconds) / 60)}:${String(Math.round(seconds) % 60).padStart(2, '0')}`;
const labels = { plan: 'Mission Studio', fly: 'Flight Workspace', inspect: 'Sensor Workspace', review: 'Evidence Review' };
const mobile = () => matchMedia('(max-width:760px)').matches;
function notice(message) {
  clearTimeout(noticeTimer); $('notice').textContent = message;
  if (message) noticeTimer = setTimeout(() => { $('notice').textContent = ''; }, 5000);
}
function metric(label, value, unit = '', title = '') {
  return `<div class="metric"${title ? ` title="${title}"` : ''}><span>${label}</span><strong>${value}</strong><small>${unit}</small></div>`;
}
function visibleFocusables(panel) {
  return [...panel.querySelectorAll('button:not(:disabled),input:not(:disabled),select,textarea,summary,[tabindex="0"]')].filter(el => el.getBoundingClientRect().width > 0 && !el.closest('[hidden]'));
}
function setModalInert(panel, open) {
  if (open && mobile()) {
    panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-modal', 'true');
    document.querySelector('.rail').inert = true; document.querySelector('.topbar').inert = true;
    document.querySelector(workspace === 'plan' ? '.plot-column' : '.flight-workspace').inert = true;
  } else {
    panel.removeAttribute('role'); panel.removeAttribute('aria-modal');
    document.querySelector('.rail').inert = false; document.querySelector('.topbar').inert = false;
    document.querySelector('.plot-column').inert = false; document.querySelector('.flight-workspace').inert = false;
  }
}
function setPlanSettings(open) {
  document.body.classList.toggle('settings-open', open);
  $('open-plan-settings').setAttribute('aria-expanded', String(open));
  setModalInert($('plan-inspector'), open);
  if (open) $('close-plan-settings').focus(); else if (mobile()) $('open-plan-settings').focus();
}
function setTestConsole(open) {
  $('test-console').hidden = !open;
  $('open-test-console').setAttribute('aria-expanded', String(open));
  setModalInert($('test-console'), open);
  if (open) $('close-test-console').focus(); else $('open-test-console').focus();
}
function setFileMenu(open) {
  $('mission-menu').hidden = !open; $('open-mission-menu').setAttribute('aria-expanded', String(open));
  if (open) visibleFocusables($('mission-menu'))[0]?.focus(); else $('open-mission-menu').focus();
}
function setWorkspace(next) {
  if (document.body.classList.contains('settings-open')) setPlanSettings(false);
  if (!$('test-console').hidden) setTestConsole(false);
  if (!$('mission-menu').hidden) setFileMenu(false);
  workspace = next; $('workspace-title').textContent = labels[next];
  for (const name of Object.keys(labels)) $(`workspace-${name}`).hidden = name !== next;
  for (const button of document.querySelectorAll('[data-workspace]')) {
    const selected = button.dataset.workspace === next;
    button.classList.toggle('active', selected);
    if (selected) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current');
  }
  notice(''); renderFlight(); renderEvents();
}
function geometryView(geometry=plan,interactive=true) {
  const b=geometry.bounds,span=Math.max(b.maxX-b.minX,b.maxY-b.minY,100),margin=span*.30;
  const width=b.maxX-b.minX+margin*2,height=b.maxY-b.minY+margin*2,px=x=>x-b.minX+margin,py=y=>b.maxY+margin-y;
  const z=interactive?zoom:1,current=geometry.transects[Math.min(selectedTransect,geometry.lineCount-1)];
  const cx=z>1&&current?px((current.start.x+current.end.x)/2):width/2,cy=z>1&&current?py((current.start.y+current.end.y)/2):height/2;
  return {width,height,px,py,scale:Math.max(width,height)/650,view:[cx-width/z/2,cy-height/z/2,width/z,height/z]};
}
function surveySvg(interactive=true,geometry=plan) {
  const {width,height,px,py,scale,view}=geometryView(geometry,interactive),frame=localFrame(geometry.origin);
  const poly=interactive?polygon.map(p=>frame.forward(p)):geometry.polygonLocal;
  const points=poly.map(p=>`${px(p.x)},${py(p.y)}`).join(' '),prefix=interactive?'plan':'fly';
  const grid=50*Math.max(1,Math.ceil(Math.max(width,height)/700));
  const firstX=Math.floor(geometry.bounds.minX/grid)*grid,firstY=Math.floor(geometry.bounds.minY/grid)*grid;
  let guides='';for(let x=firstX-grid*3;x<geometry.bounds.maxX+grid*4;x+=grid)guides+=`<path d="M${px(x)} -${height*3}V${height*4}"/>`;
  for(let y=firstY-grid*3;y<geometry.bounds.maxY+grid*4;y+=grid)guides+=`<path d="M-${width*3} ${py(y)}H${width*4}"/>`;
  const showRoute=!interactive||!dirty,segments=showRoute?geometry.transects:[];
  const connectors=segments.slice(1).map((t,i)=>{const a=segments[i].end;return `<path d="M${px(a.x)} ${py(a.y)}L${px(t.start.x)} ${py(t.start.y)}" stroke="#797980" stroke-width="1" stroke-dasharray="4 4" fill="none" vector-effect="non-scaling-stroke"/>`;}).join('');
  const lines=segments.map((t,i)=>{const active=interactive&&i===selectedTransect,col=active?'#f2ca30':'#a5a5ad',mx=(t.start.x+t.end.x)/2,my=(t.start.y+t.end.y)/2;return `<g data-transect="${i}"><path class="route-hit" d="M${px(t.start.x)} ${py(t.start.y)}L${px(t.end.x)} ${py(t.end.y)}" stroke="transparent" stroke-width="22" fill="none" vector-effect="non-scaling-stroke"/><path d="M${px(t.start.x)} ${py(t.start.y)}L${px(t.end.x)} ${py(t.end.y)}" stroke="${col}" stroke-width="${active?2.4:1.1}" fill="none" vector-effect="non-scaling-stroke"/><text x="${px(mx)+scale*5}" y="${py(my)-scale*6}" font-size="${scale*10}" fill="${col}" font-family="Plex,sans-serif">${String(i+1).padStart(2,'0')}</text></g>`;}).join('');
  let footprint='';const current=geometry.transects[selectedTransect];if(interactive&&showRoute&&footprintVisible&&current&&geometry.footprintWidth){const mx=(current.start.x+current.end.x)/2,my=(current.start.y+current.end.y)/2,fw=geometry.footprintWidth,fh=geometry.footprintHeight;footprint=`<rect x="${px(mx)-fw/2}" y="${py(my)-fh/2}" width="${fw}" height="${fh}" transform="rotate(${geometry.settings.heading} ${px(mx)} ${py(my)})" fill="#f2ca30" fill-opacity=".10" stroke="#f2ca30" stroke-width="1" stroke-dasharray="4 4" vector-effect="non-scaling-stroke"/>`;}
  const vertices=interactive?poly.map((p,i)=>`<g data-vertex="${i}" class="vertex-hit"><circle cx="${px(p.x)}" cy="${py(p.y)}" r="${scale*16}" fill="transparent"/><circle cx="${px(p.x)}" cy="${py(p.y)}" r="${scale*4}" fill="#fff" stroke="#101012" stroke-width="1" vector-effect="non-scaling-stroke"/><text x="${px(p.x)+scale*8}" y="${py(p.y)-scale*8}" font-size="${scale*10}" fill="#eee" font-family="Plex,sans-serif">P${i+1}</text></g>`).join(''):'';
  const marker=segments.length?`<circle cx="${px(segments[0].start.x)}" cy="${py(segments[0].start.y)}" r="${scale*5}" fill="#101012" stroke="#f2ca30" stroke-width="1.5" vector-effect="non-scaling-stroke"/>`:'';
  const originLabel=`${geometry.origin.lat.toFixed(5)}°N / ${geometry.origin.lon.toFixed(5)}°E`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${view.join(' ')}" aria-hidden="true"><rect x="${-width*3}" y="${-height*3}" width="${width*7}" height="${height*7}" fill="#101012"/><g stroke="#29292d" stroke-width=".6" vector-effect="non-scaling-stroke">${guides}</g>${poly.length>2?`<polygon points="${points}" fill="#19191c" stroke="${dirty?'#c9c9d0':'#f0f0f0'}" stroke-width="1.2" vector-effect="non-scaling-stroke"/>`:''}${poly.length===2?`<polyline points="${points}" fill="none" stroke="#eee" stroke-width="1"/>`:''}${footprint}${connectors}${lines}${marker}${vertices}<text x="${width/2}" y="${height-scale*18}" font-size="${scale*10}" fill="#a5a5ad" text-anchor="middle" font-family="Plex,sans-serif">${originLabel} · ENU</text></svg>`;
}
function renderPlot() {
  $('mission-map').innerHTML=surveySvg();
  const onboardPlan=missionSession.onboard?planPolygonSurvey(missionSession.onboard.package.settings):plan;
  $('flight-map').innerHTML=surveySvg(false,onboardPlan);
  $('mission-map').setAttribute('aria-label',`${polygon.length} đỉnh polygon WGS84; ${dirty?'chưa tính lại':plan.lineCount+' đoạn tuyến'}. Kéo đỉnh để sửa; cộng/trừ zoom; trái/phải chọn tuyến.`);
  $('selected-transect-label').textContent=dirty||!plan.lineCount?'—':`${String(selectedTransect+1).padStart(2,'0')} / ${String(plan.lineCount).padStart(2,'0')}`;
  $('previous-transect').disabled=dirty||selectedTransect===0||!plan.lineCount;$('next-transect').disabled=dirty||selectedTransect>=plan.lineCount-1;
  $('zoom-in').disabled=zoom>=4;$('zoom-out').disabled=zoom<=.75;
  $('toggle-footprint').disabled=dirty||!plan.footprintWidth;$('toggle-footprint').setAttribute('aria-pressed',String(footprintVisible));
  $('map-scale').textContent=`Khung ×${zoom.toFixed(2)}`;
  $('area-description').textContent=`${polygon.length} đỉnh WGS84 · kéo đỉnh hoặc nhập tọa độ.`;
}
function markDirty(message='Thông số thay đổi. Tính lại tuyến để kiểm và áp dụng.') {
  dirty=true;draftDigest=null;digestRevision++;
  for(const id of ['save-mission','export-mission','open-fly'])$(id).disabled=true;
  $('mission-validation').textContent=message;$('mission-validation').classList.add('warning');$('mission-validation').dataset.state='dirty';
  $('mission-summary').innerHTML=metric('Diện tích','—','ha')+metric('Đoạn tuyến','—')+metric('Ảnh dự kiến','—')+metric('Thời gian dự kiến','—');
  $('optics-summary').replaceChildren();renderPlot();renderFlight();
}
function renderPlan() {
  selectedTransect=Math.max(0,Math.min(selectedTransect,plan.lineCount-1));
  form.elements.namedItem('altitude').value=Number(plan.settings.altitude.toFixed(6));
  document.querySelector('.mission-title strong').textContent=plan.settings.name;
  $('site-description').textContent=`${polygon.length} đỉnh WGS84 / ${fmt(plan.area/10000,2)} ha`;
  renderPlot();
  $('mission-summary').innerHTML=metric('Diện tích',fmt(plan.area/10000,2),'ha')+metric('Đoạn tuyến',fmt(plan.footprintWidth?plan.lineCount:null))+metric('Ảnh dự kiến',fmt(plan.photoCount))+metric('Thời gian dự kiến',duration(plan.nominalSeconds));
  $('optics-summary').innerHTML=`<div><span>GSD trên nền phẳng</span><strong>${fmt(plan.gsdCm,2)} cm/px</strong></div><div><span>Chu kỳ tối thiểu tuyến</span><strong>${fmt(plan.triggerInterval,2)} s</strong></div><div><span>Khoảng tuyến</span><strong>${fmt(plan.lineSpacing,1)} m</strong></div><div><span>Đường khảo sát + nối</span><strong>${fmt(plan.distance)} m</strong></div>`;
  $('altitude-note').textContent=plan.settings.altitudeFrame==='flat-reference'?`Độ cao tính: ${fmt(plan.effectiveAltitude,1)} m trên nền phẳng tham chiếu.`:'Chưa có dữ liệu để xác định AGL; footprint và số ảnh chưa tính.';
  const v=$('mission-validation');v.classList.toggle('warning',!plan.feasible);v.dataset.state=plan.feasible?'valid':'invalid';v.textContent=plan.feasible?'Đã kiểm mô hình khảo sát. Có thể lưu hoặc diễn tập.':plan.warnings.join(' ');
  // Valid drafts with missing external data can be saved; rehearsal upload cannot.
  for(const id of ['save-mission','export-mission'])$(id).disabled=false;$('open-fly').disabled=!plan.feasible;
  const revision=++digestRevision;planDigest(surveyPackage(plan.settings)).then(d=>{if(revision===digestRevision&&!dirty){draftDigest=d;renderSession();}});
  renderFlight();
}
function readForm() {
  const data=new FormData(form),num=k=>Number(data.get(k));
  const profile=data.get('cameraProfile'),camera=profile==='none'?null:{name:profile==='demo'?DEMO_CAMERA.name:'Camera tùy chỉnh',provenance:profile==='demo'?'demo':'operator-input',...Object.fromEntries(['sensorWidth','sensorHeight','focalLength','imageWidth','minInterval'].map(k=>[k,num(k)]))};
  return {name:String(data.get('name')),polygon:structuredClone(polygon),altitude:num('altitude'),altitudeFrame:String(data.get('altitudeFrame')),speed:num('speed'),heading:num('heading'),sideOverlap:num('sideOverlap'),frontOverlap:num('frontOverlap'),targetGsdCm:data.get('targetGsdCm')===''?null:num('targetGsdCm'),camera};
}
function updateFromForm() {
  try{if(!form.reportValidity())return false;plan=planPolygonSurvey(readForm());dirty=false;renderPlan();flight.event('survey-planned',now(),{areaM2:plan.area,segments:plan.lineCount,photoCount:plan.photoCount,feasible:plan.feasible});notice(plan.feasible?'Đã tính tuyến trên polygon WGS84.':plan.warnings[0]);return true;}
  catch(e){markDirty(e.message);notice(e.message);return false;}
}
function populateForm(settings) {
  for(const k of ['name','altitude','altitudeFrame','speed','heading','sideOverlap','frontOverlap','targetGsdCm'])form.elements.namedItem(k).value=settings[k]??'';
  form.elements.namedItem('cameraProfile').value=settings.camera===null?'none':settings.camera.provenance==='demo'?'demo':'custom';
  for(const k of ['sensorWidth','sensorHeight','focalLength','imageWidth','minInterval']){form.elements.namedItem(k).value=settings.camera?.[k]??DEMO_CAMERA[k];form.elements.namedItem(k).disabled=settings.camera===null;}
}
function loadPackage(pkg) {
  if(dirty&&!confirm('Thay bản nháp chưa áp dụng bằng nhiệm vụ được chọn?'))return;
  plan=planPolygonSurvey(pkg.settings);polygon=structuredClone(pkg.settings.polygon);dirty=false;drawing=false;selectedTransect=0;zoom=1;populateForm(pkg.settings);setDrawing(false);renderPlan();flight.event('mission-imported',now(),{format:pkg.format});
}
function download(name,data) {
  const blob=new Blob([JSON.stringify(data,null,2)+'\n'],{type:'application/json'}),link=document.createElement('a');
  link.href=URL.createObjectURL(blob);link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(link.href),1000);
}
function persistSession(){try{localStorage.setItem('aeris-survey-session-v1',JSON.stringify(missionSession.snapshot()));}catch(e){notice(`Không lưu được phiên: ${e.message}`);}}
function renderSession(){
  const states={empty:'Chưa nạp',uploading:'Chờ ACK',accepted:'Chờ readback',uploaded:'Readback đã khớp',running:'Đang diễn tập',paused:'Đã tạm dừng',completed:'Đã hoàn tất',aborted:'Đã kết thúc',failed:'Nạp thất bại'};
  const pkg=missionSession.onboard?.package,tx=missionSession.transaction, count=pkg?planPolygonSurvey(pkg.settings).lineCount:0;
  const pending=['uploading','accepted'].includes(missionSession.state);
  $('onboard-name').textContent=pending&&tx?`Đang nạp: ${tx.package.settings.name}`:pkg?pkg.settings.name:'Chưa nạp nhiệm vụ';$('mission-session-state').textContent=states[missionSession.state];
  const changed=pkg&&(dirty||draftDigest!==missionSession.onboard.digest);
  $('mission-session-detail').textContent=missionSession.error||`${pkg?`${missionSession.progress}/${count} tuyến hoàn tất · plan ${missionSession.onboard.digest.slice(0,8)}`:'ACK upload chưa chứng minh nội dung trên phương tiện.'}${changed?' · Bản nháp khác mission đã nạp.':''}`;
  $('mission-start').disabled=!['uploaded','paused'].includes(missionSession.state);$('mission-start').textContent=missionSession.state==='paused'?'Tiếp tục diễn tập':'Chạy diễn tập';
  $('mission-pause').disabled=missionSession.state!=='running';$('mission-abort').disabled=!['running','paused','uploading','accepted'].includes(missionSession.state);
  $('mission-ack').disabled=missionSession.state!=='uploading';$('mission-readback').disabled=missionSession.state!=='accepted';$('mission-advance').disabled=missionSession.state!=='running';
}
async function uploadRehearsal(){
 try{if(dirty||!plan.feasible)throw Error('Cần tính và kiểm mission trước khi nạp.');await missionSession.beginUpload(surveyPackage(plan.settings));flight.event('mission-upload-requested',now(),{digest:missionSession.transaction.digest});persistSession();setWorkspace('fly');setTestConsole(true);renderSession();}
 catch(e){notice(e.message);renderSession();}
}
function sessionEvent(){return {transactionId:missionSession.transaction?.id,vehicleId:missionSession.vehicleId,sessionId:missionSession.sessionId};}
function setDrawing(open){drawing=open;$('draw-area').setAttribute('aria-pressed',String(open));$('complete-area').hidden=!open;document.querySelector('.map-stage').classList.toggle('drawing',open);}
function mapPoint(event){const svg=$('mission-map').querySelector('svg'),point=new DOMPoint(event.clientX,event.clientY).matrixTransform(svg.getScreenCTM().inverse()),v=geometryView();return localFrame(plan.origin).reverse({x:point.x+plan.bounds.minX-(v.width-(plan.bounds.maxX-plan.bounds.minX))/2,y:plan.bounds.maxY+(v.height-(plan.bounds.maxY-plan.bounds.minY))/2-point.y});}
function telemetry() {
  const at=now();flight.receiveTelemetry({aircraftId:flight.aircraftId,sessionId:flight.sessionId,sampleMs:at,mode:telemetryMode,altitude:telemetryMode==='AUTO'?plan.effectiveAltitude:0,speed:telemetryMode==='AUTO'?plan.settings.speed:0,battery:86},at);
}
function renderFlight() {
  renderSession();
  const at=now();flight.tick(at);const fresh=flight.isFresh(at),t=flight.telemetry;
  $('link-dot').classList.toggle('stale',!fresh);$('link-label').textContent=fresh?'Telemetry diễn tập':'Telemetry đã cũ';
  $('flight-mode').textContent=`${t?.mode||'—'}${fresh?'':' / dữ liệu cũ'}`;
  $('telemetry-values').classList.toggle('stale',!fresh);
  const val=key=>fresh&&t?fmt(t[key]):'—';
  $('telemetry-values').innerHTML=metric(fresh?'Độ cao giả lập':'Độ cao / dữ liệu cũ',val('altitude'),'m',t?`Cuối cùng: ${fmt(t.altitude)} m`:'Chưa có dữ liệu')+metric(fresh?'Tốc độ giả lập':'Tốc độ / dữ liệu cũ',val('speed'),'m/s',t?`Cuối cùng: ${fmt(t.speed)} m/s`:'Chưa có dữ liệu')+metric(fresh?'Pin giả lập':'Pin / dữ liệu cũ',val('battery'),'%',t?`Cuối cùng: ${fmt(t.battery)}%`:'Chưa có dữ liệu')+metric('Tuổi telemetry',t?fmt((at-t.receivedAtMs)/1000,1):'—','s');
  const c=flight.command;
  const text={sent:'Đang chờ ACK',accepted:'ACK accepted · chưa xác nhận thực thi','in-progress':'Đang xử lý · chờ telemetry',observed:'Telemetry mới đã xác nhận chế độ',rejected:'Lệnh bị mô hình từ chối','timed-out':'Quá thời gian chờ · kết quả chưa xác định'};
  $('command-state').textContent=c?`${c.mode}: ${text[c.state]}`:'Chưa có lệnh.';
  const pending=c&&!['observed','rejected','timed-out'].includes(c.state);
  $('command-state').dataset.state=c?.state||'idle';
  const stages=['sent','accepted','observed'];
  for(const el of document.querySelectorAll('[data-command-stage]')){
    const index=stages.indexOf(el.dataset.commandStage),currentIndex=stages.indexOf(c?.state);
    el.classList.toggle('current',!!c&&el.dataset.commandStage===c.state);
    el.classList.toggle('completed',currentIndex>index);
  }
  for(const button of document.querySelectorAll('[data-mode]'))button.disabled=!fresh||!!pending||button.dataset.mode===t?.mode||(button.dataset.mode==='AUTO'&&(!plan.feasible||dirty||!missionSession.onboard));
  $('command-availability').textContent=!fresh?'Dữ liệu đã cũ. Khôi phục telemetry trước khi gửi lệnh.':pending?'Đang chờ kết quả của lệnh hiện tại.':dirty?'Thông số nhiệm vụ chưa áp dụng. Quay lại Plan để tính và kiểm.':!plan.feasible?'Camera không theo kịp. Điều chỉnh thông số trong Plan.':'AUTO, HOLD và RTL chỉ tác động tới mô hình diễn tập.';
  $('ack-accepted').disabled=!pending||c?.state==='accepted';$('ack-rejected').disabled=!pending;
  $('observe-mode').disabled=!pending||paused||!['accepted','in-progress'].includes(c?.state);
  $('pause-telemetry').textContent=paused?'Khôi phục telemetry':'Tạm dừng telemetry';
  $('toggle-video').textContent=videoLost?'Khôi phục kênh video diễn tập':'Mô phỏng mất video';
  $('video-status').textContent=videoLost?'Mô hình báo mất kênh video. Telemetry được kiểm riêng.':'Kênh video diễn tập sẵn sàng; chưa có luồng hình.';
  $('video-status').classList.toggle('warning',videoLost);
  document.querySelector('.video-empty span').textContent=videoLost?'Mất kênh video giả lập':'Video chưa kết nối';
  $('fly-checks').textContent=`Telemetry: ${fresh?'mới':'cũ'} · Video: ${videoLost?'mất kênh giả lập':'chưa có luồng thật'}.`;
}
function renderEvents() {
  if(workspace!=='review')return;
  const latest=flight.events.at(-1)?.sequence||0;if(latest===lastEventSequence)return;lastEventSequence=latest;
  const body=$('event-rows');body.replaceChildren();
  for(const event of flight.events.slice().reverse()){
    const row=document.createElement('tr');const detail=Object.entries(event).filter(([key])=>!['sequence','atMs','aircraftId','sessionId','type'].includes(key)).map(([key,value])=>`${key}: ${value}`).join(' · ');
    for(const value of [event.sequence,`${(event.atMs/1000).toFixed(1)} s`,event.type,detail||'—']){const cell=document.createElement('td');cell.textContent=value;row.append(cell);}body.append(row);
  }
  if(!flight.events.length){const row=document.createElement('tr'),cell=document.createElement('td');cell.colSpan=4;cell.textContent='Chưa có sự kiện. Lập nhiệm vụ hoặc thử một lệnh trong Fly.';row.append(cell);body.append(row);}
}
for(const button of document.querySelectorAll('[data-workspace]'))button.addEventListener('click',()=>setWorkspace(button.dataset.workspace));
form.addEventListener('submit',e=>{e.preventDefault();updateFromForm();});
form.addEventListener('input',e=>{
 if(['sensorWidth','sensorHeight','focalLength','imageWidth','minInterval'].includes(e.target.name))form.elements.namedItem('cameraProfile').value='custom';
 if(e.target.name==='cameraProfile'){const selected=e.target.value;for(const k of ['sensorWidth','sensorHeight','focalLength','imageWidth','minInterval']){form.elements.namedItem(k).disabled=selected==='none';if(selected==='demo')form.elements.namedItem(k).value=DEMO_CAMERA[k];}}
 markDirty();
});
$('open-mission-menu').addEventListener('click',()=>setFileMenu($('mission-menu').hidden));
$('save-mission').addEventListener('click',()=>{try{if(dirty)throw Error('Tính lại bản nháp trước khi lưu.');library.save(plan.settings);flight.event('mission-saved-locally',now());setFileMenu(false);notice('Đã lưu local. Mission trên mô hình không thay đổi.');}catch(e){notice(`Không lưu được: ${e.message}`);}});
$('load-mission').addEventListener('click',()=>{try{const entries=library.list(),list=$('mission-library-list');list.replaceChildren();if(!entries.length){const p=document.createElement('p');p.textContent='Chưa có nhiệm vụ đã lưu.';list.append(p);}for(const entry of entries){const b=document.createElement('button'),strong=document.createElement('strong'),span=document.createElement('span');b.type='button';strong.textContent=entry.package.settings.name;span.textContent=`${entry.package.settings.polygon.length} đỉnh · ${new Date(entry.savedAt).toLocaleString('vi-VN')}`;b.append(strong,span);b.addEventListener('click',()=>{loadPackage(entry.package);$('library-dialog').close();notice('Đã mở và tính lại nhiệm vụ đã lưu.');});list.append(b);}setFileMenu(false);$('library-dialog').showModal();}catch(e){notice(e.message);}});
$('export-mission').addEventListener('click',()=>{try{if(dirty)throw Error('Tính lại bản nháp trước khi xuất.');download('survey.aeris.json',surveyPackage(plan.settings));flight.event('mission-exported',now());setFileMenu(false);notice('Đã xuất polygon và thông số. Gói chưa dùng cho autopilot.');}catch(e){notice(e.message);}});
$('import-mission').addEventListener('click',()=>{$('mission-file').click();setFileMenu(false);});
$('mission-file').addEventListener('change',async e=>{try{const file=e.target.files[0];if(!file)return;if(file.size>256*1024)throw Error('Gói vượt giới hạn 256 KB.');loadPackage(importSurvey(await file.text()));notice('Đã nhập nhiệm vụ và tính lại kết quả.');}catch(e){notice(e.message);}finally{$('mission-file').value='';}});
$('open-fly').addEventListener('click',uploadRehearsal);$('inspect-fly').addEventListener('click',()=>{setWorkspace('fly');setTestConsole(true);});
$('draw-area').addEventListener('click',()=>{if(drawing){polygon=structuredClone(plan.settings.polygon);setDrawing(false);markDirty('Đã hủy vùng đang vẽ. Tính lại để kiểm.');return;}polygon=[];setDrawing(true);markDirty('Chạm để thêm đỉnh; Kết thúc vẽ khi đủ ít nhất 3 đỉnh.');});
$('complete-area').addEventListener('click',()=>{if(polygon.length<3){notice('Cần ít nhất 3 đỉnh.');return;}if(updateFromForm())setDrawing(false);});
$('edit-coordinates').addEventListener('click',()=>{$('coordinates-input').value=polygon.map(p=>`${p.lat.toFixed(8)}, ${p.lon.toFixed(8)}`).join('\n');$('coordinates-error').textContent='';$('coordinates-dialog').showModal();});
$('apply-coordinates').addEventListener('click',()=>{try{const text=$('coordinates-input').value;if(text.length>12000)throw Error('Danh sách tọa độ quá dài.');const points=text.trim().split(/\n/).filter(l=>l.trim()).map(line=>{const parts=line.trim().split(/[,;\s]+/);if(parts.length!==2)throw Error('Mỗi dòng cần đúng latitude, longitude.');return {lat:Number(parts[0]),lon:Number(parts[1])};});const candidate={...readForm(),polygon:points};planPolygonSurvey(candidate);polygon=points;setDrawing(false);dirty=false;plan=planPolygonSurvey(candidate);zoom=1;renderPlan();$('coordinates-dialog').close();notice('Đã áp dụng tọa độ và tính lại tuyến.');}catch(e){$('coordinates-error').textContent=e.message;}});
$('mission-map').addEventListener('pointerdown',e=>{if(drawing||e.button!==0)return;const v=e.target.closest('[data-vertex]');if(v){dragging=Number(v.dataset.vertex);$('mission-map').setPointerCapture(e.pointerId);e.preventDefault();}});
$('mission-map').addEventListener('pointermove',e=>{if(dragging===null)return;try{polygon[dragging]=mapPoint(e);markDirty('Đang sửa ranh giới; nhả để tính lại tuyến.');}catch(err){notice(err.message);}});
$('mission-map').addEventListener('pointerup',e=>{if(dragging!==null){dragging=null;if($('mission-map').hasPointerCapture(e.pointerId))$('mission-map').releasePointerCapture(e.pointerId);updateFromForm();}});
$('mission-map').addEventListener('pointercancel',()=>{if(dragging!==null){dragging=null;markDirty('Thao tác kéo bị hủy; tính lại để kiểm ranh giới.');}});
$('mission-ack').addEventListener('click',()=>{missionSession.ack({...sessionEvent(),result:'accepted'});flight.event('mission-upload-ack',now());persistSession();renderFlight();});
$('mission-readback').addEventListener('click',async()=>{await missionSession.readback({...sessionEvent(),package:missionSession.transaction.package});flight.event('mission-readback',now(),{state:missionSession.state});persistSession();renderPlot();renderFlight();});
$('mission-start').addEventListener('click',()=>{try{missionSession.start();flight.event('mission-run-rehearsal',now(),{digest:missionSession.onboard.digest});persistSession();renderFlight();}catch(e){notice(e.message);}});
$('mission-pause').addEventListener('click',()=>{missionSession.pause();flight.event('mission-paused-rehearsal',now());persistSession();renderFlight();});
$('mission-abort').addEventListener('click',()=>{missionSession.abort();flight.event('mission-aborted-rehearsal',now());persistSession();renderFlight();});
$('mission-advance').addEventListener('click',()=>{missionSession.observeProgress({vehicleId:missionSession.vehicleId,sessionId:missionSession.sessionId,completedTransects:missionSession.progress+1});persistSession();renderFlight();});
$('open-plan-settings').addEventListener('click',()=>setPlanSettings(true));$('close-plan-settings').addEventListener('click',()=>setPlanSettings(false));
$('open-test-console').addEventListener('click',()=>setTestConsole($('test-console').hidden));$('close-test-console').addEventListener('click',()=>setTestConsole(false));
function selectTransect(index){selectedTransect=Math.max(0,Math.min(plan.lineCount-1,index));renderPlot();}
function changeZoom(direction){zoom=Math.max(.75,Math.min(4,Math.round((zoom+direction*.25)*100)/100));renderPlot();}
$('previous-transect').addEventListener('click',()=>selectTransect(selectedTransect-1));$('next-transect').addEventListener('click',()=>selectTransect(selectedTransect+1));
$('zoom-in').addEventListener('click',()=>changeZoom(1));$('zoom-out').addEventListener('click',()=>changeZoom(-1));$('fit-map').addEventListener('click',()=>{zoom=1;renderPlot();});
$('toggle-footprint').addEventListener('click',()=>{footprintVisible=!footprintVisible;renderPlot();});
$('mission-map').addEventListener('click',e=>{if(drawing){if(polygon.length>=64){notice('Tối đa 64 đỉnh.');return;}try{polygon.push(mapPoint(e));markDirty('Chạm thêm đỉnh hoặc Kết thúc vẽ.');}catch(err){notice(err.message);}return;}const element=e.target.closest('[data-transect]');if(element&&!dirty)selectTransect(Number(element.dataset.transect));});
$('mission-map').addEventListener('keydown',e=>{if(['+','=','-','0','ArrowLeft','ArrowRight'].includes(e.key))e.preventDefault();if(['+','='].includes(e.key))changeZoom(1);if(e.key==='-')changeZoom(-1);if(e.key==='0'){zoom=1;renderPlot();}if(e.key==='ArrowLeft')selectTransect(selectedTransect-1);if(e.key==='ArrowRight')selectTransect(selectedTransect+1);});
for(const button of document.querySelectorAll('[data-mode]'))button.addEventListener('click',()=>{try{flight.request(button.dataset.mode,now());notice('Yêu cầu đã gửi vào mô hình diễn tập.');}catch(e){notice(e.message);}renderFlight();});
function ack(result){if(!flight.command)return;flight.ack({commandId:flight.command.id,aircraftId:flight.aircraftId,sessionId:flight.sessionId,result},now());renderFlight();}
$('ack-accepted').addEventListener('click',()=>ack('accepted'));$('ack-rejected').addEventListener('click',()=>ack('rejected'));
$('observe-mode').addEventListener('click',()=>{if(!flight.command||paused)return;telemetryMode=flight.command.mode;telemetry();renderFlight();});
$('pause-telemetry').addEventListener('click',()=>{paused=!paused;flight.event(paused?'telemetry-paused':'telemetry-restored',now());if(!paused)telemetry();renderFlight();});
$('toggle-video').addEventListener('click',()=>{videoLost=!videoLost;flight.event(videoLost?'video-link-lost':'video-link-restored',now());renderFlight();});
$('reset-rehearsal').addEventListener('click',()=>$('new-session-dialog').showModal());
$('export-before-reset').addEventListener('click',()=>download('aeris-rehearsal-events.json',flight.exportLog()));
$('new-session-dialog').addEventListener('close',()=>{if($('new-session-dialog').returnValue!=='reset')return;flight=new RehearsalFlight({sessionId:crypto.randomUUID()});missionSession=new MissionSession();persistSession();clockStart=performance.now();telemetryMode='HOLD';paused=false;videoLost=false;lastEventSequence=-1;telemetry();flight.event('session-started',now(),{source:'synthetic-local'});renderFlight();renderEvents();notice('Đã bắt đầu phiên mới.');});
$('export-events').addEventListener('click',()=>download('aeris-rehearsal-events.json',flight.exportLog()));
document.addEventListener('pointerdown',e=>{if(!$('mission-menu').hidden&&!e.target.closest('#mission-menu')&&!e.target.closest('#open-mission-menu'))setFileMenu(false);});
document.addEventListener('keydown',e=>{
  if(e.key==='Escape'){if(!$('mission-menu').hidden)setFileMenu(false);else if(document.body.classList.contains('settings-open'))setPlanSettings(false);else if(!$('test-console').hidden)setTestConsole(false);}
  if(e.key==='Tab'&&mobile()){
    const panel=document.body.classList.contains('settings-open')?$('plan-inspector'):!$('test-console').hidden?$('test-console'):null;
    if(!panel)return;const items=visibleFocusables(panel),first=items[0],last=items.at(-1);
    if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
  }
});
matchMedia('(max-width:760px)').addEventListener('change',()=>{setModalInert($('plan-inspector'),false);if(document.body.classList.contains('settings-open')&&mobile())setPlanSettings(true);else if(!$('test-console').hidden&&mobile())setTestConsole(true);});
populateForm(plan.settings);
try{const raw=localStorage.getItem('aeris-survey-session-v1');if(raw)missionSession=await MissionSession.restore(JSON.parse(raw));}catch(e){notice(`Phiên cũ chưa khôi phục: ${e.message}`);}
telemetry();flight.event('session-started',now(),{source:'synthetic-local',deviceContext:device.context});renderPlan();renderFlight();
setInterval(()=>{if(!paused)telemetry();renderFlight();renderEvents();},500);
