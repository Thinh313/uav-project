import {importSurvey,planPolygonSurvey,surveyPackage} from './survey.mjs';
const clone=x=>structuredClone(x);
const stable=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?`[${x.map(stable).join(',')}]`:`{${Object.keys(x).sort().map(k=>`${JSON.stringify(k)}:${stable(x[k])}`).join(',')}}`;
export async function planDigest(pkg){const d=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(stable(pkg)));return [...new Uint8Array(d)].map(b=>b.toString(16).padStart(2,'0')).join('');}
/** Local rehearsal: ACK never establishes readback or execution. No transport. */
export class MissionSession{
 constructor({vehicleId='SIM-001',sessionId=crypto.randomUUID()}={}){this.vehicleId=vehicleId;this.sessionId=sessionId;this.state='empty';this.onboard=null;this.transaction=null;this.progress=0;this.error=null;}
 async beginUpload(pkg){
  if(['uploading','accepted','running','paused'].includes(this.state))throw Error('Phiên hiện tại chưa kết thúc; không thay nhiệm vụ đang hoạt động.');
  const clean=importSurvey(JSON.stringify(pkg));if(!planPolygonSurvey(clean.settings).feasible)throw Error('Nhiệm vụ chưa đạt kiểm tra; chưa được đưa vào mô hình phương tiện.');
  // Reserve state before awaiting digest, preventing double-click racing uploads.
  this.state='uploading';this.error=null;
  try{this.transaction={id:crypto.randomUUID(),vehicleId:this.vehicleId,sessionId:this.sessionId,package:clone(clean),digest:await planDigest(clean)};return clone(this.transaction);}
  catch(e){this.state='failed';this.error=e.message;throw e;}
 }
 matches(event){return !!this.transaction&&event.transactionId===this.transaction.id&&event.vehicleId===this.vehicleId&&event.sessionId===this.sessionId;}
 ack(event){if(!this.matches(event)||this.state!=='uploading')return false;if(!['accepted','rejected'].includes(event.result))return false;this.state=event.result==='accepted'?'accepted':'failed';if(this.state==='failed')this.error='Mô hình từ chối upload.';return true;}
 async readback(event){
  if(!this.matches(event)||this.state!=='accepted')return false;
  const transactionId=this.transaction.id;
  let clean;try{clean=importSurvey(JSON.stringify(event.package));}catch{this.state='failed';this.error='Readback không hợp lệ.';return false;}
  const digest=await planDigest(clean);
  if(this.state!=='accepted'||this.transaction.id!==transactionId)return false;
  if(digest!==this.transaction.digest){this.state='failed';this.error='Readback không khớp plan đã gửi.';return false;}
  this.onboard={package:clone(clean),digest};this.state='uploaded';this.progress=0;return true;
 }
 start(){if(!['uploaded','paused'].includes(this.state)||!this.onboard)throw Error('Cần mission readback đã khớp trước khi chạy.');this.state='running';}
 pause(){if(this.state!=='running')throw Error('Chưa có nhiệm vụ đang chạy.');this.state='paused';}
 observeProgress(event){if(event.vehicleId!==this.vehicleId||event.sessionId!==this.sessionId||this.state!=='running'||!this.onboard)return false;const count=planPolygonSurvey(this.onboard.package.settings).lineCount;if(!Number.isInteger(event.completedTransects)||event.completedTransects<this.progress||event.completedTransects>count)return false;this.progress=event.completedTransects;if(this.progress===count)this.state='completed';return true;}
 abort(){if(!['running','paused','uploading','accepted'].includes(this.state))throw Error('Không có phiên đang hoạt động.');this.state='aborted';}
 snapshot(){return {version:1,operational:false,vehicleId:this.vehicleId,sessionId:this.sessionId,state:this.state,onboard:clone(this.onboard),progress:this.progress};}
 static async restore(data){
  if(!data||data.version!==1||data.operational!==false||data.vehicleId!=='SIM-001'||typeof data.sessionId!=='string')throw Error('Snapshot phiên không hỗ trợ.');
  const s=new MissionSession({vehicleId:data.vehicleId,sessionId:data.sessionId});
  if(data.onboard){const pkg=importSurvey(JSON.stringify(data.onboard.package)),p=planPolygonSurvey(pkg.settings);if(!p.feasible||await planDigest(pkg)!==data.onboard.digest)throw Error('Snapshot nhiệm vụ không khớp digest hoặc không hợp lệ.');s.onboard={package:pkg,digest:data.onboard.digest};if(!Number.isInteger(data.progress)||data.progress<0||data.progress>p.lineCount)throw Error('Tiến độ snapshot không hợp lệ.');s.progress=data.progress;s.state=data.progress===p.lineCount?'completed':'uploaded';}
  // Reboot cannot prove running state. Explicit start required; upload ACK isn't restored.
  return s;
 }
}
export class MissionLibrary{
 constructor(storage){this.storage=storage;this.key='aeris-survey-library-v2';}
 list(){const raw=this.storage.getItem(this.key);if(!raw)return [];let data;try{data=JSON.parse(raw);}catch{throw Error('Thư viện bị lỗi JSON; dữ liệu chưa bị ghi đè.');}if(!Array.isArray(data)||data.length>50)throw Error('Thư viện không hợp lệ.');return data.map(d=>{if(typeof d.id!=='string'||typeof d.savedAt!=='string')throw Error('Bản lưu thiếu metadata.');return {...d,package:importSurvey(JSON.stringify(d.package))};});}
 save(settings){const pkg=surveyPackage(settings);planPolygonSurvey(settings);const list=this.list(),old=list.find(d=>d.package.settings.name===settings.name),entry={id:old?.id||crypto.randomUUID(),savedAt:new Date().toISOString(),package:pkg};const next=[entry,...list.filter(d=>d.id!==entry.id)].slice(0,50);this.storage.setItem(this.key,JSON.stringify(next));return clone(entry);}
}
