import * as T from '/vendor/three.module.js';
import {FlightScene} from '/scene/flight-scene.mjs';
import {RotorAudio} from '/scene/rotor-audio.mjs';
import {SceneGate,cameraBasisNed,nedToRender,need} from './observer.mjs';

class ManagedFlightScene extends FlightScene{
 bind(){this.listeners=[];const on=(node,event,fn,options)=>{node.addEventListener(event,fn,options);this.listeners.push(()=>node.removeEventListener(event,fn,options));};let drag=null;
  on(this.canvas,'pointerdown',e=>{drag=[e.clientX,e.clientY];this.canvas.setPointerCapture(e.pointerId);});
  on(this.canvas,'pointermove',e=>{if(!drag)return;this.azimuth-=(e.clientX-drag[0])*.005;this.elevation=Math.max(-.12,Math.min(1.4,this.elevation+(e.clientY-drag[1])*.004));drag=[e.clientX,e.clientY];});
  on(this.canvas,'pointerup',()=>drag=null);on(this.canvas,'pointercancel',()=>drag=null);
  on(this.canvas,'wheel',e=>{e.preventDefault();this.distance=Math.max(1.15,Math.min(80,this.distance*Math.exp(e.deltaY*.001)));},{passive:false});on(window,'resize',()=>this.resize());
 }
 disposeEvents(){for(const off of this.listeners)off();this.listeners=[];}
}

/** A view of committed simulation state. It has no flight command interface. */
export class SimulationDisplay{
 constructor({canvas,binding,mode='LIVE',sourceBinding=null,onState=()=>{}}){
  this.canvas=canvas;this.gate=new SceneGate(binding,{mode,sourceBinding});this.scene=new ManagedFlightScene(canvas);this.audio=new RotorAudio();this.onState=onState;this.mode=mode;this.running=false;this.background=document.hidden;this.lastDraw=performance.now();this.error=null;this.disposed=false;
  this.visibility=()=>{this.background=document.hidden;if(this.background){this.audio.mute();this.gate.suspend();}else{try{this.gate.resume();}catch(e){this.error=e.message;}}};
  document.addEventListener('visibilitychange',this.visibility);
  this.lost=e=>{e.preventDefault();this.error='WEBGL_CONTEXT_LOST';this.audio.mute();this.gate.suspend();};canvas.addEventListener('webglcontextlost',this.lost);
 }
 async load(){await this.scene.load();this.scene.setView('chase');
  // The reference profile is a declared flat training field. Preserve actual
  // metre scale while extending the immutable engine's 36 m ground instance.
  for(const o of this.scene.scene.children){if(o.isMesh&&o.geometry?.parameters?.width===36&&o.geometry?.parameters?.height===36){o.geometry.dispose();o.geometry=new T.PlaneGeometry(420,420);for(const k of ['map','normalMap','roughnessMap'])if(o.material[k]){o.material[k].repeat.set(140,140);o.material[k].needsUpdate=true;}}}
  this.running=true;this.draw();return this;
 }
 accept(frame,bracket){need(!this.disposed&&!this.background,'SCENE_VIEW_NOT_FOREGROUND');const result=this.gate.accept(frame,bracket);this.error=null;return result;}
 draw(){if(!this.running||this.disposed)return;const now=performance.now(),dt=Math.max(0,Math.min(.1,(now-this.lastDraw)/1000));this.lastDraw=now;
  try{const s=this.gate.state(),pose=this.gate.pose();if(pose&&s.fresh&&!this.background)this.scene.setPose(pose);
   this.audio.update({rpmEstimated:s.frame?.rpmEstimated,armed:s.frame?.ap.armed===true,fresh:s.fresh&&s.apFresh&&!this.background,ended:!this.running});
   if(!this.background)this.scene.draw(s.fresh?dt:0);this.onState({fresh:s.fresh,ageUpperMs:s.ageUpperMs,source:this.mode,frame:s.frame?.frame??null,rawRef:s.frame?.rawRef??null,audio:this.audio.snapshot(),renderedPositionNedM:this.scene.pose?.position??null,error:this.error??s.failure,flightAuthority:false});
  }catch(e){this.error=e.message;this.audio.mute();this.onState({fresh:false,error:this.error,flightAuthority:false});}
  this.animation=requestAnimationFrame(()=>this.draw());
 }
 async enableAudio(){need(!this.disposed&&!document.hidden,'AUDIO_FOREGROUND_GESTURE_REQUIRED');await this.audio.enable();}
 async disableAudio(){await this.audio.disable();}
 setView(view){need(['hero','chase','range'].includes(view),'SCENE_VIEW');this.scene.setView(view);}
 /** Render a payload-camera view of one exact committed state. Never an HUD crop.
  * This is a synthetic exposure at simulation frame N, not a physical camera.
  */
 async capturePayload({width=1280,height=720,sensorHeightMm=24,focalLengthMm=35,pitchDeg=-90,yawDeg=0,mountFrdM=[0,0,.1],feed='rgb'}={}){
  mountFrdM=mountFrdM.slice();
  const state=this.gate.state();need(state.fresh&&!this.background&&!this.disposed,'PAYLOAD_RENDER_FRESH_FRAME_REQUIRED');
  need(Number.isInteger(width)&&Number.isInteger(height)&&width>=64&&height>=64&&width<=1920&&height<=1080,'PAYLOAD_RENDER_SIZE');
  need(typeof sensorHeightMm==='number'&&Number.isFinite(sensorHeightMm)&&sensorHeightMm>0&&sensorHeightMm<=100&&typeof focalLengthMm==='number'&&Number.isFinite(focalLengthMm)&&focalLengthMm>=4&&focalLengthMm<=500,'PAYLOAD_INTRINSICS');
  need(['rgb','thermal-look'].includes(feed),'PAYLOAD_SYNTHETIC_FEED');
  const f=state.frame,oldPose=this.scene.pose;const basis=cameraBasisNed(f.quaternionWxyz,{pitchDeg,yawDeg,mountFrdM});
  const p=f.positionNedM.map((x,i)=>x+basis.mountNedM[i]),world=nedToRender(p),forward=nedToRender(basis.forwardNed),up=nedToRender(basis.upNed);
  const fov=2*Math.atan(sensorHeightMm/(2*focalLengthMm))*180/Math.PI,camera=new T.PerspectiveCamera(fov,width/height,.02,1000);
  camera.position.fromArray(world);camera.up.fromArray(up);camera.lookAt(new T.Vector3(...world).add(new T.Vector3(...forward)));camera.updateMatrixWorld(true);
  const renderer=this.scene.renderer,target=new T.WebGLRenderTarget(width,height,{depthBuffer:true}),previous=renderer.getRenderTarget(),pixels=new Uint8Array(width*height*4);target.texture.colorSpace=T.SRGBColorSpace;
  try{this.scene.setPose({position:f.positionNedM,quaternion:f.quaternionWxyz,rpmEstimated:f.rpmEstimated??[0,0,0,0]});renderer.setRenderTarget(target);renderer.render(this.scene.scene,camera);renderer.readRenderTargetPixels(target,0,0,width,height,pixels);}
  finally{renderer.setRenderTarget(previous);target.dispose();if(oldPose)this.scene.setPose(oldPose);}
  const canvas=document.createElement('canvas');canvas.width=width;canvas.height=height;const ctx=canvas.getContext('2d'),image=ctx.createImageData(width,height),stride=width*4;
  for(let y=0;y<height;y++)image.data.set(pixels.subarray((height-y-1)*stride,(height-y)*stride),y*stride);
  if(feed==='thermal-look')for(let i=0;i<image.data.length;i+=4){const l=(.2126*image.data[i]+.7152*image.data[i+1]+.0722*image.data[i+2])/255;image.data[i]=Math.round(255*Math.min(1,Math.max(0,2*l)));image.data[i+1]=Math.round(255*Math.max(0,1-Math.abs(2*l-1)));image.data[i+2]=Math.round(255*(1-l));}
  ctx.putImageData(image,0,0);const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));need(blob,'PAYLOAD_RENDER_ENCODE_FAILED');const bytes=new Uint8Array(await blob.arrayBuffer()),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');
  return{bytes,metadata:{format:'aeris-simulated-payload-exposure',version:1,source:'SEPARATE_PBR_PAYLOAD_CAMERA_RENDER_PASS',mode:this.mode,context:f.context,frame:f.frame,simulationTimeS:f.simulationTimeS,sampleHostNs:f.sampleHostNs,rawRef:f.rawRef,cameraPositionNedM:p,aircraftPositionNedM:f.positionNedM,aircraftQuaternionWxyz:f.quaternionWxyz,gimbal:{pitchDeg,yawDeg,mountFrdM},intrinsics:{width,height,sensorHeightMm,focalLengthMm,verticalFovDeg:fov},feed,radiometric:false,hardwareImages:0,image:{mime:'image/png',bytes:bytes.length,sha256:hash},geotagScope:'SIMULATED_EXPOSURE_AT_COMMITTED_FRAME_NOT_PHYSICAL_SHUTTER_TIME',HeraCalibrated:false}};
 }
 metrics(){return{...this.scene.metrics(),scope:'READ_ONLY_COMMITTED_SIMULATION_VIEW',source:this.mode,gate:this.gate.state(),audio:this.audio.snapshot(),flightCommandsSent:0,syntheticReferenceModelNotHeraCalibration:true};}
 async close(){if(this.disposed)return;this.running=false;this.disposed=true;cancelAnimationFrame(this.animation);this.gate.close();await this.audio.disable();document.removeEventListener('visibilitychange',this.visibility);this.canvas.removeEventListener('webglcontextlost',this.lost);this.scene.disposeEvents();
  const textures=new Set(),geometries=new Set(),materials=new Set();if(this.scene.scene.environment?.isTexture)textures.add(this.scene.scene.environment);
  this.scene.scene.traverse(o=>{if(o.geometry)geometries.add(o.geometry);for(const m of (Array.isArray(o.material)?o.material:o.material?[o.material]:[])){materials.add(m);for(const v of Object.values(m))if(v?.isTexture)textures.add(v);}});
  for(const x of textures)x.dispose();for(const x of geometries)x.dispose();for(const x of materials)x.dispose();for(const p of this.scene.composer.passes)p.dispose?.();this.scene.composer.dispose();this.scene.sun.shadow.dispose();this.scene.renderer.dispose();
 }
}

/** One outstanding passive request; no polling queue or control-path callbacks. */
export function pollScene(display,{url='/api/scene',intervalMs=50,fetcher=fetch}={}){
 need(Number.isInteger(intervalMs)&&intervalMs>=16&&intervalMs<=1000,'SCENE_POLL_INTERVAL');let stopped=false,controller=null,timer=null;
 const next=async()=>{if(stopped)return;if(document.hidden){timer=setTimeout(next,intervalMs);return;}
  const started=performance.now();controller=new AbortController();const deadline=setTimeout(()=>controller.abort(),250);
  try{const r=await fetcher(url,{signal:controller.signal,cache:'no-store'});need(r.ok,'SCENE_SOURCE_UNAVAILABLE');const text=await r.text();need(text.length<=32768,'SCENE_RESPONSE_BOUND');const frame=JSON.parse(text);
   if(frame.available===false&&frame.flightAuthority===false&&frame.format===undefined){display.audio.mute();display.error='SCENE_SOURCE_NOT_AVAILABLE';return;}
   display.accept(frame,{requestStartedBrowserMs:started,receivedBrowserMs:performance.now()});}
  catch(e){display.audio.mute();display.error=e.name==='AbortError'?'SCENE_SOURCE_TIMEOUT':e.message;}
  finally{clearTimeout(deadline);controller=null;if(!stopped)timer=setTimeout(next,Math.max(0,intervalMs-(performance.now()-started)));}
 };next();return()=>{stopped=true;clearTimeout(timer);controller?.abort();};
}

/** One passive SSE stream. Its events retain the original calibrated Node send
 * time; receive time is never substituted for source/transport freshness. */
export function streamScene(display,{url='http://127.0.0.1:8896/api/scene-events',getClock,EventSourceType=EventSource}={}){
 need(typeof getClock==='function','SCENE_STREAM_CLOCK_PROVIDER');let stopped=false;const source=new EventSourceType(url);
 const close=reason=>{if(stopped)return;stopped=true;source.close();display.audio.mute();display.gate.suspend();display.error=reason;};
 source.onmessage=event=>{if(stopped||document.hidden)return;const receivedBrowserMs=performance.now();try{need(typeof event.data==='string'&&event.data.length<=32768,'SCENE_STREAM_MESSAGE_BOUND');const q=JSON.parse(event.data);need(q.format==='aeris-scene-event'&&q.version===1,'SCENE_STREAM_ENVELOPE');if(q.frame?.available===false){display.audio.mute();display.error='SCENE_SOURCE_NOT_AVAILABLE';return;}display.accept(q.frame,{receivedBrowserMs,eventClock:getClock(),serverSentNodeMs:q.serverSentNodeMs});}catch(e){close(e.message);}};
 source.onerror=()=>close('SCENE_STREAM_EOF_NO_RECONNECT');return()=>{if(!stopped){stopped=true;source.close();}};
}
