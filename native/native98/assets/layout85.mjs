// UI coordination only. No storage, source identity, permission, timing or flight changes.
const panel=document.querySelector('#panel83');let panelOpener=null;
function closePanel(){panel.hidden=true;if(panelOpener?.isConnected)panelOpener.focus();}
document.addEventListener('click',e=>{
 const b=e.target.closest('button,a');if(!b)return;
 if(b.closest('.topbar,.navrail')&&!b.closest('#panel83')){if(!panel.hidden)panel.hidden=true;}
 if(['open-workspace83','open-sitl83','ops84'].includes(b.id)){
  panelOpener=b;
  if(!document.querySelector('#sheet').hidden)document.querySelector('#sheet-close').click();
  if(!document.querySelector('#return-backdrop').hidden)document.querySelector('#cancel-return').click();
 }
},true);
panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','false');panel.setAttribute('aria-labelledby','title83');
new MutationObserver(()=>{if(!panel.hidden)document.querySelector('#close83').focus();}).observe(panel,{attributes:true,attributeFilter:['hidden']});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!panel.hidden){e.preventDefault();e.stopImmediatePropagation();closePanel();}},true);
document.querySelector('#close83').addEventListener('click',()=>{if(panelOpener?.isConnected)panelOpener.focus();});
for(const [selector,label]of [['.sheet-content','Nội dung bảng tùy chọn'],['.pane-scroll','Nội dung nhiệm vụ'],['.review-body','Nội dung hồ sơ'],['#workspace83','Nội dung workspace'],['#plan83','Nội dung khảo sát SITL'],['#live83','Nội dung preflight SITL'],['#review83','Nội dung review SITL'],['#records84','Danh sách hồ sơ đã lưu'],['#record84','Chi tiết hồ sơ đã lưu']]){
 for(const e of document.querySelectorAll(selector)){e.tabIndex=0;e.setAttribute('aria-label',label);}
}

if(document.body.dataset.qa85==='browser'&&document.querySelector('#history84')){
 document.querySelector('#history84 header small').textContent='Bản sao hồ sơ đã lưu · chỉ đọc kiểm UI';
 document.querySelector('#history84 h1').textContent='Lịch sử SITL · NATIVE84';
}
const paneTitle=document.querySelector('#pane-title');
const labelTitle=()=>paneTitle.title=paneTitle.textContent;
new MutationObserver(labelTitle).observe(paneTitle,{childList:true,characterData:true,subtree:true});labelTitle();
