// Native compatibility and self-observed render diagnostics; no command/authority or source fixture injection.
const body=document.body,panel=document.querySelector('#panel83'),video=document.querySelector('#video-warning');
const supports={has:CSS.supports('selector(:has(*))'),backdrop:CSS.supports('backdrop-filter','blur(1px)'),webkitBackdrop:CSS.supports('-webkit-backdrop-filter','blur(1px)'),grid:CSS.supports('display','grid')};
body.dataset.glass86=supports.backdrop||supports.webkitBackdrop?'blur-supported':'translucent-fallback';
const env=JSON.parse(window.Native82Bridge.environment86());
const info=document.createElement('p');info.id='environment86';info.textContent=`CREW02 engineering · Android ${env.sdk} · WebView ${env.webview}\nGiao diện: ${supports.has?':has hỗ trợ':'tương thích state mirror'} · ${body.dataset.glass86}\nNguồn ${env.source} · ${env.hasHostToken?'token host được cấp có chủ ý':'chưa có token host'} · không có video hoặc UAV thật.`;document.querySelector('#workspace83').prepend(info);
function mirror(){body.dataset.panel86=String(!panel.hidden);body.dataset.video86=String(!video.hidden);}
const observer=new MutationObserver(mirror);observer.observe(panel,{attributes:true,attributeFilter:['hidden']});observer.observe(video,{attributes:true,attributeFilter:['hidden']});mirror();
window.native86Insets=(height,ime)=>{body.dataset.ime86=String(ime);if(ime)setTimeout(()=>document.activeElement?.scrollIntoView({block:'center',inline:'nearest'}),120);schedule();};
let scheduled=false,last='',count=0,forceCapture96=false,lastSample96=-1;
function schedule(force=false){forceCapture96 ||= force===true;const now=performance.now();if(scheduled||!forceCapture96&&now-lastSample96<250)return;scheduled=true;requestAnimationFrame(()=>requestAnimationFrame(()=>{scheduled=false;const forced=forceCapture96;forceCapture96=false;lastSample96=performance.now();capture(forced);}));}
function capture(forced=false){
 if(count>=2048||document.hidden)return;
 const visible=e=>{if(!e)return false;const s=getComputedStyle(e),r=e.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0&&(!e.closest('details:not([open])')||e.closest('summary'));};
 const box=s=>{const e=document.querySelector(s);if(!visible(e))return null;const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom};};
 const boxes=Object.fromEntries(['.brand b','.metric:first-child>span','.topbar','.telemetry','.navrail','.camera-tools','#task-pane','#sheet','#return-backdrop','#review-panel','#panel83','.native-status','.pane-action','.pane-scroll','.pane-heading','#diagnostics90','#source90','#local-video90'].map(s=>[s,box(s)]));
 const active=['#diagnostics90','#panel83','#sheet','#return-backdrop','#review-panel','#task-pane'].find(s=>visible(document.querySelector(s)));
 const controls=[];for(const e of document.querySelectorAll('button,input,select,textarea,summary')){
  if(!visible(e)||['#panel83','#sheet','#return-backdrop','#diagnostics90','#review-panel'].includes(active)&&!document.querySelector(active).contains(e))continue;const r=e.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2;if(x<0||y<0||x>=innerWidth||y>=innerHeight)continue;
  let inClip=true;for(let p=e.parentElement;p;p=p.parentElement){const s=getComputedStyle(p),b=p.getBoundingClientRect();if(/auto|scroll|hidden|clip/.test(s.overflow+s.overflowX+s.overflowY)&&(x<b.left||x>b.right||y<b.top||y>b.bottom)){inClip=false;break;}}if(!inClip)continue;
  const t=document.elementFromPoint(x,y),owner=e.closest('.pane-scroll'),clip=owner?.getBoundingClientRect(),inOwnViewport=!clip||(y>=clip.top&&y<=clip.bottom);controls.push({x:r.x,y:r.y,right:r.right,bottom:r.bottom,inOwnViewport,id:e.id||e.getAttribute('aria-label')||e.textContent.trim().slice(0,64),width:r.width,height:r.height,disabled:e.disabled===true,covered:!(t===e||e.contains(t)),inPanel:active?document.querySelector(active).contains(e):false,type:e.type??'',textOverflow:e.scrollHeight>e.clientHeight+1});
 }
 const a=boxes['.brand b'],b=boxes['.metric:first-child>span'];
 const data={format:'aeris-native86-self-observed-ui',version:1,provenance:'RENDERER_SELF_REPORT_NOT_ATTESTATION',viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},theme:body.dataset.theme,view:body.dataset.view,panel:active??null,sheetTitle:document.querySelector('#sheet-title').textContent,scenario:body.dataset.scenario,overlay:body.dataset.panel86,video:body.dataset.video86,glass:body.dataset.glass86,ime:body.dataset.ime86==='true',supports,themeIcon:document.querySelector('#theme use').getAttribute('href'),alignmentDelta:a&&b?Math.abs(a.x-b.x):null,boxes,controls,sourceStatus:document.querySelector('#native-status').textContent,mission:document.querySelector('#pane-title').textContent};
 const key=JSON.stringify(data);if(key===last&&!forced)return;last=key;count++;window.Native82Bridge.reportUI86(JSON.stringify({...data,rendererElapsedMs:performance.now()}));
}
document.addEventListener('click',()=>schedule(true));document.addEventListener('change',()=>schedule(true));document.addEventListener('scroll',()=>schedule(true),true);window.addEventListener('resize',()=>schedule(true));document.addEventListener('visibilitychange',()=>schedule(true));document.fonts.ready.then(schedule);schedule();
