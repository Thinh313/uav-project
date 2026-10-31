import{connectMedia,assertMediaPacket}from'./client.mjs';
import{decodePacket}from'./relay-core.mjs';
const keys=['run','boot','configId','feed','profileId','viewerId'];
export const exactKeySession=(a,b)=>!!a&&!!b&&keys.every(k=>typeof a[k]==='string'&&a[k].length>0&&a[k]===b[k]);
const sha=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
async function bounded(work,ms,error){let timer;try{return await Promise.race([Promise.resolve().then(work),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error(error)),ms);})]);}finally{clearTimeout(timer);}}
/** Decode the retained actual network key only; never draws/counts a video frame. */
export async function decodeRetainedNetworkKey({packet,packetSha256,keySha256,session,decoderConfig,isCurrent=()=>true}){
 const started=performance.now();let decoder,current=true,codecError=null;const result={decoderConfig:structuredClone(decoderConfig),configSupport:null,outputs:0,output:null,flushMs:null,elapsedMs:null,status:'NOT_RUN',videoAcceptance:false};
 try{
  if(!isCurrent())throw Error('DIAGNOSTIC_SESSION_ENDED');if(packet.byteLength>4*2**20||await sha(packet)!==packetSha256)throw Error('DIAGNOSTIC_PACKET_SHA');
  const{meta,data}=decodePacket(packet);assertMediaPacket(meta,session);if(meta.type!=='key'||await sha(data)!==keySha256)throw Error('DIAGNOSTIC_EXACT_NETWORK_KEY');
  result.configSupport=await bounded(()=>VideoDecoder.isConfigSupported(decoderConfig),1500,'DIAGNOSTIC_SUPPORT_1500MS_TIMEOUT');if(!current||!isCurrent())throw Error('DIAGNOSTIC_SESSION_ENDED');if(!result.configSupport.supported)throw Error('DIAGNOSTIC_CONFIG_UNSUPPORTED');
  decoder=new VideoDecoder({output:frame=>{try{if(!current||!isCurrent())return;if(frame.timestamp!==meta.timestampUs)throw Error('DIAGNOSTIC_OUTPUT_TIMESTAMP');result.outputs++;result.output={timestampUs:frame.timestamp,width:frame.codedWidth,height:frame.codedHeight,atMs:performance.now()-started};}catch(e){codecError=e.message;}finally{frame.close();}},error:e=>{if(current&&isCurrent())codecError=String(e.message).slice(0,180);}});
  decoder.configure(decoderConfig);decoder.decode(new EncodedVideoChunk({type:'key',timestamp:meta.timestampUs,data}));const flushStarted=performance.now();await bounded(()=>decoder.flush(),1500,'DIAGNOSTIC_FLUSH_1500MS_TIMEOUT');result.flushMs=performance.now()-flushStarted;
  if(!current||!isCurrent())throw Error('DIAGNOSTIC_SESSION_ENDED');if(codecError)throw Error(codecError);if(result.outputs!==1||result.output.width!==1280||result.output.height!==720)throw Error('DIAGNOSTIC_EXACT_KEY_OUTPUT_REQUIRED');result.status='EXACT_NETWORK_KEY_DECODED';
 }catch(e){result.status='FAILED_OR_TIMEOUT';result.error=String(e.message).slice(0,180);}finally{current=false;try{decoder?.close();}catch{}result.elapsedMs=performance.now()-started;}
 return result;
}
/** One explicit two-condition diagnostic; source remains stopped and no viewer restarts. */
export async function diagnoseSameNetworkKey({mediaOrigin,session,sourceChallenge,isCurrent=()=>true,onStage=()=>{}}){
 if(!isCurrent())throw Error('DIAGNOSTIC_SESSION_ENDED');const client=await connectMedia('viewer',mediaOrigin);const armed=await client.json('diagnostic-arm',{session});const id=armed.id,started=performance.now();
 onStage('Chờ một keyframe mới từ nguồn mạng…');let captured;
 const target=()=>{if(!isCurrent())throw Error('DIAGNOSTIC_SESSION_ENDED');};
 while(performance.now()-started<=4500){target();captured=await client.json('diagnostic-status',{id,session});if(captured.state==='CAPTURED')break;if(captured.state!=='ARMED'&&captured.state!=='CAPTURING')throw Error('DIAGNOSTIC_CAPTURE_'+captured.state);await new Promise(r=>setTimeout(r,100));}
 if(captured?.state!=='CAPTURED')throw Error('DIAGNOSTIC_CAPTURE_4500MS_TIMEOUT');target();
 const packet=new Uint8Array(await(await client.post('diagnostic-key',{id,session})).arrayBuffer());if(packet.length!==captured.packetBytes||await sha(packet)!==captured.packetSha256)throw Error('DIAGNOSTIC_CAPTURE_SHA');const parsed=decodePacket(packet);if(await sha(parsed.data)!==captured.keySha256)throw Error('DIAGNOSTIC_KEY_SHA');assertMediaPacket(parsed.meta,session);
 const profile=client.bootstrap.profiles.profiles.find(p=>p.id===session.profileId);if(!profile)throw Error('DIAGNOSTIC_PROFILE');const decoderConfig={codec:profile.codec,codedWidth:1280,codedHeight:720,optimizeForLatency:true,hardwareAcceleration:'prefer-software'};
 const report={format:'FIELD02_SAME_NETWORK_KEY_DIAGNOSTIC',id,serverBoot:client.bootstrap.serverBoot,session:{...session},packetSha256:captured.packetSha256,keySha256:captured.keySha256,packetBytes:packet.length,keyBytes:parsed.data.length,meta:parsed.meta,decoderConfig,startedBrowserMs:started,cases:[],videoAcceptance:false,authority:'NONE',physicalLatency:'NOT_MEASURED',encoderDecoderBackend:'UNKNOWN_PREFER_SOFTWARE_REQUEST_ONLY',sourceKind:'SYNTHETIC',actualImages:0,scope:'SAME_RETAINED_ACTUAL_NETWORK_KEY_OFFLINE_DECODE_NOT_STREAM_FPS_OR_CAMERA_EXPOSURE'};
 for(const condition of['ACTIVE','STOPPED']){
  target();await client.json('diagnostic-status',{id,session});onStage(condition==='ACTIVE'?'Đo đúng key mạng khi nguồn đang encode…':'Dừng nguồn có xác nhận rồi đo lại đúng key…');
  const item={producerCondition:condition,acknowledgements:[],result:null,conditionVerified:false};report.cases.push(item);
  try{item.acknowledgements.push(await sourceChallenge({action:condition==='ACTIVE'?'STATUS':'STOP',condition,id,session}));target();item.result=await decodeRetainedNetworkKey({packet,packetSha256:captured.packetSha256,keySha256:captured.keySha256,session,decoderConfig,isCurrent});target();item.acknowledgements.push(await sourceChallenge({action:'STATUS',condition,id,session}));item.conditionVerified=true;}catch(e){item.conditionError=String(e.message).slice(0,180);}
 }
 target();report.finishedBrowserMs=performance.now();report.totalMs=report.finishedBrowserMs-started;const saved=await client.json('diagnostic-report',{id,session,report});return{report,saved};
}
