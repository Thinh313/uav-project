/** FIELD01 host-only media controls. All DOM mutations stay inside container. */
export async function mountMediaPanel({container,mediaOrigin='http://127.0.0.1:8871',onCapture,onState=()=>{}}={}) {
  if (!container) throw Error('MEDIA_PANEL_CONTAINER_REQUIRED');
  const parsed=new URL(mediaOrigin);
  if(parsed.hostname!=='127.0.0.1'||parsed.protocol!=='http:'||parsed.pathname!=='/')throw Error('LOOPBACK_MEDIA_ORIGIN_REQUIRED');
  mediaOrigin=parsed.origin;
  const {createViewer}=await import(mediaOrigin+'/viewer.mjs');
  const panel=document.createElement('section');panel.className='field-media-panel';panel.setAttribute('aria-label','Video FIELD01 qua localhost');
  panel.innerHTML=`
    <header class="fmp-heading"><div><h2>Hình ảnh tổng hợp</h2><p>Nguồn độc lập, truyền qua localhost</p></div><span class="fmp-status" data-fmp="freshness">Chưa có khung</span></header>
    <div class="fmp-viewport"><div class="fmp-decoded" data-fmp="decoded"></div><div class="fmp-empty" data-fmp="empty"><strong>Chưa nhận video</strong><span>Chọn nguồn, bắt đầu nguồn rồi mở viewer.</span></div><figure class="fmp-source"><iframe data-fmp="publisher" title="Nguồn video tổng hợp độc lập, chỉ bắt đầu khi chọn" allow="autoplay 'none'"></iframe><figcaption>Nguồn độc lập</figcaption></figure><span class="fmp-feed" data-fmp="feed-label">RGB tổng hợp</span></div>
    <div class="fmp-configuration"><label>Nguồn<select data-fmp="feed"><option value="rgb">RGB tổng hợp</option><option value="thermal">Thermal-look, không đo nhiệt</option></select></label><label>Codec<select data-fmp="profile"><option value="H264-720P30-V1">H264 · 720p30</option><option value="VP8-720P30-V1">VP8 · fallback chọn rõ</option></select></label></div>
    <div class="fmp-source-actions"><button type="button" data-fmp="source-start" class="fmp-primary" disabled>Bắt đầu nguồn</button><button type="button" data-fmp="source-stop" disabled>Dừng nguồn</button><button type="button" data-fmp="viewer-start">Mở viewer</button><button type="button" data-fmp="viewer-stop" disabled>Dừng viewer</button></div>
    <div class="fmp-actions"><button type="button" data-fmp="measure" disabled>Đo foreground 30 giây</button><button type="button" data-fmp="pause" disabled>Ngắt relay 500 ms</button><button type="button" data-fmp="save" disabled>Lưu báo cáo</button><button type="button" data-fmp="capture" class="fmp-primary" disabled>Chụp khung đang xem</button></div>
    <output class="fmp-notice" data-fmp="notice" role="status">Đang kết nối nguồn độc lập…</output>
    <details class="fmp-diagnostics"><summary>Kết quả và phạm vi đo</summary><dl><div><dt>Tốc độ hiển thị</dt><dd data-fmp="fps">Chưa đo</dd></div><div><dt>P95 nguồn → canvas</dt><dd data-fmp="latency">UNKNOWN</dd></div><div><dt>Phục hồi keyframe</dt><dd data-fmp="recovery">Chưa đo</dd></div></dl><p data-fmp="counts">Nguồn / encoded / published / decoded: chưa có dữ liệu</p><p>Đồng hồ nguồn và viewer được hiệu chuẩn theo khoảng sai số của host. Số liệu chỉ tới lệnh vẽ canvas, không đo độ trễ vật lý. Backend codec chưa biết.</p></details>
    <p class="fmp-scope">HOST · nguồn RGB / thermal-look tổng hợp. Không có camera thực, đo nhiệt hay xác nhận Android.</p>`;
  container.append(panel);
  const $=name=>panel.querySelector(`[data-fmp="${name}"]`),iframe=$('publisher');
  const setup=document.createElement('details');setup.className='fmp-setup';const setupTitle=document.createElement('summary');setupTitle.textContent='Nguồn, viewer và kết quả đo';setup.append(setupTitle);const setupBody=document.createElement('div');setupBody.className='fmp-setup-body';setupBody.append(panel.querySelector('.fmp-configuration'),panel.querySelector('.fmp-source-actions'),panel.querySelector('.fmp-diagnostics'));setup.append(setupBody);panel.insertBefore(setup,panel.querySelector('.fmp-scope'));
  function fullyVisible(element){if(!element?.isConnected||document.hidden)return false;const r=element.getBoundingClientRect();if(r.width<20||r.height<20||r.top<0||r.left<0||r.right>innerWidth+1||r.bottom>innerHeight+1)return false;for(let ancestor=element;ancestor;ancestor=ancestor.parentElement){const css=getComputedStyle(ancestor);if(css.display==='none'||css.visibility==='hidden'||Number(css.opacity)===0)return false;if(ancestor!==element&&[css.overflowX,css.overflowY].some(value=>['auto','scroll','hidden','clip'].includes(value))){const a=ancestor.getBoundingClientRect();if(r.left<a.left-1||r.right>a.right+1||r.top<a.top-1||r.bottom>a.bottom+1)return false;}}return true;}
  function visualCheck(){return fullyVisible(iframe)&&fullyVisible($('decoded').querySelector('canvas'));}
  let closed=false,busy=false,sourceReady=false,sourceActive=false,sourcePending=false,sourceStatus=null,viewerState=null,measuring=false,report=null,saved=null,measurementEnd=0,lastMessage='Đang kết nối nguồn độc lập…';
  function notify(){try{onState(state());}catch{}}
  function notice(message,error=false){lastMessage=message;$('notice').textContent=message;$('notice').dataset.error=String(error);notify();}
  function state(){return{sourceReady,sourceActive,sourcePending,source:sourceStatus?structuredClone(sourceStatus):null,viewer:viewerState?structuredClone(viewerState):null,measuring,report:report?structuredClone(report):null,saved:saved?{...saved}:null,message:lastMessage,closed,sourceKind:'SYNTHETIC',physicalLatency:'NOT_MEASURED',actualImages:0};}
  function render(){if(closed)return;const active=!!viewerState?.active,preview=viewer.getPreview(),available=!!preview;
    $('source-start').disabled=busy||sourcePending||!sourceReady||sourceActive;$('source-stop').disabled=busy||sourcePending||!sourceActive;
    $('feed').disabled=busy||sourceActive;$('profile').disabled=busy||sourceActive;
    $('viewer-start').disabled=busy||active;$('viewer-stop').disabled=busy||!active;
    $('measure').disabled=busy||!available||measuring;$('pause').disabled=busy||!available;
    $('save').disabled=busy||!report;$('capture').disabled=busy||!available||typeof onCapture!=='function';
    $('empty').hidden=available;$('freshness').textContent=available?Math.round(preview.ageMs)+' ms · tổng hợp':active?'Đang chờ khung':'Chưa có khung';$('freshness').dataset.fresh=String(available);
    $('feed-label').textContent=(viewerState?.session?.feed??$('feed').value)==='thermal'?'Thermal-look · không đo nhiệt':'RGB tổng hợp';
    $('measure').textContent=measuring?'Đang đo · '+Math.max(0,Math.ceil((measurementEnd-performance.now())/1000))+' giây':'Đo foreground 30 giây';
    const source=sourceStatus?.counts,c=viewerState?.counters;$('counts').textContent='Nguồn / encoded / published / decoded: '+(source?[source.source,source.encoded,source.published,c?.decoded??0].join(' / '):'chưa có dữ liệu')+(source?' · bỏ nguồn '+source.sourceDrops+', bỏ output '+source.outputDrops+', bỏ viewer '+(c?.consumerDrops??0):'');
    if(report){$('fps').textContent=report.displayedFps.toFixed(1)+' fps';$('latency').textContent=report.latencyStatus==='CALIBRATED_BOUNDS'&&Number.isFinite(report.latencyP95UpperMs)?'≤ '+report.latencyP95UpperMs.toFixed(1)+' ms (cận trên)':'UNKNOWN';const recovered=report.faultWindows.filter(f=>Number.isFinite(f.recoveryMs));$('recovery').textContent=recovered.length?recovered.at(-1).recoveryMs.toFixed(0)+' ms':report.faultWindows.length?'Chưa phục hồi':'Chưa đo';}
  }
  const viewer=createViewer({container:$('decoded'),baseUrl:mediaOrigin,isVisuallyVisible:visualCheck,onState:update=>{viewerState=update;if(update.report){report=update.report;measuring=false;notice('Đã đo '+(report.durationMs/1000).toFixed(1)+' giây; '+(report.engineeringGate.coverage?'đủ khoảng foreground.':'khoảng đo chưa hợp lệ.'));}else if(update.error)notice('Viewer: '+update.error,true);render();notify();}});
  async function action(fn){if(closed||busy)return;busy=true;render();try{return await fn();}catch(error){notice(error.message??String(error),true);}finally{busy=false;render();}}
  function command(value){iframe.contentWindow.postMessage(value,mediaOrigin);}
  function sourceMessage(event){if(closed||event.origin!==mediaOrigin||event.source!==iframe.contentWindow||event.data?.type!=='FIELD01_SOURCE_STATUS')return;sourceStatus=event.data;sourceReady=true;sourcePending=false;sourceActive=event.data.active===true;if(sourceActive&&event.data.session?.feed)$('feed').value=event.data.session.feed;notice(event.data.text);render();}
  window.addEventListener('message',sourceMessage);
  iframe.src=mediaOrigin+'/publisher?compact=1';
  iframe.addEventListener('error',()=>notice('Không mở được publisher; kiểm tra dịch vụ media localhost.',true));
  $('source-start').onclick=()=>action(async()=>{sourcePending=true;command({type:'FIELD01_SOURCE_START',feed:$('feed').value,profileId:$('profile').value});notice('Đã yêu cầu bắt đầu nguồn; đang chờ phản hồi publisher.');});
  $('source-stop').onclick=()=>action(async()=>{sourcePending=true;command({type:'FIELD01_SOURCE_STOP'});notice('Đã yêu cầu dừng nguồn; đang chờ phản hồi publisher.');});
  $('viewer-start').onclick=()=>action(async()=>{await viewer.start();viewerState=viewer.state();notice('Viewer đã mở, đang chờ keyframe từ nguồn độc lập.');});
  $('viewer-stop').onclick=()=>action(async()=>{viewer.stop();viewerState=viewer.state();measuring=false;notice('Viewer đã dừng.');});
  $('measure').onclick=()=>action(async()=>{setup.open=false;panel.scrollTop=0;$('measure').focus({preventScroll:true});await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));if(!visualCheck())throw Error('Nguồn và canvas cần cùng nằm trọn trong vùng hiển thị.');viewer.measure({durationMs:30000});measurementEnd=performance.now()+30000;measuring=true;report=null;saved=null;$('fps').textContent='Đang đo';$('latency').textContent='Đang đo';$('recovery').textContent='Chưa đo';notice('Đang đo foreground 30 giây. Giữ nguồn và viewer cùng hiển thị.');});
  $('pause').onclick=()=>action(async()=>{await viewer.pause(500);notice('Đã ngắt relay 500 ms; chờ keyframe để đo phục hồi.');});
  $('save').onclick=()=>action(async()=>{saved=await viewer.saveReport();notice('Đã lưu '+saved.file+' · SHA '+saved.sha256.slice(0,12));});
  $('capture').onclick=()=>action(async()=>{const captured=await viewer.snapshot();await onCapture(captured);notice('Đã chuyển khung tổng hợp cho quy trình chụp của host.');});
  const visibilityObserver=new IntersectionObserver(()=>{if(measuring&&!visualCheck())viewer.invalidateVisualCoverage('PUBLISHER_OR_CANVAS_INTERSECTION_LOST');},{threshold:[0,.95,1]});visibilityObserver.observe(iframe);visibilityObserver.observe(viewer.canvas);
  const timer=setInterval(()=>{if(closed)return;viewerState=viewer.state();render();},200);
  function close(){if(closed)return;command({type:'FIELD01_SOURCE_STOP'});viewer.stop('MEDIA_PANEL_CLOSED');closed=true;clearInterval(timer);visibilityObserver.disconnect();window.removeEventListener('message',sourceMessage);iframe.src='about:blank';panel.remove();notify();}
  render();
  return{element:panel,viewer,snapshot:()=>viewer.snapshot(),state,close};
}
