/** Separate PBR payload video surface. Observer HUD is never its source. */
import * as T from '/vendor/three.module.js';
import {cameraBasisNed,nedToRender,need} from './observer.mjs';
export class PayloadVideoSurface{
 constructor(display,{canvas,width=1280,height=720,sensorHeightMm=24,focalLengthMm=35}={}){
  need(display&&canvas&&width===1280&&height===720,'PAYLOAD_VIDEO_SURFACE_CONTRACT');
  need(Number.isFinite(sensorHeightMm)&&sensorHeightMm>0&&sensorHeightMm<=100&&Number.isFinite(focalLengthMm)&&focalLengthMm>=4&&focalLengthMm<=500,'PAYLOAD_VIDEO_INTRINSICS');
  this.display=display;this.canvas=canvas;this.width=width;this.height=height;this.closed=false;
  this.renderer=new T.WebGLRenderer({canvas,antialias:false,alpha:false});this.renderer.setPixelRatio(1);this.renderer.setSize(width,height,false);this.renderer.outputColorSpace=T.SRGBColorSpace;this.renderer.toneMapping=T.ACESFilmicToneMapping;this.renderer.toneMappingExposure=display.scene.renderer.toneMappingExposure;
  this.camera=new T.PerspectiveCamera(2*Math.atan(sensorHeightMm/(2*focalLengthMm))*180/Math.PI,width/height,.02,1000);
  this.intrinsics={width,height,sensorHeightMm,focalLengthMm,verticalFovDeg:this.camera.fov};
  this.target=new T.WebGLRenderTarget(width,height);this.postScene=new T.Scene();this.postCamera=new T.OrthographicCamera(-1,1,1,-1,0,1);
  this.postMaterial=new T.ShaderMaterial({uniforms:{source:{value:this.target.texture}},depthTest:false,depthWrite:false,toneMapped:false,vertexShader:'varying vec2 uv0; void main(){uv0=uv;gl_Position=vec4(position.xy,0.0,1.0);}',fragmentShader:'uniform sampler2D source;varying vec2 uv0;void main(){vec3 c=texture2D(source,uv0).rgb;float l=clamp(dot(c,vec3(.2126,.7152,.0722)),0.0,1.0);gl_FragColor=vec4(clamp(2.0*l,0.0,1.0),max(0.0,1.0-abs(2.0*l-1.0)),1.0-l,1.0);}'});
  this.postGeometry=new T.PlaneGeometry(2,2);this.postScene.add(new T.Mesh(this.postGeometry,this.postMaterial));
 }
 async warmup(){
  need(!this.closed,'PAYLOAD_VIDEO_CLOSED');
  // Deliberate graphics preparation before source-frame admission. These
  // draws are not exposures or FDM frames and must never receive frame proofs.
  if(this.renderer.compileAsync){await this.renderer.compileAsync(this.display.scene.scene,this.camera);await this.renderer.compileAsync(this.postScene,this.postCamera);}
  else{this.renderer.compile(this.display.scene.scene,this.camera);this.renderer.compile(this.postScene,this.postCamera);}
  this.renderer.setRenderTarget(null);this.renderer.render(this.display.scene.scene,this.camera);this.renderer.setRenderTarget(this.target);this.renderer.render(this.display.scene.scene,this.camera);this.renderer.setRenderTarget(null);this.renderer.render(this.postScene,this.postCamera);this.renderer.getContext().finish();
  this.warmed=true;return{prepared:true,source:'GRAPHICS_ONLY_NO_FDM_EXPOSURE',frameProofProduced:false};
 }
 render({pitchDeg=-45,yawDeg=0,mountFrdM=[0,0,.1],feed='rgb',sensorHeightMm=this.intrinsics.sensorHeightMm,focalLengthMm=this.intrinsics.focalLengthMm}={}){
  need(!this.closed&&!document.hidden,'PAYLOAD_VIDEO_NOT_FOREGROUND');const state=this.display.gate.state();need(state.fresh,'PAYLOAD_VIDEO_STALE_FRAME');
  need(['rgb','thermal-look'].includes(feed),'PAYLOAD_VIDEO_FEED');
  need(Number.isFinite(sensorHeightMm)&&sensorHeightMm>0&&sensorHeightMm<=100&&Number.isFinite(focalLengthMm)&&focalLengthMm>=4&&focalLengthMm<=500,'PAYLOAD_VIDEO_INTRINSICS');
  this.camera.fov=2*Math.atan(sensorHeightMm/(2*focalLengthMm))*180/Math.PI;this.camera.updateProjectionMatrix();this.intrinsics={...this.intrinsics,sensorHeightMm,focalLengthMm,verticalFovDeg:this.camera.fov};
  const f=state.frame,mount=mountFrdM.slice(),basis=cameraBasisNed(f.quaternionWxyz,{pitchDeg,yawDeg,mountFrdM:mount}),p=f.positionNedM.map((x,i)=>x+basis.mountNedM[i]),world=nedToRender(p),forward=nedToRender(basis.forwardNed),up=nedToRender(basis.upNed),oldPose=this.display.scene.pose;
  this.camera.position.fromArray(world);this.camera.up.fromArray(up);this.camera.lookAt(new T.Vector3(...world).add(new T.Vector3(...forward)));this.camera.updateMatrixWorld(true);
  try{this.display.scene.setPose({position:f.positionNedM,quaternion:f.quaternionWxyz,rpmEstimated:f.rpmEstimated??[0,0,0,0]});this.renderer.setRenderTarget(feed==='thermal-look'?this.target:null);this.renderer.render(this.display.scene.scene,this.camera);if(feed==='thermal-look'){this.renderer.setRenderTarget(null);this.renderer.render(this.postScene,this.postCamera);}}
  finally{this.renderer.setRenderTarget(null);if(oldPose)this.display.scene.setPose(oldPose);}
  need(this.display.gate.state().fresh,'PAYLOAD_VIDEO_SOURCE_EXPIRED_DURING_RENDER');
  return{format:'aeris-sim-payload-video-frame',version:1,source:'SEPARATE_PBR_PAYLOAD_CAMERA',context:f.context,frame:f.frame,simulationTimeS:f.simulationTimeS,sampleHostNs:f.sampleHostNs,rawRef:f.rawRef,aircraftPositionNedM:f.positionNedM,aircraftQuaternionWxyz:f.quaternionWxyz,cameraPositionNedM:p,gimbal:{pitchDeg,yawDeg,mountFrdM:mount},intrinsics:{...this.intrinsics},feed,radiometric:false,hardwareImages:0,HeraCalibrated:false};
 }
 close(){if(this.closed)return;this.closed=true;this.target.dispose();this.postGeometry.dispose();this.postMaterial.dispose();this.renderer.dispose();}
}
