import {randomUUID} from 'node:crypto';
import {HeraMCU45,replay} from '../heramcu45/model.mjs';
import {MockPeer45,mockConfig,IDENTITY} from '../heramcu45/fixtures.mjs';
import {clone,config,digest,stable,CONTRACT,CONTRACT_SHA,GROUPS,PORTS,INPUT_AXIS,MOCK_RF_ROUTES} from '../heramcu45/schema.mjs';
const TERMINAL=['LINK_LOST','INVALIDATED','CONFIG_UNCERTAIN','EVIDENCE_LIMIT'];
export class Workspace46{
 constructor(){this.revision=0;this.clock=0;this.peer=new MockPeer45();this.records=[];this.raw={6:2047,7:2047,10:2047,11:2047};this.selectedPort=PORTS[0];this.preview=null;this.draft=null;this.review=null;this.newModel();}
 newModel(){const id=randomUUID();this.model=new HeraMCU45({origin:CONTRACT.mockPolicy.origin,session:id,boot:randomUUID(),target:'mock:herahub46'});this.clock=0;this.preview=null;this.draft=null;this.raw={6:2047,7:2047,10:2047,11:2047};}
 act(kind,data={}){const e=this.model.process({kind,t:++this.clock*100,data});if(e.body.error)throw Error(e.body.error);return e.body.result;}
 rx(kind,data,transaction=null,override={}){return this.act('RX',{...this.peer.packet(this.model.context,kind,data,transaction),...override});}
 require(state){if(this.model.state!==state)throw Error('STATE_REQUIRED:'+state);}
 ack(operation,result='ACCEPTED',step=null,progress=null,override={}){const p=this.model.pending;if(!p||p.operation!==operation)throw Error('NO_MATCHING_PENDING');return this.rx('ACK',{operation,result,step,progress},p.id,override);}
 samples(){this.require('MOCK_READY');this.rx('POWER',{batteryMv:[12100,12050],adapterPlugged:false,warnings:[]});for(const port of PORTS){this.rx('RF',{port:MOCK_RF_ROUTES[port],status:'CONNECTED',rssiPercent:76});this.rx('CHANNELS',{port,bootMs:this.clock*100+100,channels:Array(16).fill(1500)});}this.preview=null;}
 archive(){const record=this.model.export();replay(record);if(this.records.length>=4)throw Error('HISTORY_LIMIT_EXPORT_RELOAD_NEW_WORKSPACE');this.records.push(record);}
 run(kind,data={}){
  if(kind==='connect'){this.require('DISCONNECTED');this.act('CONNECT');}
  else if(kind==='identity'){this.require('WAIT_INFO');this.rx('INFO',IDENTITY);}
  else if(kind==='read'){if(!['DISCOVERED','READBACK_REQUIRED'].includes(this.model.state))throw Error('NO_CONFIG_READ_AVAILABLE');const q=this.act('READ_CONFIG');this.rx('CONFIG',this.peer.applied,q.transaction);this.draft=null;this.preview=null;}
  else if(kind==='samples')this.samples();
  else if(kind==='preview'){this.require('MOCK_READY');const raw=clone(data.raw);this.raw=raw;this.selectedPort=data.port;this.preview=this.act('PREVIEW',{rawInputs:raw,port:data.port});}
  else if(kind==='startCalibration'){this.preview=null;this.act('BEGIN_CALIBRATION');}
  else if(kind==='calibrationAck'){this.require('CALIBRATING');this.ack('CALIBRATE','ACCEPTED',this.model.step,100);}
  else if(kind==='calibrationResult'){this.require('CALIBRATING');const step=this.model.step;if(this.model.progress!==100)throw Error('ACK100_BEFORE_SYNTHETIC_RESULT');this.rx('CALIBRATION_RESULT',{step,axes:GROUPS[step][1].map(axis=>({axis,samples:[data.min,data.trim,data.max]})),pressedMask:step===8?data.pressedMask:0},this.model.pending.id);if(this.model.state==='SAVE_REQUIRED')this.peer.apply(this.model.candidate);}
  else if(kind==='cancelCalibration'){this.preview=null;this.act('CANCEL_CALIBRATION');}
  else if(kind==='stage'){this.require('MOCK_READY');this.draft=null;const c=config(data);this.draft=c;}
  else if(kind==='apply'){this.require('MOCK_READY');if(!this.draft)throw Error('VALIDATE_MAPPING_FIRST');this.preview=null;this.act('APPLY_MAPPING',this.draft);this.peer.apply(this.draft);}
  else if(kind==='applyAck'){this.require('APPLY_PENDING');this.ack('APPLY_MAPPING');}
  else if(kind==='save'){this.require('SAVE_REQUIRED');this.preview=null;this.act('SAVE');this.peer.save();}
  else if(kind==='saveAck'){this.require('SAVE_PENDING');this.ack('SAVE');}
  else if(kind==='disconnect'){this.preview=null;this.act('DISCONNECT');}
  else if(kind==='reboot'){this.preview=null;this.act('REBOOT');this.peer.reboot();}
  else if(kind==='newSession'){if(!TERMINAL.includes(this.model.state))throw Error('DISCONNECT_OR_REBOOT_BEFORE_NEW_SESSION');this.archive();this.newModel();}
  else if(kind==='stale'){this.clock+=26;this.preview=null;this.act('TICK');}
  else if(kind==='timeout'){this.clock+=Math.ceil((this.model.state==='CALIBRATING'?61000:4000)/100);this.preview=null;this.act('TICK');}
  else if(kind==='jam'){this.require('MOCK_READY');this.preview=null;this.rx('RF',{port:MOCK_RF_ROUTES[data.port],status:'JAMMED',rssiPercent:0});}
  else if(kind==='foreignAck'){if(!this.model.pending)throw Error('NO_PENDING_ACK');const p=this.model.pending;this.rx('ACK',{operation:p.operation,result:'ACCEPTED',step:this.model.state==='CALIBRATING'?this.model.step:null,progress:this.model.state==='CALIBRATING'?100:null},p.id,{target:'mock:foreign'});}
  else if(kind==='mismatch'){this.require('READBACK_REQUIRED');const q=this.act('READ_CONFIG'),c=clone(this.peer.applied);c.revision+='-mismatch';this.preview=null;this.rx('CONFIG',c,q.transaction);}
  else if(kind==='import'){this.review=null;const record=data.record,result=replay(record,data.expectedSha||null);this.review={result,seal:clone(record.seal),context:clone(record.context),suppliedExpected:!!data.expectedSha};}
  else throw Error('UI_ACTION_NOT_ALLOWED');
  return this.view();
 }
 dispatch(kind,data,revision){if(!Number.isSafeInteger(revision)||revision!==this.revision)throw Error('STALE_UI_REVISION_NO_RETRY');this.revision++;try{return this.run(kind,data);}catch(e){this.preview=null;throw e;}}
 view(){const summary=this.model.summary(),t=this.model.clock,source=[...this.model.sources].map(([name,s])=>({name,ageMs:t-s.at,data:clone(s.data)}));let differences=[];
  if(this.draft&&this.model.configuration)for(const p of PORTS){const a=this.model.configuration.ports.find(x=>x.port===p),b=this.draft.ports.find(x=>x.port===p);for(const key of ['assign','min','max','trim','invertMask','protocol','frequencyHz'])if(stable(a[key])!==stable(b[key]))differences.push(p+' / '+key);}if(this.draft&&this.model.configuration&&stable(this.draft.axes)!==stable(this.model.configuration.axes))differences.push('Axis / deadzone,invert');if(this.draft&&this.model.configuration&&stable(this.draft.multiModeButtons)!==stable(this.model.configuration.multiModeButtons))differences.push('MMB / mode,trigger,values,step');
  return {format:'aeris-heraui46-view',revision:this.revision,clockMs:Math.max(0,t),clockMode:'VIRTUAL_USER_STEPPED_NOT_REALTIME',summary,context:clone(this.model.context),source,raw:clone(this.raw),preview:clone(this.preview),configuration:clone(this.model.configuration),draft:clone(this.draft),candidate:clone(this.model.candidate),calibrationResults:clone(this.model.calibrationResults),groups:GROUPS.map(([name,axes])=>({name,axes})),differences,storedMockSha256:digest(this.peer.stored),appliedMockSha256:digest(this.peer.applied),history:this.records.map(r=>({state:r.summary.state,events:r.events.length,seal:r.seal,session:r.context.session})),events:this.model.events.slice(-8).map(e=>({n:e.body.n,kind:e.body.input.kind,error:e.body.error,state:e.body.snapshot.state})),record:this.model.export(),review:clone(this.review),unknowns:clone(CONTRACT.unknowns),contractSha256:CONTRACT_SHA,contractRevision:CONTRACT.revision,operational:false};
 }
}
