import {NativeWorkflow44} from './workflow/workflow.mjs';
import {FIELDS} from './workflow/editor.mjs';
import {localFrame,DEMO_ORIGIN} from './workflow/vendor/survey.mjs';
import {validateCapsule44} from './workflow/capsule.mjs';
import {ADJUSTMENTS,tickPresentationKey,reviewPresentation} from './controls82.mjs';
import {storage82,nativeTransport} from './transport82.mjs';
const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
export class Controller82{
 constructor(ui){
  this.ui=ui;this.w=new NativeWorkflow44(storage82);this.started=performance.now();this.busy=false;this.loaded=false;this.error='';this.routeConfirmed=false;this.lastView=null;this.interruptionPending=false;this.lifecycleActive=false;this.pendingConfirmation=new Map();this.paused=false;
  window.native82Lifecycle=action=>{if(action==='pause')this.background();else if(action==='resume'){this.lifecycleActive=false;this.w.focus();this.ui.authorityEvent({kind:'revokeAll'});this.routeConfirmed=false;this.ui.render();}};
 }
 now(){return Math.floor(performance.now()-this.started);}
 form(){const f={...this.w.journey.form};for(const k of ['name','vertices','heading','sideOverlap','frontOverlap'])f[k]=$('#form-'+k).value;f.altitude=String(this.ui.state.mission.altitude);f.speed=String(this.ui.state.mission.speed);return f;}
 fill(){const f=this.w.journey.form;for(const k of ['name','vertices','heading','sideOverlap','frontOverlap'])$('#form-'+k).value=f[k];this.ui.state.mission.altitude=Number(f.altitude);this.ui.state.mission.speed=Number(f.speed);this.ui.state.mission.type='survey';}
 async action(fn){if(this.busy)return false;this.busy=true;this.error='';this.ui.render();try{await fn();return true;}catch(e){this.error=e.message;this.ui.toast(e.message);this.ui.emit('native82-error',{reason:e.message});return false;}finally{this.busy=false;this.ui.render();if(this.interruptionPending){this.interruptionPending=false;if(this.w.journey.running)this.action(()=>this.w.journey.transition('INTERRUPTED_LINK',this.now()));}}}
 async initialize(){
  this.ui.state.view=document.body.dataset.source87==='sitl'?'fly':'plan';this.ui.state.map=true;this.bind();
  await this.action(async()=>{await this.w.load(this.now());if(!this.w.store.capsule)this.w.edit({...this.w.journey.form,altitude:'30',speed:'1'});if(document.body.dataset.source87==='sitl'&&!this.w.store.capsule)await this.w.save(this.now());this.loaded=true;this.fill();});
  this.ui.render();
  this.timer=setInterval(()=>{if(this.loaded&&!document.hidden){if(this.w.source&&!this.w.grant)this.w.tick(this.now());const key=tickPresentationKey(this.w.state(this.now()));if(key!==this.lastTickKey){this.lastTickKey=key;this.ui.render();}}},750);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)this.background();else{this.lifecycleActive=false;this.w.focus();this.ui.authorityEvent({kind:'revokeAll'});this.ui.render();}});
  window.addEventListener('pagehide',()=>{clearInterval(this.timer);this.background();});
 }
 bind(){
  for(const k of ['name','vertices','heading','sideOverlap','frontOverlap'])$('#form-'+k).oninput=()=>this.edited();
  $('#native-save').onclick=()=>this.action(async()=>{this.guardEdit();this.w.edit(this.form());await this.w.save(this.now());this.ui.toast('Đã xác nhận lưu journal · không có quyền được lưu');});
  $('#native-compile').onclick=()=>this.action(async()=>{this.guardEdit();this.w.edit(this.form());await this.w.compile(this.now());this.routeConfirmed=false;this.ui.setView('preflight');});
  $('#native-inspect').onclick=()=>this.inspect();
  $('#native-reload').onclick=()=>this.action(async()=>{this.ui.authorityEvent({kind:'revokeAll'});this.w.revoke();this.routeConfirmed=false;await this.w.load(this.now());this.loaded=true;this.fill();this.ui.toast('Đã đọc và replay journal; không khôi phục quyền');});
  $('#native-point').onclick=()=>this.action(async()=>{this.guardControl();if(this.paused)throw Error('Mock đang tạm dừng; tiếp tục có chủ ý');await this.w.point(this.now());});
  $('#native-land').onclick=()=>this.action(async()=>{this.guardControl();if(this.paused)throw Error('Mock đang tạm dừng');await this.w.land(this.now());this.ui.setView('review');});
  $('#native-ack').onclick=()=>this.action(async()=>{this.guardControl();await this.w.ack(this.now());this.ui.toast('ACK ghi vào hồ sơ; không tăng điểm và không xác nhận bay');});
  $('#native-start').onclick=()=>this.start();$('#pause').onclick=()=>this.pauseMock();$('#native-resume').onclick=()=>{try{this.guardControl();if(!this.w.grant)throw Error('Không có grant mock hiện tại');this.paused=false;this.ui.render();}catch(e){this.ui.toast(e.message);}};$('#mode').onclick=()=>this.ui.toast('Chế độ lấy từ hành trình mock; chưa nối lệnh đổi mode UAV');
  $('#pane-next').onclick=()=>{if(this.ui.state.view==='plan')this.ui.setView('preflight');else this.start();};
  $('#confirm-home').onchange=()=>this.confirm('home');$('#confirm-height').onchange=()=>this.confirm('datum');
  $('#confirm-route').onchange=()=>{this.routeConfirmed=$('#confirm-route').checked;this.ui.render();};
  for(const id of ['native-scenario','native-airspace'])$('#'+id).onchange=()=>{this.w.revoke();this.routeConfirmed=false;this.ui.render();};
  $('#review-preview').onclick=()=>this.ui.toast('Ảnh nền minh họa; hồ sơ không chứa ảnh thực');
  $$('.contact-sheet button').forEach(b=>b.onclick=()=>this.ui.toast('Không có media thực đã kiểm trong hồ sơ này'));
  $('#native-export').disabled=nativeTransport;
  $('#native-export').onclick=()=>this.action(async()=>{const raw=await this.w.export();const u=URL.createObjectURL(new Blob([raw],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='aeris-native82-mock-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});
 }
 guardEdit(){if(!this.loaded||this.w.journey.running||this.w.store.blocked||this.w.journey.blocked)throw Error('Nhiệm vụ bị khóa hoặc lưu chưa xác nhận');if(Object.keys(this.ui.state.inputErrors).length)throw Error('Sửa các giá trị nhiệm vụ sai trước');}
 guardControl(){if(!this.ui.canControl())throw Error('Cần quyền bay mẫu của phiên A và kênh mới');}
 edited(){if(!this.loaded||this.busy)return;try{this.guardEdit();this.w.edit(this.form());this.routeConfirmed=false;this.ui.resetConfirmations();}catch(e){this.error=e.message;}this.ui.render();}
 async inspect(){return this.action(async()=>{this.guardControl();await this.w.inspect(this.now(),$('#native-scenario').value,$('#native-airspace').value,()=>this.now());this.routeConfirmed=false;this.ui.resetConfirmations();});}
 async confirm(kind){const el=kind==='home'?$('#confirm-home'):$('#confirm-height'),checked=el.checked;this.pendingConfirmation.set(kind,checked);try{return await this.action(async()=>{this.guardControl();if(checked)await this.w.confirm(kind,this.now());else{this.w.journey[kind]=false;this.w.revoke();this.routeConfirmed=false;}});}finally{this.pendingConfirmation.delete(kind);this.ui.render();}}
 pauseMock(){if(!this.ui.canControl())return;this.paused=true;this.ui.closeReturn(false);this.ui.state.mode='Tạm dừng';this.ui.render();this.ui.toast('Dừng tiến độ quan sát mock; không gửi lệnh UAV');}
 returnPreview(){this.paused=true;this.ui.render();this.ui.toast('Đã duyệt tương tác RTL mẫu; chưa có thực thi RTL. Tiến độ mock tạm dừng.');}
 async start(){return this.action(async()=>{this.guardControl();if(!this.routeConfirmed)throw Error('Xác nhận tuyến trước Fly mock');await this.w.start(this.now(),()=>this.now());this.paused=false;this.ui.setView('fly');this.ui.toast('Đã mở phiên Fly mock có journal; không gửi lệnh UAV');});}
 async background(){this.lifecycleActive=true;this.ui.authorityEvent({kind:'revokeAll'});this.routeConfirmed=false;try{await this.w.background(this.now());}catch(e){this.error='Background commit chưa xác nhận: '+e.message;}this.ui.render();}
 async scenarioChanged(id){if(['link','telemetry','reboot'].includes(id)){this.routeConfirmed=false;this.w.revoke();await this.action(async()=>{if(this.w.journey.bundle&&this.w.journey.running)await this.w.journey.transition('INTERRUPTED_LINK',this.now());});}}
 authorityChanged(){if(this.loaded&&!this.ui.canControl()){this.routeConfirmed=false;this.w.revoke();if(this.w.journey.running&&!this.lifecycleActive){if(this.busy)this.interruptionPending=true;else this.action(()=>this.w.journey.transition('INTERRUPTED_LINK',this.now()));}}}

 paintHUD(){
    if(document.body.dataset.presentation84==='sitl')return;
  $('#telemetry-freshness').textContent='Chưa nối telemetry bay';$('#video-freshness').textContent='Camera minh họa';$('#payload-freshness').textContent='Chưa nối payload';
  $('.satellite').dataset.freshness='unknown';$('.satellite').title='Chưa nối GNSS bay';$('.heading').dataset.freshness='unknown';$('#mode').title='Trạng thái hành trình UI mock, không phải flight mode quan sát';$('#satellite-value').textContent='—';$('.satellite').setAttribute('aria-label','Chưa có GNSS bay thực');$('#heading-value').textContent='—';$('.heading').setAttribute('aria-label','Chưa có heading bay');$('#gimbal-value').textContent='—';$('#gimbal-meta').textContent='Gimbal chưa có nguồn';
  const values={height:this.loaded?String(this.ui.state.mission.altitude):'—',speed:this.loaded?String(this.ui.state.mission.speed):'—',distance:'—',wind:'—'};for(const el of $$('[data-live]'))el.textContent=values[el.dataset.live];
  for(const x of $$('.metric')){x.dataset.freshness='design-only';x.title='Giá trị đặt hoặc chưa có nguồn; không phải telemetry bay';}
  const labels=$$('.metric>span');labels[0].textContent='Độ cao đặt / Home';labels[1].textContent='Tốc độ đặt';labels[2].textContent='Cách Home';labels[3].textContent='Phiên mock';labels[4].textContent='Gió chưa biết';$('#flight-time').textContent='—';
 }
 paintReviewIcon(phase){const v=reviewPresentation(phase,this.loaded);$('.review-lead .check-circle use').setAttribute('href',v.symbol);$('.review-lead .check-circle').dataset.phase=v.state;}
 paint(){
  this.paintReviewIcon(this.w.store.capsule?.journey.current?.phase);
  this.paintHUD();if(!this.loaded){
   $('#native-status').dataset.loaded='false';$('#native-status').dataset.error=String(!!this.error);$('#native-status').textContent=this.error?'Chưa xác nhận journal · bấm Đọc lại journal, không tự ghi lại':'Đang đọc journal · chưa kết luận hồ sơ';
   $('.review-lead h2').textContent='Chưa đọc xong hồ sơ';$('.review-lead p').textContent='Chưa xác nhận trạng thái hoàn tất hoặc thực thi';for(const x of $$('.review-stats strong'))x.textContent='—';$('.contact-heading').hidden=$('.contact-sheet').hidden=true;$('.review-timeline ol').replaceChildren();$('#native-record-list').textContent=this.error?'Cần đọc lại rõ ràng. Bằng chứng cũ được giữ nguyên.':'Đang xác minh journal…';
   for(const id of ['native-save','native-compile','native-inspect','native-start','native-point','native-land','native-ack','pane-next','confirm-home','confirm-height','confirm-route','native-export','native-resume','mission-undo','altitude','altitude-number','speed','speed-number'])$('#'+id).disabled=true;
   for(const k of ['name','vertices','heading','sideOverlap','frontOverlap'])$('#form-'+k).disabled=true;
   for(const id of ['corridor','survey','mission-payload'])$('#'+id).disabled=true;
   $('#pane-title').textContent='Chưa đọc nhiệm vụ';$('#mission-length').textContent='—';$('#mission-detail').textContent='Chưa xác nhận tuyến đã lưu';$('#pane-estimate').textContent='Đọc lại journal trước khi tiếp tục';$('#revision-label').textContent='Chưa xác nhận revision';$('#mission-binding').textContent='Chưa đối chiếu camera nhiệm vụ';$('#mode-name').textContent='Chưa đọc trạng thái';
   for(const k of ['altitude','speed'])for(const d of ['down','up'])$('#'+k+'-'+d).disabled=true;
   $('#native-reload').disabled=this.busy;document.dispatchEvent(new Event('paint84'));return;
  }
  $('#native-status').dataset.loaded='true';
  let s;try{s=this.w.state(this.now());}catch(e){$('#native-status').textContent=e.message;return;}
  if(['plan','review'].includes(this.ui.state.view)&&$('#alert-title').textContent==='Chưa cấp quyền diễn tập'){$('#flight-alert').hidden=true;document.body.dataset.alert='false';}
  const w=this.w,b=w.journey.bundle,a=s.source?.assessment,binding=s.source?.binding,allowed=!!s.source?.allowed;
  const runtimeLabel=nativeTransport?'Native82 · mô phỏng':'Host preview · mô phỏng';const shownPhase=this.ui.state.view==='review'?(s.current?.phase??'Chưa có hồ sơ'):s.phase;
  $('#native-status').textContent=(this.error?'Chưa xác nhận thao tác · '+this.error.slice(0,110):'')||`${runtimeLabel} · ${s.storageBlocked?'Lưu chưa xác nhận':'Journal r'+s.revision} · ${shownPhase}`;
  $('#native-status').dataset.error=String(!!this.error||s.storageBlocked);$('#native-status').dataset.phase=shownPhase;$('#native-status').dataset.revision=String(s.revision);
  $('#mission-binding').textContent=`Camera đang xem: ${this.ui.state.payload==='phase'?'P1 Phase One':this.ui.state.payload==='sony'?'P3 Sony LR1':'P2 nhiệt'} (minh họa). Camera compiler: preset mẫu chưa hiệu chuẩn; chưa dùng profile Phase One/Sony thực.`;
  $('#mission-camera-name').textContent='Camera mẫu chưa hiệu chuẩn';$('#mission-payload').disabled=true;$('#mission-payload').options[0].textContent='Preset camera mẫu · chưa hiệu chuẩn';
  $('#corridor').disabled=true;$('#corridor').title='Compiler hành lang chưa nối ở native82; không thay bằng polygon ngầm';$('#survey').disabled=this.busy||w.journey.running;
  $('#revision-label').textContent=`${w.journey.dirty?'Chưa lưu':'Đã lưu'} · journal r${s.revision}`;
  $('#pane-title').textContent=w.journey.form.name;$('#pane-estimate').textContent=b?`${b.geometry.waypoints.length} điểm · ${b.missionSha256.slice(0,12)} · tổng hợp`:'Lưu khảo sát và compile để có tuyến mới';
  $('#mission-length').textContent=b?b.geometry.waypoints.length+' điểm tuyến':'Chưa compile';$('#mission-detail').textContent='Polygon tổng hợp quanh Home · không terrain thật';
  $('#pf-position').textContent=a?.state??'Chưa có source mới';$('#pf-battery').textContent=allowed?'Profile pin mẫu khớp':'Chưa đối chiếu';$('#pf-wind').textContent='Chưa có nguồn gió thật';
  $('#pf-summary').textContent=allowed?'Profile / Home / tuyến khớp trong mock':'Chưa đủ điều kiện Fly mock';
  $('#pf-subtitle').textContent=b?`Mission ${b.missionSha256.slice(0,12)}`:'Compile khảo sát trước';
  $('#native-proof').textContent=s.source?`Đối chiếu: ${[...(a?.reasons??[]),...(binding?.reasons??[])].map(x=>x.code).join(', ')||'khớp'}; airspace ${w.inspection?.body.airspace.assessment.state??'chưa biết'}. Tham số / nguồn có deadline, không tự gia hạn.`:'Chưa đọc profile trong epoch này; snapshot cũ chỉ xem ở hồ sơ.';
  $('#approval-binding').textContent=`Duyệt gắn mission SHA, Home/datum, profile cohort và epoch ${w.journey.epoch.slice(0,8)}; không lưu quyền.`;
  $('#confirm-home').checked=this.pendingConfirmation.has('home')?this.pendingConfirmation.get('home'):w.journey.home;$('#confirm-height').checked=this.pendingConfirmation.has('datum')?this.pendingConfirmation.get('datum'):w.journey.datum;$('#confirm-route').checked=this.routeConfirmed;
  for(const id of ['confirm-home','confirm-height','confirm-route'])$('#'+id).disabled=this.busy||!allowed||w.journey.running||!this.ui.canControl();
  const count=Number(w.journey.home)+Number(w.journey.datum)+Number(this.routeConfirmed);$('#confirmation-progress').textContent=count+'/3';
  $('#pane-next').textContent=this.ui.state.view==='plan'?'Mở kiểm tra trước bay':'Bắt đầu Fly mock';
  const startable=s.ready&&this.routeConfirmed&&this.ui.canControl()&&!this.busy;
  $('#pane-next').disabled=this.ui.state.view==='preflight'?!startable:!b||this.busy;
  $('#native-start').disabled=!startable;$('#native-start').hidden=this.ui.state.view!=='fly'||w.journey.running;
  $('#native-inspect').disabled=this.busy||!b||w.journey.running||s.storageBlocked||!this.ui.canControl();
  for(const id of ['native-save','native-compile'])$('#'+id).disabled=this.busy||w.journey.running||s.storageBlocked||Object.keys(this.ui.state.inputErrors).length>0;
  $('#native-reload').disabled=this.busy;
  for(const k of ['name','vertices','heading','sideOverlap','frontOverlap'])$('#form-'+k).disabled=this.busy||w.journey.running||s.storageBlocked;
  for(const k of ['altitude','speed']){const locked=this.busy||w.journey.running||s.storageBlocked,invalid=Object.keys(this.ui.state.inputErrors).length>0;$('#'+k+'-number').disabled=locked;for(const [d,limit]of [['down',ADJUSTMENTS[k].min],['up',ADJUSTMENTS[k].max]])$('#'+k+'-'+d).disabled=locked||invalid||this.ui.state.mission[k]===limit;}
  $('#mission-undo').disabled=this.busy||w.journey.running||s.storageBlocked||this.ui.state.mission.undo.length===0;
  $('#native-resume').hidden=!this.paused||!w.journey.running;$('#native-resume').disabled=this.busy||!s.grant||!this.ui.canControl();$('#native-point').disabled=this.paused||this.busy||s.phase!=='RUNNING_MOCK'||!s.grant||!this.ui.canControl();
  $('#native-land').disabled=this.paused||this.busy||s.phase!=='AWAITING_MOCK_LANDING'||!s.grant||!this.ui.canControl();
  $('#native-ack').disabled=this.busy||s.phase!=='RUNNING_MOCK'||!s.grant;
  $('#native-progress').textContent=w.journey.running?`${this.paused?'Tạm dừng · ':''}${s.cursor} / ${b?.geometry.waypoints.length??0} điểm quan sát · ${s.phase}`:'Chưa có phiên Fly mock đang chạy';
  $('#native-fly-controls').hidden=this.ui.state.view!=='fly';
  // Native review uses the validated capsule, not the concept's static completion/photographs.
  const cap=w.store.capsule,records=[...(cap?.journey.history??[]),...(cap?.journey.current?[cap.journey.current]:[])];
  $('#native-record-list').replaceChildren(...records.slice().reverse().map(record=>{const article=document.createElement('article'),h=document.createElement('h3'),p=document.createElement('p');h.textContent=record.missionForm.name;p.textContent=`${record.phase} · ${record.cursor} điểm · ${record.missionSha256.slice(0,16)}`;article.append(h,p);return article;}));
  if(!records.length)$('#native-record-list').textContent='Chưa có hồ sơ đã xác nhận lưu.';
  const current=cap?.journey.current;$('#review-panel h1').textContent=current?.missionForm.name??w.journey.form.name;
  $('.review-lead h2').textContent=current?.phase==='COMPLETED_MOCK'?'Hoàn tất mock có hồ sơ':current?.phase.startsWith('INTERRUPTED')?'Phiên mock gián đoạn':'Chưa có nhiệm vụ hoàn tất';
  $('.review-lead p').textContent='Replay capsule và chuỗi sự kiện · không có bằng chứng bay thực';
  const stats=$$('.review-stats strong');stats[0].textContent=String(current?.events.length??0);stats[1].textContent=String(current?.cursor??0);stats[2].textContent='0';
  const labels=$$('.review-stats span');labels[0].textContent='Sự kiện đã lưu';labels[1].textContent='Điểm quan sát mock';labels[2].textContent='Ảnh thực đã kiểm';
  $('.contact-heading').hidden=$('.contact-sheet').hidden=true;$('.review-actions>span').textContent='Không có media thực; ảnh nền chỉ minh họa.';
  $('.review-panel>header p').textContent=`Journal r${s.revision} · ${cap?.preflightSnapshots.length??0} snapshot preflight · operational=false`;
  $('#history-context span').textContent=`${current?.phase??'Chưa có hồ sơ'} · lịch sử; không phải telemetry hiện tại`;
  $('.review-timeline ol').replaceChildren(...(current?.events??[]).slice(-10).map(e=>{const li=document.createElement('li'),t=document.createElement('b'),d=document.createElement('span');t.textContent=e.body.elapsedMs+' ms';d.textContent=e.body.kind;li.append(t,d);return li;}));
  $('.review-timeline p').textContent='Sự kiện mock đã semantic replay; ACK không xác nhận tiến độ.';
  $('#native-export').disabled=nativeTransport||!cap||s.storageBlocked||this.busy;
  $('#mode-name').textContent=w.journey.running?(this.paused?'Tạm dừng mock':'Fly mock'):s.current?.phase==='COMPLETED_MOCK'?'Đã đóng mock':'Chưa chạy mock';if(b)this.draw(b,s.cursor);document.dispatchEvent(new Event('paint84'));
 }
 draw(bundle,cursor){
  const group=$('#native-route'),ns='http://www.w3.org/2000/svg',f=localFrame(bundle.geometry.origin);
  const points=bundle.geometry.waypoints.map(p=>f.forward(f.reverse(p)));const bound=Math.max(10,...points.flatMap(p=>[Math.abs(p.x),Math.abs(p.y)]))*1.4;
  const project=p=>({x:780+p.x/bound*120,y:430-p.y/bound*120});group.replaceChildren();
  const line=document.createElementNS(ns,'polyline');line.setAttribute('points',points.map(project).map(p=>p.x+','+p.y).join(' '));line.setAttribute('fill','none');line.setAttribute('stroke','#ffe27a');line.setAttribute('stroke-width','3');group.append(line);
  points.forEach((point,i)=>{const p=project(point),c=document.createElementNS(ns,'circle');c.setAttribute('cx',p.x);c.setAttribute('cy',p.y);c.setAttribute('r','7');c.setAttribute('fill',i<cursor?'#fff':'#ffe27a');c.setAttribute('stroke','#111');c.setAttribute('stroke-width','2');group.append(c);});
 }
}
