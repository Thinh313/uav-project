/** Four explicit synthetic peers, never vendor SDK/camera attestation. */
import{DEVICES as BASE,MockAdapter}from'../../../payload/gateway01/mock-adapter.mjs';
export const DEVICES=Object.freeze([...BASE,
 Object.freeze({id:'mock-phaseone',label:'RGB độ phân giải cao · giả lập',cameraId:'SYNTHETIC-HIGHRES-01',feed:'rgb',profile:'PHASE_ONE_CONTRACT_MOCK_NOT_VENDOR_DRIVER',firmware:'mock-1',capabilities:['gimbal','iso','capture'],radiometry:false}),
 Object.freeze({id:'mock-corona',label:'UV quan sát · giả lập',cameraId:'SYNTHETIC-UV-01',feed:'rgb',profile:'UV_LOOK_ONLY_NOT_CORONA_DISCHARGE_PHYSICS',firmware:'mock-1',capabilities:['gimbal','capture'],radiometry:false})]);
export class FourPayloadAdapter extends MockAdapter{
 constructor(){super();for(const d of DEVICES)if(!this.states.has(d.id))this.states.set(d.id,{pitchDeg:-45,yawDeg:0,iso:d.capabilities.includes('iso')?200:null});}
 discover(){if(!this.connected)throw Error('LINK_DOWN');return DEVICES.map(d=>({...structuredClone(d),bootId:this.bootId,sourceKind:'SYNTHETIC',frame:'BODY_RELATIVE_DEGREES'}));}
}
