/** Capability seam. Browser observations cannot establish Android hardware capability. */
export const DEVICE_FIELDS=['androidBuild','densityDpi','inputTransport','channelMap','liveVideoCodec','decoderInstances','radioModules','rtkRoute','controllerBatteryApi'];
export function capabilityProfile(observations={},context='browser-review'){
 if(!['browser-review','android-device','replay'].includes(context))throw Error('Capability context không hợp lệ.');
 const fields=Object.fromEntries(DEVICE_FIELDS.map(k=>[k,{state:'unknown',value:null,source:null}]));
 for(const[k,v]of Object.entries(observations)){
  if(!DEVICE_FIELDS.includes(k)||!v||v.state!=='observed'||typeof v.source!=='string'||!v.source.trim()||!Number.isFinite(v.atMs)||v.atMs<0||v.value===undefined||v.value===null)throw Error('Observation cần source/thời điểm/value hợp lệ.');
  if(context==='browser-review')throw Error('Browser không xác minh capability HeraHub.');
  fields[k]=structuredClone(v);
 }
 return {target:'RtR HeraHub',context,operational:false,fields};
}
/** Input trace seam; no physical flight bindings are invented. */
export class InputAdapter{
 constructor(){this.mapping=new Map();this.attached=false;this.calibration=null;}
 attach({transport,source,calibration}){if(typeof transport!=='string'||!transport||typeof source!=='string'||!source||typeof calibration!=='string'||!calibration)throw Error('Cần transport, source và calibration version.');this.attached=true;this.calibration=calibration;}
 bind(channel,action){if(!['select-next-transect','select-previous-transect','capture-request'].includes(action)||typeof channel!=='string'||!channel)throw Error('Chưa hỗ trợ binding này.');this.mapping.set(channel,action);}
 detach(){this.attached=false;}
 interpret({channel,pressed}){if(!this.attached||pressed!==true||!this.mapping.has(channel))return null;return {action:this.mapping.get(channel),source:'input-adapter',calibration:this.calibration,operational:false};}
}
