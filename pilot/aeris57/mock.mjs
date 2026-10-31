// Explicit synthetic dependency for tests. Never imports FixedBackend or opens an AP socket.
export class MockBackend{
 constructor(){this.mock=true;this.calls=[];this.failure=null;this.s={simulation:true,controllerActive:false,verifying:false,busy:false,run:null,session:null,boot:null,capacity:{admitted:true,retainedBytes:0,quotaBytes:4*2**30},vehicle:null,physics:null,input:null,challenge:'mock-challenge',actualImages:0,fullG1Accepted:false};}
 async get(route){if(route==='state')return structuredClone(this.s);if(route==='history')return[];if(route.startsWith('history/'))throw Error('NO_MOCK_RECORD');throw Error('MOCK_GET_ROUTE')}
 async post(route,d){this.calls.push({route,body:structuredClone(d)});if(this.failure===route)throw Error('WRITE_OUTCOME_UNKNOWN_NO_RETRY:MOCK_FAULT');if(route==='start'){this.s={...this.s,controllerActive:true,run:'MOCK57',session:'mock-session',boot:'mock-boot',remainingHostSeconds:120,profile:{load:d.load,wind:d.wind},vehicle:{mode:'GUIDED',armed:false,connected:true,preflight:[{id:'firmware',pass:true,detail:'SYNTHETIC_ONLY'}]},physics:{frame:0,timestamp:0,position:[0,0,0],velocity:[0,0,0],quaternion:[1,0,0,0],rpmEstimated:[0,0,0,0],massKg:d.load==='empty'?3:4,ground:true,serverAgeMs:{low:0,high:1}},input:{state:'REVOKED',reason:'MOCK',axes:[0,0,0,0]}};return structuredClone(this.s)}
  if(route==='verify-lease')return{challenge:this.s.challenge};if(route==='claim'){this.s.input.state='NEUTRAL_REQUIRED';return{lease:'mock-lease'}}
  if(route==='input'){this.s.input={...this.s.input,state:'ACTIVE',axes:d.packet.axes};return{input:this.s.input}}
  if(route==='release'){this.s.input={state:'REVOKED',reason:'MOCK_RELEASE',axes:[0,0,0,0]};return{released:true}}
  if(route==='takeoff'){this.s.vehicle.mode='LOITER';this.s.vehicle.armed=true;this.s.physics.position=[0,0,-5];this.s.physics.ground=false;this.s.physics.rpmEstimated=[4400,4400,4400,4400]}
  if(route==='land'){this.s.vehicle.mode='LAND';this.s.vehicle.armed=false;this.s.physics.position=[0,0,0];this.s.physics.ground=true;this.s.input.state='REVOKED'}
  if(route==='end'){if(this.s.vehicle.armed||!this.s.physics.ground)throw Error('LAND_BEFORE_END');this.s.controllerActive=false}
  return structuredClone(this.s)
 }
}
