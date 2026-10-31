import {randomUUID} from 'node:crypto';
export const DEVICES=Object.freeze([
 {id:'mock-survey',label:'RGB khảo sát · mock',cameraId:'SYNTHETIC-RGB-01',feed:'rgb',profile:'SONY_PIXY_CONTRACT_MOCK_NOT_VENDOR_DRIVER',firmware:'mock-1',capabilities:['gimbal','iso','capture'],radiometry:false},
 {id:'mock-ir',label:'IR quan sát · mock',cameraId:'SYNTHETIC-IR-01',feed:'thermal',profile:'EOIR_CONTRACT_MOCK_NOT_THERMAL_HARDWARE',firmware:'mock-1',capabilities:['gimbal','capture'],radiometry:false}
]);
export class MockAdapter {
 constructor(){this.bootId=randomUUID();this.connected=true;this.states=new Map(DEVICES.map(d=>[d.id,{pitchDeg:-45,yawDeg:0,iso:d.feed==='rgb'?200:null}]));this.fault='none';this.calls=0;}
 discover(){if(!this.connected)throw Error('LINK_DOWN');return DEVICES.map(d=>({...structuredClone(d),bootId:this.bootId,sourceKind:'SYNTHETIC',frame:'BODY_RELATIVE_DEGREES'}));}
 invoke(id,action,args){if(!this.connected)throw Error('LINK_DOWN');this.calls++;const s=this.states.get(id);if(!s)throw Error('UNKNOWN_DEVICE');const fault=this.fault;this.fault='none';
  if(action==='gimbal')Object.assign(s,args);if(action==='iso')s.iso=args.iso;
  return {deviceId:fault==='wrongTarget'?'WRONG_DEVICE':id,bootId:this.bootId,action,
    ack:true,observed:fault==='lostFeedback'?null:structuredClone(s),fault,sourceKind:'SYNTHETIC'};
 }
 reboot(){this.bootId=randomUUID();this.connected=true;for(const [id]of this.states)this.states.set(id,{pitchDeg:-45,yawDeg:0,iso:id==='mock-survey'?200:null});this.fault='none';}
}
