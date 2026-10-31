/** Layout/touch preview only. No bridge, storage, aircraft, mission or persistence implementation. */
import'./phone06.mjs';
const $=s=>document.querySelector(s),unsupported=['admit','export-key','import-trust','observer','profile','loiter','enable','hold','rtl','land'];
function lock(){for(const id of unsupported){const b=$('#phone06-'+id);if(b){if(!b.disabled)b.disabled=true;b.title='Chỉ dùng trong ứng dụng Android native';}}}
function view(name){document.body.dataset.view=name;for(const b of document.querySelectorAll('.nav-item[data-view]')){b.classList.toggle('active',b.dataset.view===name);b.setAttribute('aria-current',b.dataset.view===name?'page':'false');}$('#task-pane').hidden=name!=='plan';$('#review-panel').hidden=true;window.phone06.render();lock();}
for(const b of document.querySelectorAll('.nav-item[data-view]'))b.onclick=()=>view(b.dataset.view);
$('#theme').onclick=()=>{const night=document.body.dataset.theme!=='night';document.body.dataset.theme=night?'night':'day';$('#theme use').setAttribute('href',night?'#i-moon':'#i-sun');$('#theme').setAttribute('aria-pressed',String(night));$('#theme').setAttribute('aria-label',night?'Chuyển sang giao diện ngày':'Chuyển sang giao diện đêm');};
for(const e of document.querySelectorAll('[data-live],#flight-time,#satellite-value,#battery-value'))e.textContent='—';
for(const b of document.querySelectorAll('button'))if(!b.matches('#theme,#phone06-open,#phone06-close,#phone06-rehearse,.nav-item[data-view]'))b.disabled=true;
for(const [id,label]of [['telemetry-freshness','Telemetry UNKNOWN · preview'],['video-freshness','Không có video · preview'],['payload-freshness','Payload UNKNOWN · preview']])$('#'+id).textContent=label;
$('#link-label').textContent='PREVIEW';for(const e of document.querySelectorAll('.status-dot'))e.style.visibility='hidden';
$('#native-status').textContent='PREVIEW · Chỉ bố cục và rèn cần offline · không telemetry, nhiệm vụ, storage hoặc lệnh bay';$('#native-status').hidden=false;
document.addEventListener('click',e=>{if(unsupported.some(id=>e.target.closest('#phone06-'+id))){e.preventDefault();e.stopImmediatePropagation();}},true);
new MutationObserver(lock).observe($('#phone06-panel'),{attributes:true,subtree:true,attributeFilter:['disabled']});lock();view('fly');
