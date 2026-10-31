import {PayloadSession} from './core.mjs';
import {SimulatorAdapter,discoverFixtures} from './simulator.mjs';
import {PAYLOADS} from './fixtures.mjs';
const $=id=>document.getElementById(id),adapter=new SimulatorAdapter();
const model=new PayloadSession({adapter,sessionId:`sim-${Math.floor(Date.now()/1000)}`});model.connect();discoverFixtures(model);
const stateLabels={REQUESTED:'Đã gửi yêu cầu mô phỏng',ACK_ACCEPTED:'ACK chấp nhận · chưa có quan sát thực thi',OBSERVED_SIMULATION:'Đã quan sát phản hồi mô phỏng',REJECTED:'Lệnh bị từ chối',UNKNOWN:'Kết quả chưa xác định · không tự gửi lại',TIMED_OUT_UNCERTAIN:'Hết hạn · kết quả chưa xác định'};
const action=(fn)=>{try{fn();$('message').textContent='';}catch(e){$('message').textContent=e.message;}render();};
function selected(){const s=model.snapshot();return s.payloads.find(p=>p.id===s.selected);}
function command(operation,args={}){action(()=>model.command(selected().id,operation,args));setTimeout(()=>{adapter.step();render();},500);}
for(const p of PAYLOADS){const b=document.createElement('button');b.className='payload-choice';b.dataset.payload=p.id;b.append(document.createTextNode(p.label),document.createElement('span'));b.onclick=()=>action(()=>model.select(p.id));$('payload-selector').append(b);}
$('acquire').onclick=()=>action(()=>model.authority(selected().id,'operator'));
$('release').onclick=()=>action(()=>model.authority(selected().id,'none'));
$('capture').onclick=()=>command('capture');
$('set-zoom').onclick=()=>command('zoom',{value:Number($('zoom').value)});
$('focus').onclick=()=>command('focus',{value:'auto'});
$('set-gimbal').onclick=()=>command('gimbal',{pitchDeg:Number($('pitch').value),yawDeg:Number($('yaw').value)});
$('nadir').onclick=()=>command('gimbal',{pitchDeg:-90,yawDeg:0});
$('stream-select').onchange=()=>action(()=>model.stream(selected().id,$('stream-select').value));
$('zoom').oninput=()=>$('zoom-value').textContent=`${$('zoom').value}× / yêu cầu`;
$('video-fault').onclick=()=>action(()=>{const p=selected();model.fault(p.id,'video',p.stream.live);});
$('gimbal-fault').onclick=()=>action(()=>{const p=selected();model.fault(p.id,'gimbal',!p.gimbalFault);});
$('payload-loss').onclick=()=>action(()=>model.fault(selected().id,'link'));
$('rediscover').onclick=()=>action(()=>model.discover(PAYLOADS.find(p=>p.id===selected().id)));
$('mission-authority').onclick=()=>action(()=>model.authority(selected().id,'mission'));
$('reply-mode').onchange=()=>adapter.fault=$('reply-mode').value;
$('aircraft-toggle').onclick=()=>action(()=>{if(model.snapshot().link)model.disconnect();else{model.connect();discoverFixtures(model);}});
$('export').onclick=async()=>{const bytes=new TextEncoder().encode(JSON.stringify(model.review(),null,2)+'\n'),digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(n=>n.toString(16).padStart(2,'0')).join('');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([bytes],{type:'application/json'}));a.download=`aeris-payload21-SIMULATION-${digest.slice(0,12)}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);$('message').textContent=`Đã xuất review mô phỏng · SHA-256 ${digest}`;};
for(const name of ['fly','matrix'])$(name+'-tab').onclick=()=>{$('fly-view').hidden=name!=='fly';$('matrix-view').hidden=name!=='matrix';for(const other of ['fly','matrix'])if(other===name)$(other+'-tab').setAttribute('aria-current','page');else $(other+'-tab').removeAttribute('aria-current');if(name==='fly')render();};
let viewKey='';
function render(){
  const s=model.snapshot(),p=s.payloads.find(p=>p.id===s.selected);
  $('aircraft-mode').textContent=s.link?'HOLD / mô phỏng':'Mất liên kết';$('altitude').textContent=s.link?'42 m':'—';$('session').textContent=s.sessionId;
  $('aircraft-toggle').textContent=s.link?'Ngắt liên kết mô phỏng':'Kết nối lại mô phỏng';
  $('active-label').textContent=p.label;$('feed-status').textContent=p.frameFresh?'Luồng tổng hợp đang hoạt động':'Luồng không còn mới';
  const r=p.route;$('route-label').textContent=r.camera.kind==='proxy'?`SYS ${r.systemId} / proxy ${r.camera.deviceId}`:`SYS ${r.systemId} / CAM ${r.camera.componentId}`;
  $('feed-warning').hidden=p.frameFresh;$('feed-warning').textContent=p.connected?'Mất luồng tổng hợp':'Mất liên kết payload';
  for(const b of $('payload-selector').children){const q=s.payloads.find(p=>p.id===b.dataset.payload);b.setAttribute('aria-pressed',String(q.id===p.id));b.querySelector('span').textContent=!q.connected?'Mất liên kết':!q.frameFresh?'Mất luồng':q.gimbalFault?'Lỗi gimbal':'Sẵn sàng mô phỏng';}
  $('authority-status').textContent=p.authorityFresh&&p.authority?.owner==='operator'?'Người vận hành đang có quyền':p.authority?.owner==='mission'?'Mission đang có quyền':'Chưa nhận quyền / quyền hết hạn';
  $('acquire').disabled=!s.link||!p.controlFresh||p.authorityFresh&&p.authority?.owner==='operator';$('release').disabled=!s.link||!p.controlFresh||!p.authority;
  if(viewKey!==p.id){viewKey=p.id;$('stream-select').replaceChildren();for(const stream of p.streams){const o=document.createElement('option');o.value=stream.id;o.textContent=stream.type==='thermal'?'Nhiệt tổng hợp':stream.type==='survey'?'Khảo sát tổng hợp':'Màu tổng hợp';$('stream-select').append(o);}if(p.capabilities.zoom){$('zoom').min=p.capabilities.zoomRange[0];$('zoom').max=p.capabilities.zoomRange[1];$('zoom').value=p.settings.zoom;}$('pitch').value=-45;$('yaw').value=0;}
  $('stream-select').value=p.stream.id;$('stream-select').disabled=!p.connected;
  for(const [el,op]of [['capture','capture'],['set-zoom','zoom'],['focus','focus'],['set-gimbal','gimbal'],['nadir','gimbal']]){$(el).disabled=!!model.eligible(p.id,op);$(el).title=model.eligible(p.id,op)||'Thử lệnh mô phỏng';}
  $('zoom').disabled=!p.capabilities.zoom;$('pitch').disabled=$('yaw').disabled=!p.capabilities.gimbal;
  if(p.capabilities.gimbal){$('pitch').min=p.capabilities.pitchRange[0];$('pitch').max=p.capabilities.pitchRange[1];$('yaw').min=p.capabilities.yawRange[0];$('yaw').max=p.capabilities.yawRange[1];}
  $('zoom-value').textContent=p.settings.zoom?`${p.settings.zoom}× / phản hồi`:'Không hỗ trợ';
  $('capture-count').textContent=`${p.captureReceipts} capture receipt tổng hợp · 0 ảnh thật`;
  $('gimbal-state').textContent=!p.capabilities.gimbal?'Không có gimbal':p.gimbalFault?'Đang lỗi':'Sẵn sàng mô phỏng';
  $('gimbal-fault').disabled=!p.capabilities.gimbal;$('rediscover').disabled=p.discovered||!s.link;
  $('angles').textContent=p.capabilities.gimbal?`Góc phản hồi ${p.settings.pitchDeg}° / ${p.settings.yawDeg}°`:'Góc phản hồi —';
  const c=s.commands.filter(c=>c.payloadId===p.id&&c.sessionId===s.sessionId&&c.discoveryId===p.discoveryId).at(-1);$('command-state').textContent=c?`${c.id} / ${c.operation}: ${stateLabels[c.state]}`:'Phiên khám phá hiện tại chưa có lệnh. Nhận quyền để thử thao tác.';
  const interesting=s.events.filter(e=>!['VIEW_SELECTED'].includes(e.type)).slice(-6).reverse();$('journal').replaceChildren(...interesting.map(e=>{const li=document.createElement('li');li.textContent=`${(e.atMs/1000).toFixed(1)}s · ${e.payloadId||e.command?.payloadId||'máy bay'} · ${eventText(e)}`;return li;}));
  draw(p);
}
function eventText(e){const labels={DISCOVERED:'Khám phá cấu hình tổng hợp',AIRCRAFT_CONNECTED:'Kết nối mô phỏng',AIRCRAFT_DISCONNECTED:'Ngắt liên kết; không tự khôi phục lệnh',AUTHORITY_OBSERVED:'Quyền điều khiển đã phản hồi',COMMAND_REQUESTED:'Yêu cầu mô phỏng',COMMAND_ACK:'ACK',COMMAND_OBSERVED_SIMULATION:'Quan sát phản hồi mô phỏng',COMMAND_TIMEOUT:'Hết hạn; kết quả chưa xác định',COMMAND_UNCERTAIN:'Kết quả chưa xác định',STREAM_SELECTED:'Chọn luồng',FAULT:'Tình huống lỗi',FEEDBACK_IGNORED:'Bỏ qua phản hồi không hợp lệ'};return `${labels[e.type]||e.type} ${e.result||e.owner||e.reason||e.command?.operation||e.faultType||''}`;}
function draw(p){const canvas=$('scene'),width=canvas.clientWidth,height=canvas.clientHeight;if(!width||!height)return;const dpr=Math.min(devicePixelRatio,2);canvas.width=width*dpr;canvas.height=height*dpr;const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);const thermal=p.streams.find(s=>s.id===p.stream.id).type==='thermal';ctx.fillStyle=thermal?'#201b23':'#20272c';ctx.fillRect(0,0,width,height);ctx.save();ctx.translate(width/2,height/2);ctx.rotate((p.settings.yawDeg||0)*Math.PI/180);const scale=p.settings.zoom||1;ctx.scale(Math.sqrt(scale),Math.sqrt(scale));ctx.strokeStyle=thermal?'#735963':'#56616b';ctx.lineWidth=1;for(let x=-width;x<=width;x+=50){ctx.beginPath();ctx.moveTo(x,-height);ctx.lineTo(x,height);ctx.stroke();}for(let y=-height;y<=height;y+=50){ctx.beginPath();ctx.moveTo(-width,y);ctx.lineTo(width,y);ctx.stroke();}ctx.fillStyle=thermal?'#976851':'#73807c';ctx.fillRect(-150,-90,200,65);ctx.fillStyle=thermal?'#b38b62':'#91958b';ctx.fillRect(80,-20,90,110);ctx.strokeStyle='#c7ced6';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(-width,100);ctx.lineTo(width,-100);ctx.stroke();ctx.restore();ctx.fillStyle='#fff';ctx.font='13px Plex, Arial';ctx.fillText(`${p.stream.id} / synthetic`,16,24);}
setInterval(()=>{const s=model.snapshot();for(const p of s.payloads)if(s.link&&p.connected){model.heartbeat(p.id);model.frame(p.id);if(p.authority)model.authority(p.id,p.authority.owner);}render();},1000);
window.addEventListener('resize',render);render();
fetch('/matrix.json').then(r=>{if(!r.ok)throw Error('Matrix unavailable');return r.json();}).then(matrix=>{for(const row of matrix.rows){const tr=document.createElement('tr');for(const k of ['workflow','ragas','aeris','missing']){const td=document.createElement('td');td.textContent=row[k];tr.append(td);}$('matrix-rows').append(tr);}const a=document.createElement('a');a.href=matrix.sourceURL;a.textContent='Nguồn công bố RAGAS';a.target='_blank';a.rel='noopener';$('matrix-sources').append(a,document.createTextNode(` · Bản chụp ${matrix.capturedAt} · RAGAS runtime/A/B: NOT_CHECKED`));}).catch(e=>$('matrix-sources').textContent=e.message);
