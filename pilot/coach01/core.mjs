import {createHash} from 'node:crypto';
import {verifyPackage} from '../betaworkbench05/package.mjs';
import {Decoder} from '../../services/mavlink.mjs';
import {parseKml} from '../workbench01/kml.mjs';
import {createPlan} from '../workbench01/core.mjs';
import {prepareSITL} from '../workbench02/sitl-contract.mjs';
import {localFrame} from '../../app/core/survey.mjs';

export const POLICY=Object.freeze({id:'COACH01_REFERENCE_V2',maxGuestGapMs:1000,maxHostGapMs:2000,heartbeatFreshMs:1500,altitudeBandM:2,stripDistanceNoticeM:2,maxSourceBytes:32*2**20,maxRawRows:100000,calibration:'ENGINEERING_REFERENCE_NOT_HERA_OR_PILOT_GRADING'});
export const stable=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?'['+x.map(stable).join(',')+']':'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+stable(x[k])).join(',')+'}';
export const hash=x=>createHash('sha256').update(x).digest('hex');
const need=(v,m)=>{if(!v)throw Error(m);};
const finite=Number.isFinite;
export function percentile(values,p=.95){if(!values.length)return null;const xs=[...values].sort((a,b)=>a-b);return xs[Math.max(0,Math.ceil(xs.length*p)-1)];}
export function angleDelta(a,b){return((b-a+540)%360+360)%360-180;}
export function segmentDistance(p,a,b){const dx=b.x-a.x,dy=b.y-a.y,l=dx*dx+dy*dy,t=l===0?0:Math.max(0,Math.min(1,((p.x-a.x)*dx+(p.y-a.y)*dy)/l));return Math.hypot(p.x-a.x-t*dx,p.y-a.y-t*dy);}
export function localPoint(lat,lon,origin){return localFrame(origin).forward({lat,lon});}
export function motion(samples){
 const accelerations=[],turnRates=[];let qualifiedPairs=0,rejectedPairs=0;
 for(let i=1;i<samples.length;i++){
  const a=samples[i-1],b=samples[i],guest=b.bootMs-a.bootMs,host=b.hostMs-a.hostMs;
  if(b.breakBefore||guest<=0||guest>POLICY.maxGuestGapMs||host<0||host>POLICY.maxHostGapMs){rejectedPairs++;continue;}
  qualifiedPairs++;const dt=guest/1000;
  if([a.vx,a.vy,b.vx,b.vy].every(finite))accelerations.push({value:Math.hypot(b.vx-a.vx,b.vy-a.vy)/dt,records:[a.record,b.record]});
  if([a.headingDeg,b.headingDeg].every(finite))turnRates.push({value:Math.abs(angleDelta(a.headingDeg,b.headingDeg))/dt,records:[a.record,b.record]});
 }
 return{qualifiedPairs,rejectedPairs,accelerationP95MS2:percentile(accelerations.map(x=>x.value)),accelerationMaxMS2:accelerations.length?Math.max(...accelerations.map(x=>x.value)):null,headingRateP95DegS:percentile(turnRates.map(x=>x.value)),accelerationPeak:accelerations.length?accelerations.reduce((a,b)=>a.value>b.value?a:b):null,scope:'VEHICLE_HORIZONTAL_VELOCITY_CHANGE_NOT_STICK_INPUT_OR_PILOT_SKILL'};
}
const eventNames={PREFLIGHT:'Đối chiếu preflight',READBACK_VERIFIED:'Đã đối chiếu nhiệm vụ',ARM_GROUND_INTENT:'Yêu cầu arm',POST_ARM_HOME_REVIEW_REQUIRED:'Xác nhận Home sau arm',AUTO_INTENT:'Yêu cầu AUTO',AUTO_OBSERVED:'Đã quan sát AUTO',BETA_CLOSE_INTENT:'Đóng phiên bay',LINK_CLOSE:'Đóng liên kết'};

export function analyzeTelemetry(rows,review,plan){
 need(Array.isArray(rows)&&rows.length>0&&rows.length<=POLICY.maxRawRows,'RAW_ROW_BOUND');
 const sessions=rows.filter(r=>r.kind==='SESSION');need(sessions.length===1,'ONE_RAW_SESSION');
 const context=sessions[0].data.context;
 need(context&&context.boot===review.boot&&context.session===review.session&&context.epoch===review.run&&context.system===42&&context.component===1,'RAW_SESSION_CONTEXT');
 need(sessions[0].data.planSha256===review.planSha256&&sessions[0].data.missionSha256===review.missionSha256,'RAW_PLAN_CONTEXT');
 const decoder=new Decoder(),trace=[],events=[],gaps=[],warnings=[];
 let previousNs=-1n,heartbeat=null,foreignMessages=0,previousPosition=null,wireMessages=0,autoIntent=null;
 const ref=(row,detail)=>({record:row.n,file:'flight/raw.jsonl',hostMs:Number(BigInt(row.hostNs))/1e6,...detail});
 for(const row of rows){
  need(typeof row.hostNs==='string'&&/^\d+$/.test(row.hostNs),'HOST_CLOCK_INTEGER');const ns=BigInt(row.hostNs);need(ns>=previousNs,'HOST_CLOCK_REGRESSION');previousNs=ns;
  const hostMs=Number(ns)/1e6;need(finite(hostMs),'HOST_CLOCK_RANGE');
  if(eventNames[row.kind])events.push(ref(row,{id:row.kind,label:eventNames[row.kind],kind:'EVENT'}));
  if(row.kind==='AUTO_INTENT')autoIntent=ref(row,{});
  if(row.kind!=='RX_RAW')continue;
  need(typeof row.data.rawHex==='string'&&/^(?:[a-f0-9]{2})*$/i.test(row.data.rawHex)&&row.data.rawHex.length<=131072,'WIRE_HEX_BOUND');
  for(const m of decoder.push(Buffer.from(row.data.rawHex,'hex'))){
   wireMessages++;
   if(m.system!==context.system||m.component!==context.component){foreignMessages++;continue;}
   const f=m.fields;
   if(m.id===0)heartbeat={hostMs,mode:f.custom_mode,armed:!!(f.base_mode&128),record:row.n};
   if(m.id!==33)continue;
   need([f.time_boot_ms,f.lat,f.lon,f.alt,f.relative_alt,f.vx,f.vy,f.hdg].every(finite),'POSITION_FINITE');
   const latitudeDeg=f.lat/1e7,longitudeDeg=f.lon/1e7;
   need(Math.abs(latitudeDeg)<=90&&Math.abs(longitudeDeg)<=180,'POSITION_COORDINATES');
   const p=localPoint(latitudeDeg,longitudeDeg,plan.origin),localDomain=Math.hypot(p.x,p.y)<=2500;
   const fresh=heartbeat&&hostMs-heartbeat.hostMs<=POLICY.heartbeatFreshMs;
   const sample={record:row.n,hostMs,bootMs:f.time_boot_ms,latitudeDeg,longitudeDeg,relativeHomeM:f.relative_alt/1000,mslM:f.alt/1000,vx:f.vx/100,vy:f.vy/100,groundSpeedMS:Math.hypot(f.vx,f.vy)/100,headingDeg:f.hdg===65535?null:f.hdg/100,x:p.x,y:p.y,localDomain,mode:fresh?heartbeat.mode:null,armed:fresh?heartbeat.armed:null,heartbeatRecord:fresh?heartbeat.record:null,breakBefore:null,stripDistanceM:null};
   if(previousPosition){
    const guest=sample.bootMs-previousPosition.bootMs,host=hostMs-previousPosition.hostMs;
    if(guest<=0||guest>POLICY.maxGuestGapMs||host>POLICY.maxHostGapMs)sample.breakBefore=guest<0?'GUEST_CLOCK_REGRESSION':guest===0?'DUPLICATE_GUEST_TIME':guest>POLICY.maxGuestGapMs?'TELEMETRY_GAP':'HOST_RECEIVE_GAP';
    if(sample.breakBefore){const g=ref(row,{kind:'GAP',id:sample.breakBefore,label:'Dữ liệu gián đoạn',previousRecord:previousPosition.record,guestGapMs:guest,hostGapMs:host,startHostMs:previousPosition.hostMs,endHostMs:hostMs});gaps.push(g);events.push(g);}
   }
   if(localDomain&&sample.mode===3&&sample.armed===true&&Math.abs(sample.relativeHomeM-plan.input.options.altitudeAglM)<=POLICY.altitudeBandM&&plan.legs.length)sample.stripDistanceM=Math.min(...plan.legs.map(l=>segmentDistance(sample,l.start,l.end)));
   sample.traceIndex=trace.length;trace.push(sample);previousPosition=sample;
  }
 }
 need(decoder.stats.corrupt===0&&decoder.stats.unsupported===0,'CORRUPT_OR_UNSUPPORTED_WIRE');
 need(decoder.buffer.length===0,'PARTIAL_WIRE_TAIL');need(trace.length>0,'NO_TARGET_POSITION');
 const startHostMs=trace[0].hostMs,endHostMs=trace.at(-1).hostMs;
 const inAuto=trace.filter(s=>s.mode===3&&s.armed===true),strip=trace.filter(s=>s.stripDistanceM!==null);
 const airborne=inAuto.filter(s=>s.relativeHomeM>2),motionStats=motion(airborne.map((s,i,a)=>({...s,breakBefore:s.breakBefore||(i&&s.traceIndex!==a[i-1].traceIndex+1?'FILTERED_INTERVAL':null)})));
 if(!airborne.length)warnings.push('NO_OBSERVED_ARMED_AUTO_AIRBORNE_POSITION');
 if(!strip.length)warnings.push('NO_SURVEY_ALTITUDE_ELIGIBLE_SAMPLES');
 if(gaps.some(g=>g.id==='GUEST_CLOCK_REGRESSION'))warnings.push('POSSIBLE_REBOOT_OR_UINT32_WRAP_NOT_RESOLVED');
 if(trace.some(s=>!s.localDomain))warnings.push('POSITIONS_OUTSIDE_2500M_LOCAL_APPROXIMATION');
 return{startHostMs,endHostMs,durationS:(endHostMs-startHostMs)/1000,trace:trace.map(s=>({...s,tS:(s.hostMs-startHostMs)/1000})),events:events.map(e=>({...e,tS:(e.hostMs-startHostMs)/1000})),gaps,wire:{...decoder.stats,wireMessages,foreignMessages,crcVerified:true,crcScope:'KNOWN_DIALECT_ONLY_UNKNOWN_NOT_INTERPRETED',source:'RX_RAW_ONLY_NOT_RX_DECODED'},motion:motionStats,metrics:{positionSamples:trace.length,armedAutoSamples:inAuto.length,autoAirborneSamples:airborne.length,maxGroundSpeedMS:Math.max(...trace.map(s=>s.groundSpeedMS)),maxRelativeHomeM:Math.max(...trace.map(s=>s.relativeHomeM)),eligibleStripSamples:strip.length,nearestStripP95M:percentile(strip.map(s=>s.stripDistanceM)),stripNoticeSamples:strip.filter(s=>s.stripDistanceM>POLICY.stripDistanceNoticeM).length},warnings,autoIntent};
}

export async function analyzePackage(bytes){
 need(bytes.length<=POLICY.maxSourceBytes,'SOURCE32MIB');
 const verification=verifyPackage(bytes),bundle=JSON.parse(bytes),read=n=>Buffer.from(bundle.files[n].base64,'base64').toString();
 need(verification.source==='OBSERVED_OWNED_SITL'||verification.source==='MOCK_PROTOCOL_NOT_ARDUPILOT','UNSUPPORTED_FLIGHT_SOURCE');
 const review=JSON.parse(read('flight/review.json'));
 need(stable(review)===stable(bundle.review),'OUTER_REVIEW_DIFFERS');
 const rows=read('flight/raw.jsonl').trimEnd().split('\n').map(JSON.parse),wal=read('workspace/journal.jsonl').trimEnd().split('\n').map(JSON.parse);
 const bound=wal.filter(r=>r.kind==='BETA_MODEL_BOUND'&&r.data.workbenchSha256===review.workbenchSha256);
 need(bound.length===1,'ONE_MATCHING_MODEL');
 const input=bound[0].data.input,plan=createPlan(await parseKml(input.kml),input),prep=await prepareSITL(plan,{confirmSyntheticHomeAmsl10:true});
 need(Object.keys(prep.binding).every(k=>prep.binding[k]===review[k]&&bound[0].data.binding[k]===review[k]),'RECONSTRUCTED_MODEL_PLAN_BINDING');
 const telemetry=analyzeTelemetry(rows,review,plan);
 const captures=[];
 for(const n of Object.keys(bundle.files).filter(n=>n.endsWith('/sidecar.json'))){
  const s=JSON.parse(read(n)),prefix=n.slice(0,-12),image=bundle.files[prefix+'original.jpg'];
  need(s.context.flightRun===review.run&&s.context.flightBoot===review.boot&&s.context.modelSha256===review.modelSha256&&s.context.planSha256===review.planSha256,'MEDIA_BOOT_CONTEXT');
  need(s.sourceKind==='SYNTHETIC'&&s.actualImages===0&&s.position?.qualifiedForSurvey===false&&image&&s.file?.sha256===image.sha256&&s.file?.sizeBytes===image.bytes,'MEDIA_PROVENANCE');
  captures.push({id:s.captureId,file:prefix+'original.jpg',sha256:image.sha256,sourceKind:s.sourceKind,actualImages:0,frameId:s.frameId,position:s.position,timing:s.timing,reference:{file:n},imageQuality:'NOT_QUALIFIED',surveyCoverage:'UNKNOWN'});
 }
 const findings=[];
 const add=(id,severity,title,explanation,proposal,evidence)=>findings.push({id,severity,title,explanation,proposal,evidence,engine:'DETERMINISTIC_RULES_V1',command:null});
 if(!review.accepted)add('INCOMPLETE','warning','Phiên chưa hoàn tất','Hồ sơ nguồn không ghi nhận hoàn tất nhiệm vụ.','Đọc lại nguyên nhân gián đoạn trước khi lập nhiệm vụ mới.',[{file:'flight/review.json',field:'reason',value:review.reason}]);
 if(telemetry.gaps.length)add('GAPS','warning','Có khoảng trống quan sát','Không nối đường hoặc tính gia tốc qua các khoảng trống này.','Đối chiếu log và trạng thái liên kết tại các mốc được đánh dấu.',telemetry.gaps.map(g=>({file:g.file,record:g.record,previousRecord:g.previousRecord,id:g.id})));
 else add('SAMPLED','info','Chuỗi vị trí không có khoảng trống vượt ngưỡng','Kết luận chỉ áp dụng dữ liệu và ngưỡng tham chiếu trong báo cáo.','Dùng timeline để xem từng mẫu gốc.',[{file:'flight/raw.jsonl',records:[telemetry.trace[0].record,telemetry.trace.at(-1).record]}]);
 if(telemetry.metrics.stripNoticeSamples)add('STRIP','notice','Có mẫu cách dải khảo sát hơn 2 m','Đo tới dải khảo sát gần nhất khi AUTO, armed và ở vùng cao độ tham chiếu; không phải sai số bám tuyến đang thực thi.','Xem lại các đoạn chuyển dải, thời điểm chụp và tốc độ trước khi kết luận.',telemetry.trace.filter(s=>s.stripDistanceM>2).slice(0,12).map(s=>({file:'flight/raw.jsonl',record:s.record,distanceM:s.stripDistanceM})));
 add('MEDIA','warning','Chưa đủ bằng chứng chất lượng khảo sát',`${captures.length} ảnh tổng hợp, 0 ảnh thực. Định vị là tham chiếu nhận trên host; thời điểm phơi sáng vật lý chưa biết.`,'Bổ sung ảnh gốc camera, đồng bộ thời gian và tư thế camera trước khi đánh giá độ phủ/độ nhòe bản đồ.',captures.length?captures.map(c=>c.reference):[{file:'flight/review.json',field:'actualImages',value:0}]);
 add('CONTROL','info','Đánh giá chuyển động của drone','AUTO không cung cấp bằng chứng để chấm kỹ năng người lái hay thao tác cần.','Ở bài tập manual sau này, ghi input và quyền điều khiển cùng clock trước khi chấm.',[{file:'flight/review.json',field:'source',value:review.source}]);
 const report={format:'aeris-coach01-report',version:1,sourcePackageSha256:verification.sha256,run:review.run,boot:review.boot,modelSha256:review.modelSha256,planSha256:review.planSha256,source:review.source,sourceAccepted:review.accepted,sourceReason:review.reason,rawHead:verification.rawHead,rawRecords:verification.rawRecords,policy:POLICY,operational:false,authorityRestorable:false,ai:{mode:'DETERMINISTIC_BASELINE',learnedModel:false,llmCalls:0,provider:null,controlAuthority:false,humanProductivityComparison:'NOT_MEASURED'},verification:{integrity:'HASH_CHAIN_VERIFIED_NOT_SOURCE_AUTHENTICATED',reconstructedPlan:true,video:verification.videoQuality},plan:{name:plan.acquisition.feature.name,origin:plan.origin,home:plan.home,regions:plan.regions,legs:plan.legs,shots:plan.shots.map(s=>({id:s.id,x:s.x,y:s.y})),plannedPhotos:plan.shots.length,plannedAltitudeRelativeHomeM:input.options.altitudeAglM,altitudeScope:'RELATIVE_HOME_ON_EXPLICIT_SYNTHETIC_FLAT_NOT_GENERAL_AGL',plannedSpeedMS:input.options.speedMS},telemetry,inspection:{actualImages:0,syntheticImages:captures.length,captures,realCoveragePct:null,realGsdCm:null,blurQualification:'UNKNOWN',overlapQualification:'UNKNOWN',positionQualification:'HOST_REFERENCE_NOT_SURVEY',photogrammetry:'NOT_IMPLEMENTED'},findings,limits:['No learned model or AI flight controller','No pilot skill score from AUTO','Local planar approximation <=2500m, no exact route compliance','Relative Home is not generally AGL; synthetic flat fixture only','No calibrated physical Hera dynamics or sensor perception','No physical media, measured exposure sync or real survey quality']};
 return{...report,sha256:hash(stable(report))};
}

export function verifyReport(report){const{sha256,...body}=report;need(report.format==='aeris-coach01-report'&&sha256===hash(stable(body))&&report.operational===false&&report.authorityRestorable===false&&report.ai.controlAuthority===false,'REPORT_DIGEST_OR_SCOPE');return sha256;}
export async function receiveReport(bytes,source){const report=JSON.parse(bytes);verifyReport(report);need(hash(source)===report.sourcePackageSha256,'REPORT_SOURCE_DIGEST');const computed=await analyzePackage(source);need(stable(computed)===stable(report),'REPORT_RECOMPUTE_MISMATCH');return{status:'VERIFIED_RECOMPUTED',sha256:report.sha256,run:report.run,authorityRestorable:false,sourceAuthenticated:false};}
