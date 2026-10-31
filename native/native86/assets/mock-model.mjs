// Design rehearsal only. No hardware, MAVLink, persistent grants or flight transport.
export const PAYLOADS = Object.freeze({
 phase: {name:'Phase One',slot:'P1',format:'Ảnh mẫu',kind:'optical',description:'Kiểm tra chi tiết · cấu hình minh họa'},
 thermal: {name:'Camera nhiệt',slot:'P2',format:'Nhiệt minh họa',kind:'thermal',description:'Không có đo nhiệt hoặc hiệu chuẩn thật'},
 sony: {name:'Sony LR1',slot:'P3',format:'Ảnh mẫu',kind:'optical',description:'Khảo sát · cấu hình minh họa'}
});
export const SCENARIOS = Object.freeze({
 healthy:{label:'Liên kết bình thường',rc:true,telemetry:'fresh',video:'fresh',payload:'fresh',battery:78},
 battery:{label:'Pin thấp / dự phòng',rc:true,telemetry:'fresh',video:'fresh',payload:'fresh',battery:22},
 critical:{label:'Pin rất thấp',rc:true,telemetry:'fresh',video:'fresh',payload:'fresh',battery:12},
 video:{label:'Mất hình ảnh',rc:true,telemetry:'fresh',video:'stale',payload:'fresh',battery:78},
 link:{label:'Mất liên kết điều khiển',rc:false,telemetry:'stale',video:'fresh',payload:'stale',battery:null},
 telemetry:{label:'Telemetry quá hạn, RC còn',rc:true,telemetry:'stale',video:'fresh',payload:'fresh',battery:null},
 reboot:{label:'Autopilot reboot / chưa có dữ liệu',rc:true,telemetry:'unknown',video:'fresh',payload:'unknown',battery:null}
});
export function createMission(){return {type:'corridor',altitude:80,speed:5,payload:'phase',revision:1,approval:null,undo:[]};}
export function editMission(m,patch){
 const next={...m,...patch};
 if(!['corridor','survey'].includes(next.type)||!PAYLOADS[next.payload])return {ok:false,error:'Cấu hình nhiệm vụ không hợp lệ'};
 if(!Number.isFinite(next.altitude)||next.altitude<30||next.altitude>120||Math.abs(next.altitude*10-Math.round(next.altitude*10))>1e-6)return {ok:false,error:'Độ cao: 30–120 m, tối đa 1 số lẻ'};
 if(!Number.isFinite(next.speed)||next.speed<1||next.speed>10||Math.abs(next.speed*10-Math.round(next.speed*10))>1e-6)return {ok:false,error:'Tốc độ: 1–10 m/s, tối đa 1 số lẻ'};
 if(['type','altitude','speed','payload'].every(k=>next[k]===m[k]))return {ok:true,mission:m};
 const previous=Object.fromEntries(['type','altitude','speed','payload'].map(k=>[k,m[k]]));
 return {ok:true,mission:{...next,revision:m.revision+1,approval:null,undo:[...m.undo,previous].slice(-12)}};
}
export function undoMission(m){if(!m.undo.length)return m;return {...m,...m.undo.at(-1),revision:m.revision+1,approval:null,undo:m.undo.slice(0,-1)};}
export function approveMission(m,confirmed,session){return confirmed===3&&session?{...m,approval:{revision:m.revision,payload:m.payload,session}}:m;}
export function approvalValid(m,session){return m.approval?.revision===m.revision&&m.approval?.payload===m.payload&&m.approval?.session===session;}
export function createAuthority(){return {revision:0,sessions:{A:{name:'Phi công A',epoch:1,online:true},B:{name:'Operator B',epoch:1,online:true}},flight:null,payload:{phase:null,thermal:null,sony:null},pending:[],seen:[],last:'Chưa cấp quyền · buổi diễn tập mới'};}
export function sessionKey(a,id){return a.sessions[id]?.online?`${id}:${a.sessions[id].epoch}`:null;}
export function ownerName(a,key){if(!key)return 'Chưa cấp';const [id,epoch]=key.split(':');return a.sessions[id]?.online&&String(a.sessions[id].epoch)===epoch?a.sessions[id].name:'Phiên hết hạn';}
export function owns(a,id,resource,payload='phase'){const key=sessionKey(a,id);return !!key&&(resource==='flight'?a.flight:a.payload[payload])===key;}
export function applyAuthority(a,e){
 const fail=reason=>({ok:false,reason,authority:a});
 if(!e.id||a.seen.includes(e.id))return fail('Sự kiện lặp / replay bị từ chối');
 if(e.revision!==a.revision)return fail('Revision cũ / tranh chấp; đọc lại quyền');
 if(!['A','B'].includes(e.actor))return fail('Sai phiên');
 if(['request','resolve','grant'].includes(e.kind)&&!sessionKey(a,e.actor))return fail('Phiên đang mất kết nối');
 const n=structuredClone(a),key=sessionKey(n,e.actor),field=e.resource==='flight'?'flight':'payload';
 if(['grant','request'].includes(e.kind)){
  if(!['flight','payload'].includes(e.resource)||field==='payload'&&!PAYLOADS[e.payload])return fail('Sai tài nguyên/payload');
  if(field==='flight'&&e.actor!=='A')return fail('Operator B không được nhận quyền bay');
  const owner=field==='flight'?n.flight:n.payload[e.payload];
  if(e.kind==='grant'){
   if(owner)return fail('Đã có chủ quyền; cần bàn giao');
   if(field==='flight')n.flight=key;else n.payload[e.payload]=key;
   n.last=`Cấp mẫu: ${e.resource==='flight'?'Bay':PAYLOADS[e.payload].slot} → ${n.sessions[e.actor].name}`;
  }else{
   if(!owner||owner===key)return fail('Không có chủ khác để yêu cầu bàn giao');
   if(n.pending.some(p=>p.resource===e.resource&&p.payload===e.payload))return fail('Đã có yêu cầu chờ / tranh chấp');
   n.pending.push({id:e.id,requester:key,owner,resource:e.resource,payload:e.payload});n.last='Yêu cầu chờ chủ quyền xác nhận';
  }
 }else if(e.kind==='resolve'){
  const p=n.pending.find(p=>p.id===e.requestId);
  if(!p||p.owner!==key)return fail('Chỉ chủ quyền đúng phiên được xử lý yêu cầu');
  if(e.payload!==p.payload)return fail('Phản hồi sai payload');
  const owner=p.resource==='flight'?n.flight:n.payload[p.payload];
  if(owner!==p.owner)return fail('Chủ quyền đã đổi');
  if(e.accept){const [id]=p.requester.split(':');if(sessionKey(n,id)!==p.requester)return fail('Phiên nhận đã hết hạn');if(p.resource==='flight')n.flight=p.requester;else n.payload[p.payload]=p.requester;}
  n.pending=n.pending.filter(x=>x.id!==p.id);n.last=e.accept?'Bàn giao đã xác nhận trong mock':'Chủ quyền đã từ chối';
 }else if(['disconnect','restart','reconnect'].includes(e.kind)){
  const old=`${e.actor}:${n.sessions[e.actor].epoch}`;
  if(e.kind!=='reconnect'){
   if(n.flight===old)n.flight=null;
   for(const p of Object.keys(n.payload))if(n.payload[p]===old)n.payload[p]=null;
   n.pending=n.pending.filter(p=>p.owner!==old&&p.requester!==old);
   n.sessions[e.actor].epoch++;
  }
  n.sessions[e.actor].online=e.kind!=='disconnect';n.last='Phiên đổi / quyền thu hồi; không tự cấp lại';
 }else if(e.kind==='revokeAll'){
  n.flight=null;for(const p of Object.keys(n.payload))n.payload[p]=null;n.pending=[];n.last='Thu hồi toàn bộ quyền mẫu';
 }else return fail('Sự kiện không được hỗ trợ');
 n.revision++;n.seen=[...n.seen,e.id].slice(-128);return {ok:true,authority:n};
}
export function channelState(scenario,since,now){
 const s=SCENARIOS[scenario]??SCENARIOS.healthy,age=Math.max(0,now-since)/1000;
 return {...s,age:Math.floor(age+4),telemetryLabel:s.telemetry==='fresh'?'Telemetry mẫu · mới':s.telemetry==='unknown'?'Telemetry chưa biết':`Telemetry cuối · ${Math.floor(age+4)} s`,videoLabel:s.video==='fresh'?'Video mẫu · mới':`Khung cuối · ${Math.floor(age+4)} s`};
}
export function flightEnabled(a,id,c){return c.rc&&c.telemetry==='fresh'&&owns(a,id,'flight');}
export function cameraEnabled(a,id,p,c){return c.rc&&c.payload==='fresh'&&c.video==='fresh'&&owns(a,id,'payload',p);}
