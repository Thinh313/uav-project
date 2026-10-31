import{clampTime,clock,sampleAt,altitudeRange,fitProjection,verifyClientReport}from'./replay.mjs';
const $=id=>document.getElementById(id),NS='http://www.w3.org/2000/svg';
let state,report=null,at=0,playing=false,raf=0,playEpoch=0,reportEpoch=0,showStrips=true,loading=false;
const blobURLs=new Map(),THEME_KEY='aeris.coach01.theme',REPORT_KEY='aeris.coach01.last-report';
const icons={play:'M9 5 19 12 9 19Z',pause:'M8 5v14M16 5v14',sun:'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1 1M18 18l1 1M5 19l1-1M18 6l1-1',moon:'M20 15A8 8 0 0 1 9 4a8.5 8.5 0 1 0 11 11Z'};
function icon(el,name){el.replaceChildren();const s=document.createElementNS(NS,'svg'),p=document.createElementNS(NS,'path');s.setAttribute('viewBox','0 0 24 24');s.setAttribute('aria-hidden','true');p.setAttribute('d',icons[name]);s.append(p);el.append(s);}
const format=(n,d=1)=>Number.isFinite(n)?n.toLocaleString('vi-VN',{maximumFractionDigits:d,minimumFractionDigits:d}):'—';
function text(tag,value,cls){const e=document.createElement(tag);e.textContent=value;if(cls)e.className=cls;return e;}
function status(value){$('status').textContent=value;}
function preference(key,value){try{if(value===undefined)return localStorage.getItem(key);localStorage.setItem(key,value);}catch{/* presentation preferences are optional */}return null;}
function theme(value){const light=value==='light';document.documentElement.dataset.theme=light?'light':'dark';icon($('theme'),light?'moon':'sun');$('theme').setAttribute('aria-label',light?'Chuyển sang giao diện tối':'Chuyển sang giao diện sáng');}
function controls(){
 for(const id of['open','file','demo','refresh-history'])$(id).disabled=loading;
 for(const id of['play','scrub','rate','start','fit','strips','export'])$(id).disabled=loading||!report;
 for(const id of['history-list','findings','events'])for(const button of $(id).querySelectorAll('button'))button.disabled=loading;
 document.body.setAttribute('aria-busy',String(loading));
}
function failure(error){const messages={ORIGIN_OR_CSRF:'Phiên server đã thay đổi. Hãy thực hiện lại thao tác; không tự gửi lại yêu cầu.',ANALYSIS_BUSY:'Server đang xử lý hồ sơ khác. Hãy thử lại khi tác vụ đó kết thúc.',REPORT_DIGEST:'Checksum báo cáo không khớp. Không mở hoặc tải báo cáo này.',REPORT_SCOPE:'Báo cáo không thuộc phạm vi replay được hỗ trợ.',CLIENT_CRYPTO_UNAVAILABLE:'Trình duyệt chưa cung cấp WebCrypto để kiểm báo cáo.',EXPORT_CONTEXT:'Báo cáo tải về không khớp hồ sơ đang xem.',SOURCE32MIB:'Gói lớn hơn giới hạn 32 MiB.',BODY_TIMEOUT:'Thao tác quá thời gian chờ.'};return messages[error.message]??(error.name==='AbortError'?'Server chưa phản hồi trong thời gian cho phép.':error.message);}
async function withResponse(url,body,consume){
 const controller=new AbortController(),alarm=setTimeout(()=>controller.abort(),8000);
 try{return await consume(await fetch(url,body===undefined?{signal:controller.signal}:{method:'POST',signal:controller.signal,headers:{'Content-Type':'application/json','X-Coach-CSRF':state?.csrf??''},body}));}
 finally{clearTimeout(alarm);}
}
async function api(url,body){return withResponse(url,body,async r=>{let data;try{data=await r.json();}catch(e){if(e.name==='AbortError')throw e;throw Error('Server trả dữ liệu không đọc được; hồ sơ hiện tại được giữ nguyên.');}if(!r.ok)throw Error(typeof data.error==='string'?data.error:'Không đọc được hồ sơ');return data;});}
async function guarded(fn){if(loading)return;loading=true;document.body.classList.add('busy');pause();controls();try{await fn();}catch(e){status('Không hoàn tất: '+failure(e));}finally{loading=false;document.body.classList.remove('busy');controls();}}
async function refreshHistory(){
 const fresh=await api('/api/state');if(typeof fresh.csrf!=='string'||!fresh.csrf||!Array.isArray(fresh.reports)||!Array.isArray(fresh.issues))throw Error('Phản hồi danh sách hồ sơ không hợp lệ.');state=fresh;
 $('history-count').textContent=state.reports.length;$('history-list').replaceChildren();
 for(const h of state.reports){const b=text('button',h.name+' · '+h.run.slice(-8));b.onclick=()=>guarded(async()=>{await load(await api('/api/report/'+h.id));status('Đã kiểm và tính lại báo cáo từ hồ sơ gốc.');});$('history-list').append(b);}
 if(state.issues.length)$('history-list').append(text('p',`${state.issues.length} hồ sơ chưa hợp lệ, không được mở.`,'evidence-caption'));controls();
}
async function mutation(url,body){await refreshHistory();return api(url,body);}// One explicit POST only; never automatic retry.
async function afterSuccess(message){try{await refreshHistory();status(message);}catch{status(message+' Hồ sơ đã lưu, nhưng chưa tải lại được lịch sử. Chọn Làm mới hồ sơ để kiểm lại.');}}
function pause(){playing=false;playEpoch++;cancelAnimationFrame(raf);raf=0;icon($('play'),'play');$('play').setAttribute('aria-label','Phát lại');}
function seek(t){at=clampTime(t,report?.telemetry.durationS??0);$('scrub').value=String(at);draw();}
async function load(r){
 await verifyClientReport(r);
 if(!r.telemetry.trace.every((s,i,a)=>[s.tS,s.x,s.y,s.relativeHomeM,s.groundSpeedMS].every(Number.isFinite)&&(!i||s.tS>=a[i-1].tS)))throw Error('REPORT_SCOPE');
 pause();report=r;at=0;const imageEpoch=++reportEpoch;$('scrub').value='0';preference(REPORT_KEY,r.sha256);
 $('empty').hidden=true;$('source').textContent=r.source==='OBSERVED_OWNED_SITL'?'Hồ sơ Android–ArduPilot SITL':'Hồ sơ giao thức mô phỏng';$('mission').textContent=r.plan.name;
 $('subtitle').textContent=r.sourceAccepted?'Nguồn ghi nhận hoàn tất · Đánh giá khảo sát thực còn thiếu dữ liệu':'Nguồn ghi nhận gián đoạn · Không coi là hoàn tất';$('scrub').max=r.telemetry.durationS;
 $('overview').replaceChildren();const grid=text('div','','overview');
 for(const[label,value]of[['Mẫu vị trí',r.telemetry.metrics.positionSamples],['Gia tốc P95',format(r.telemetry.motion.accelerationP95MS2,2)+' m/s²'],['Khoảng trống',r.telemetry.gaps.length],['Ảnh thực',r.inspection.actualImages]]){const item=document.createElement('div');item.append(text('span',label),text('strong',value));grid.append(item);}$('overview').append(grid);
 $('findings').replaceChildren();
 for(const f of r.findings){
  const e=text('article','','finding');e.dataset.severity=f.severity;e.append(text('h3',f.title),text('p',f.explanation),text('p',f.proposal,'proposal'));const refs=text('div','','refs');
  for(const v of f.evidence.slice(0,6)){if(v.record){const b=text('button','Raw #'+v.record);b.onclick=()=>{pause();const s=r.telemetry.trace.find(s=>s.record>=v.record)??r.telemetry.trace.at(-1);seek(s.tS);status(`Dẫn chứng: ${v.file}, record ${v.record}. Hiển thị mẫu vị trí gần mốc, không nội suy.`);};refs.append(b);}else refs.append(text('span',v.file+(v.field?' · '+v.field:''),'evidence-caption'));}e.append(refs);$('findings').append(e);
 }
 $('events').replaceChildren();for(const e of r.telemetry.events){const b=text('button',clock(e.tS)+' '+e.label);b.title='Raw #'+e.record;b.onclick=()=>{pause();seek(e.tS);status(`${e.label} · raw #${e.record}. Hiển thị mẫu đã ghi gần mốc.`);};$('events').append(b);}
 $('capture').replaceChildren();const capture=r.inspection.captures[0];
 if(capture){const img=document.createElement('img'),caption=text('p','Ảnh tổng hợp · '+capture.id);img.alt='Ảnh camera tổng hợp đã lưu trong hồ sơ';img.onerror=()=>{if(imageEpoch===reportEpoch)caption.textContent='Chưa tải được ảnh tổng hợp. Không thay bằng ảnh khác hoặc suy chất lượng ảnh.';};img.src='/api/report/'+r.sha256+'/image?file='+encodeURIComponent(capture.file);$('capture').append(img,caption,text('p','Định vị tham chiếu host: '+format(capture.position.latitudeDeg,7)+', '+format(capture.position.longitudeDeg,7)+'. Không đủ chuẩn khảo sát.'));}
 $('limits').replaceChildren();for(const value of['Ngưỡng tham chiếu: gap guest ≤1 s; gap host ≤2 s. Độ cao / Home, không mặc định là AGL.','Khoảng cách tới dải khảo sát gần nhất chỉ tính trong AUTO, armed và ±2 m quanh cao độ nhiệm vụ. Không phải sai số bám waypoint.','Chưa định lượng độ phủ, GSD, nhòe hay chồng phủ ảnh thực. Không chấm điểm tổng hoặc chấm kỹ năng phi công.','Rules xác định; chưa có mô hình AI học máy hay kết nối điều khiển.'])$('limits').append(text('p',value));$('limits').append(text('code','SHA báo cáo: '+r.sha256));$('integrity').textContent='Checksum + raw/WAL đã kiểm · Không chứng thực nguồn';controls();draw();
}
function setup(canvas){
 const dpr=Math.min(devicePixelRatio||1,2),rect=canvas.getBoundingClientRect();if(!rect.width||!rect.height)return null;
 const width=Math.round(rect.width*dpr),height=Math.round(rect.height*dpr);if(canvas.width!==width)canvas.width=width;if(canvas.height!==height)canvas.height=height;
 const ctx=canvas.getContext('2d');if(!ctx)return null;ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,rect.width,rect.height);return{ctx,w:rect.width,h:rect.height};
}
function draw(){
 const map=setup($('map')),chart=setup($('chart'));if(!map||!chart)return;
 const css=getComputedStyle(document.documentElement),fg=css.getPropertyValue('--fg'),muted=css.getPropertyValue('--muted'),pathColor=css.getPropertyValue('--path'),strip=css.getPropertyValue('--strip'),gridColor=css.getPropertyValue('--grid'),{ctx:c,w,h}=map;
 c.strokeStyle=gridColor;c.lineWidth=1;for(let x=0;x<w;x+=48){c.beginPath();c.moveTo(x,0);c.lineTo(x,h);c.stroke();}for(let y=0;y<h;y+=48){c.beginPath();c.moveTo(0,y);c.lineTo(w,y);c.stroke();}
 if(!report){chart.ctx.fillStyle=muted;chart.ctx.font='12px Barlow';chart.ctx.fillText('Độ cao / Home theo thời gian nhận trên host',12,25);return;}
 const r=report,trace=r.telemetry.trace,{index,sample:selected,unavailable}=sampleAt(trace,at);
 $('height').textContent=unavailable?'—':format(selected.relativeHomeM);$('speed').textContent=unavailable?'—':format(selected.groundSpeedMS);
 $('mode').textContent=unavailable?'Thiếu dữ liệu':selected.mode===3?'AUTO':selected.mode===6?'RTL':selected.mode===9?'LAND':selected.mode===null?'Chưa rõ':'Mode '+selected.mode;
 $('record').textContent=unavailable?'—':'#'+selected.record;$('clock').textContent=unavailable?'Vị trí cuối đã biết · Khoảng trống, không nội suy':selected.headingDeg===null?'Mẫu gần nhất · Hướng chưa biết':'Mẫu gần nhất · Không nội suy · Heading từ telemetry';$('time').textContent=clock(at)+' / '+clock(r.telemetry.durationS);
 const projection=fitProjection([...trace,...r.plan.legs.flatMap(l=>[l.start,l.end]),r.plan.home],w,h);
 if(projection){const{X,Y}=projection;
  c.lineWidth=1.3;if(showStrips){c.strokeStyle=strip;c.setLineDash([5,5]);for(const leg of r.plan.legs){c.beginPath();c.moveTo(X(leg.start.x),Y(leg.start.y));c.lineTo(X(leg.end.x),Y(leg.end.y));c.stroke();}c.setLineDash([]);}
  c.strokeStyle=pathColor;c.globalAlpha=.25;c.lineWidth=2;c.beginPath();trace.forEach((p,i)=>{if(!i||p.breakBefore)c.moveTo(X(p.x),Y(p.y));else c.lineTo(X(p.x),Y(p.y));});c.stroke();c.globalAlpha=1;
  c.beginPath();for(let i=0;i<=index;i++){const p=trace[i];if(!i||p.breakBefore)c.moveTo(X(p.x),Y(p.y));else c.lineTo(X(p.x),Y(p.y));}c.stroke();
  c.fillStyle=muted;c.font='600 12px Barlow';c.fillText('H',X(r.plan.home.x)-4,Y(r.plan.home.y)+20);c.beginPath();c.arc(X(r.plan.home.x),Y(r.plan.home.y),4,0,Math.PI*2);c.strokeStyle=strip;c.stroke();
  c.save();c.translate(X(selected.x),Y(selected.y));c.beginPath();if(unavailable||selected.headingDeg===null)c.arc(0,0,7,0,Math.PI*2);else{c.rotate(selected.headingDeg*Math.PI/180);c.moveTo(0,-11);c.lineTo(8,9);c.lineTo(0,5);c.lineTo(-8,9);c.closePath();}c.fillStyle=unavailable?muted:pathColor;c.fill();c.strokeStyle=fg;c.lineWidth=1;c.stroke();c.restore();
 }
 const d=chart.ctx,range=altitudeRange(trace),xx=t=>12+t/Math.max(.001,r.telemetry.durationS)*(chart.w-24),yy=v=>chart.h-7-(v-range.min)/(range.max-range.min)*(chart.h-17);
 d.strokeStyle=strip;d.lineWidth=1.3;d.beginPath();trace.forEach((s,i)=>{if(!i||s.breakBefore)d.moveTo(xx(s.tS),yy(s.relativeHomeM));else d.lineTo(xx(s.tS),yy(s.relativeHomeM));});d.stroke();d.strokeStyle=pathColor;d.beginPath();d.moveTo(xx(at),2);d.lineTo(xx(at),chart.h-1);d.stroke();d.fillStyle=muted;d.font='11px Barlow';d.fillText('Home '+format(range.min,0)+'…'+format(range.max,0)+' m',14,11);
}
async function exportReport(){
 if(!report)return;const expected=report;
 return withResponse('/api/report/'+expected.sha256+'/export',undefined,async res=>{if(!res.ok){let error;try{error=await res.json();}catch{}throw Error(error?.error??'Không tải được báo cáo.');}
 if(!res.headers.get('content-type')?.includes('application/json'))throw Error('Báo cáo tải về không đúng định dạng JSON.');
 if(Number(res.headers.get('content-length')??0)>32*2**20)throw Error('Báo cáo vượt giới hạn tải.');const bytes=await res.arrayBuffer();if(bytes.byteLength>32*2**20)throw Error('Báo cáo vượt giới hạn tải.');
 const downloaded=JSON.parse(new TextDecoder().decode(bytes));await verifyClientReport(downloaded);if(downloaded.sha256!==expected.sha256)throw Error('EXPORT_CONTEXT');
 const url=URL.createObjectURL(new Blob([bytes],{type:'application/json'})),anchor=document.createElement('a');anchor.href=url;anchor.download='AERIS-debrief-'+expected.run.replace(/[^a-z0-9_-]/ig,'').slice(0,64)+'.json';anchor.hidden=true;document.body.append(anchor);
 try{anchor.click();}finally{anchor.remove();const timer=setTimeout(()=>{URL.revokeObjectURL(url);blobURLs.delete(url);},1000);blobURLs.set(url,timer);}
 status('Đã kiểm checksum và yêu cầu trình duyệt tải báo cáo. Chưa xác nhận file đã lưu trên máy.');});
}
$('theme').onclick=()=>{const value=document.documentElement.dataset.theme==='light'?'dark':'light';theme(value);preference(THEME_KEY,value);draw();};
$('open').onclick=()=>$('file').click();
$('file').onchange=async()=>{const file=$('file').files[0];try{if(!file)return;await guarded(async()=>{if(file.size>32*2**20)throw Error('SOURCE32MIB');status('Đang kiểm SHA, chuỗi raw/WAL và dựng lại nhiệm vụ…');const result=await mutation('/api/import',await file.arrayBuffer());await load(result.report);await afterSuccess('Đã phân tích và lưu hồ sơ · '+format(result.analysisMs,0)+' ms.');});}finally{$('file').value='';}};
$('demo').onclick=()=>guarded(async()=>{status('Đang đối chiếu hồ sơ SITL đã lưu…');const result=await mutation('/api/demo','{}');await load(result.report);await afterSuccess('Đã mở hồ sơ SITL cũ · Không chạy chuyến bay mới.');});
$('refresh-history').onclick=()=>guarded(async()=>{await refreshHistory();status('Đã làm mới danh sách hồ sơ.');});
$('export').onclick=()=>guarded(exportReport);
$('scrub').oninput=()=>{pause();seek(Number($('scrub').value));};$('start').onclick=()=>{pause();seek(0);};$('fit').onclick=draw;
$('strips').onclick=()=>{showStrips=!showStrips;$('strips').classList.toggle('selected',showStrips);$('strips').setAttribute('aria-pressed',String(showStrips));$('strips').setAttribute('aria-label',showStrips?'Ẩn dải khảo sát':'Hiện dải khảo sát');$('strip-label').textContent=showStrips?'Dải khảo sát':'Dải khảo sát (đã ẩn)';draw();};
$('play').onclick=()=>{
 if(!report||loading)return;if(playing){pause();return;}if(at>=report.telemetry.durationS)seek(0);playing=true;const epoch=++playEpoch;icon($('play'),'pause');$('play').setAttribute('aria-label','Tạm dừng');let last=performance.now();
 const frame=now=>{if(!playing||epoch!==playEpoch)return;const dt=Math.max(0,(now-last)/1000);last=now;seek(at+dt*Number($('rate').value));if(at>=report.telemetry.durationS){pause();return;}raf=requestAnimationFrame(frame);};raf=requestAnimationFrame(frame);
};
document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});
window.addEventListener('pagehide',()=>{pause();for(const[url,timer]of blobURLs){clearTimeout(timer);URL.revokeObjectURL(url);}blobURLs.clear();});
new ResizeObserver(draw).observe($('map'));window.addEventListener('resize',draw);document.fonts.ready.then(draw);theme(preference(THEME_KEY));icon($('play'),'play');$('strips').setAttribute('aria-pressed','true');
guarded(async()=>{status('Đang đọc danh sách hồ sơ…');await refreshHistory();const previous=preference(REPORT_KEY);if(previous&&/^[a-f0-9]{64}$/.test(previous)&&state.reports.some(h=>h.id===previous)){await load(await api('/api/report/'+previous));status('Đã mở lại hồ sơ đã kiểm. Replay đang tạm dừng; không có quyền điều khiển bay.');}else status('Sẵn sàng mở hồ sơ. Không có kết nối điều khiển bay.');});draw();
