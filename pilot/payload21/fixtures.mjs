// Heterogeneous synthetic addresses/capabilities, not Hera as-built defaults.
export const PAYLOADS = [
  {id:'front',label:'Trước / EO + nhiệt',route:{aircraftId:'SIM-HERA',systemId:1,camera:{kind:'component',componentId:100,deviceId:0},gimbal:{managerComponentId:1,deviceId:1}},capabilities:{capture:true,zoom:true,focus:true,gimbal:true,zoomRange:[1,8],pitchRange:[-90,30],yawRange:[-120,120]},streams:[{id:'front-eo',type:'colour'},{id:'front-ir',type:'thermal'}]},
  {id:'center',label:'Giữa / khảo sát',route:{aircraftId:'SIM-HERA',systemId:1,camera:{kind:'proxy',componentId:1,deviceId:2}},capabilities:{capture:true,zoom:false,focus:false,gimbal:false},streams:[{id:'center-survey',type:'survey'}]},
  {id:'rear',label:'Sau / EO',route:{aircraftId:'SIM-HERA',systemId:1,camera:{kind:'component',componentId:101,deviceId:0},gimbal:{managerComponentId:1,deviceId:2}},capabilities:{capture:true,zoom:true,focus:false,gimbal:true,zoomRange:[1,4],pitchRange:[-90,20],yawRange:[-100,100]},streams:[{id:'rear-eo',type:'colour'}]}
];
