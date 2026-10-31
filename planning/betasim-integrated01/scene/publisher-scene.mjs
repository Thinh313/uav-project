import {SimulationDisplay,pollScene,streamScene} from './display.mjs';
import {PayloadVideoSurface} from './payload-surface.mjs';
let display,surface,stopPoll,loading=null,audio=false;const exposureFrames=new Map(),seenExposures=new Set();let exposureBusy=false;
export async function preparePayloadSource(canvas){
 if(surface)return surface;if(loading)return loading;
 loading=(async()=>{const response=await fetch('/scene/config.json',{cache:'no-store'});if(!response.ok)throw Error('ROOT_SCENE_DESCRIPTOR_UNAVAILABLE');const descriptor=await response.json();if(descriptor.mode!=='LIVE')throw Error('ACTUAL_PUBLISHER_REQUIRES_LIVE_ROOT_SOURCE');
  const holder=document.createElement('section');holder.id='simulation-observer';holder.style.cssText='position:relative;width:100%;height:360px;overflow:hidden;border-radius:12px';const observer=document.createElement('canvas');observer.style.cssText='width:100%;height:100%;display:block;max-height:none';holder.append(observer);canvas.before(holder);
  const label=document.createElement('output');label.style.cssText='position:absolute;bottom:12px;left:16px;background:#13171a88;color:white;padding:8px 12px;border-radius:8px;backdrop-filter:blur(16px)';holder.append(label);
  display=new SimulationDisplay({canvas:observer,binding:descriptor.binding,sourceBinding:descriptor.sourceBinding,mode:'LIVE',onState:s=>{label.textContent=s.fresh?'Mô phỏng SITL · khung '+s.frame:'Nguồn mô phỏng chưa sẵn sàng · '+(s.error??'chờ trạng thái');}});await display.load();surface=new PayloadVideoSurface(display,{canvas});await surface.warmup();stopPoll=pollScene(display);
  const sound=document.createElement('button');sound.type='button';sound.textContent='Bật âm thanh mô phỏng';sound.onclick=async()=>{try{if(audio){await display.disableAudio();audio=false;}else{await display.enableAudio();audio=true;}sound.textContent=audio?'Tắt âm thanh mô phỏng':'Bật âm thanh mô phỏng';}catch(e){label.textContent=e.message;}};holder.before(sound);return surface;
 })();return loading;
}
export function renderPayloadSource(feed,{videoFrameId=null}={}){if(!surface)throw Error('PAYLOAD_SCENE_NOT_READY');const state=display.gate.state(),camera=state.frame?.payloadCamera,selected=feed==='thermal'?'thermal-look':'rgb';
 if(!camera||camera.source!=='MOCK_PAYLOAD_READBACK'||!Number.isSafeInteger(camera.revision)||camera.revision<0||typeof camera.deviceId!=='string'||camera.deviceId.length>128||camera.feed!==selected||!['pitchDeg','yawDeg','sensorHeightMm','focalLengthMm'].every(k=>typeof camera[k]==='number'&&Number.isFinite(camera[k]))||!Array.isArray(camera.mountFrdM)||camera.mountFrdM.length!==3||!camera.mountFrdM.every(Number.isFinite))throw Error('SOURCE_CAMERA_READBACK_OR_FEED_NOT_QUALIFIED');
 const metadata={...surface.render({pitchDeg:camera.pitchDeg,yawDeg:camera.yawDeg,mountFrdM:camera.mountFrdM,feed:selected,sensorHeightMm:camera.sensorHeightMm,focalLengthMm:camera.focalLengthMm}),payloadCameraRevision:camera.revision,payloadDeviceId:camera.deviceId,payloadCameraSource:camera.source};
 if(camera.cropMode!=='CENTER_CROP_16_9'||!Number.isFinite(camera.sourceSensorWidthMm)||!Number.isFinite(camera.sourceSensorHeightMm)||camera.sourceSensorWidthMm<=0||camera.sourceSensorHeightMm<=0||Math.abs(camera.sensorHeightMm-Math.min(camera.sourceSensorHeightMm,camera.sourceSensorWidthMm/(1280/720)))>1e-9)throw Error('SOURCE_CAMERA_SENSOR_CROP_CONTRACT');
 metadata.intrinsics={...metadata.intrinsics,effectiveSensorWidthMm:camera.sensorHeightMm*(1280/720),sourceSensorWidthMm:camera.sourceSensorWidthMm,sourceSensorHeightMm:camera.sourceSensorHeightMm,cropMode:camera.cropMode};
 const request=state.frame?.pendingExposure;
 if(request&&!seenExposures.has(request.requestId)&&!exposureBusy){
  if(!Number.isSafeInteger(videoFrameId)||videoFrameId<1||typeof request.requestId!=='string'||!/^[A-Za-z0-9_.:-]{1,128}$/.test(request.requestId)||request.payloadId!==camera.deviceId||!['rgb','thermal','thermal-look'].includes(request.feed)||(request.feed==='rgb'?'rgb':'thermal-look')!==selected||seenExposures.size>=32)throw Error('SOURCE_EXPOSURE_REQUEST_CONTEXT');
  seenExposures.add(request.requestId);exposureBusy=true;
  // toBlob snapshots this exact payload canvas now, before the next render.
  // No observer HUD, decoded Android frame or subsequent pose is substituted.
  const result=new Promise((resolve,reject)=>{const deadline=setTimeout(()=>reject(Error('SOURCE_EXPOSURE_ENCODE_500MS')),500);surface.canvas.toBlob(blob=>{clearTimeout(deadline);if(!blob||blob.size>2*1024*1024){reject(Error('SOURCE_EXPOSURE_JPEG_BOUND'));return;}resolve(blob);},'image/jpeg',.92);}).then(async blob=>{const bytes=new Uint8Array(await blob.arrayBuffer());let text='';for(let at=0;at<bytes.length;at+=32768)text+=String.fromCharCode(...bytes.subarray(at,at+32768));return{requestId:request.requestId,videoFrameId,metadata,jpegBase64:btoa(text)};}).finally(()=>{exposureBusy=false;});
  // Attach a rejection handler immediately; transport retrieves the original
  // outcome only after its exact frame proof is durable. No automatic retry.
  const settled=result.then(value=>({ok:true,value}),error=>({ok:false,error}));exposureFrames.set(videoFrameId,settled);
 }
 return metadata;
}
export function takeSourceExposure(videoFrameId){const q=exposureFrames.get(videoFrameId)??null;exposureFrames.delete(videoFrameId);return q;}
export function cancelSourceExposures(){exposureFrames.clear();}
export function promoteSceneToEvents(getClock){if(!display||!surface)throw Error('SCENE_NOT_PREPARED');stopPoll?.();stopPoll=streamScene(display,{getClock});}
export async function waitForPayloadSource(canvas,{feed='rgb',maximumMs=120000}={}){
 if(maximumMs!==120000)throw Error('SOURCE_PREPARATION_BOUND');await preparePayloadSource(canvas);const until=performance.now()+maximumMs;
 while(performance.now()<until){if(document.hidden)throw Error('SOURCE_PREPARATION_NOT_FOREGROUND');const s=display.gate.state(),c=s.frame?.payloadCamera;if(s.failure)throw Error(s.failure);if(s.fresh&&c?.source==='MOCK_PAYLOAD_READBACK'&&c.feed===(feed==='thermal'?'thermal-look':'rgb'))return;await new Promise(resolve=>setTimeout(resolve,50));}
 throw Error('SOURCE_PREPARATION_TIMEOUT_NO_RETRY');
}
window.addEventListener('pagehide',()=>{stopPoll?.();surface?.close();void display?.close();},{once:true});
