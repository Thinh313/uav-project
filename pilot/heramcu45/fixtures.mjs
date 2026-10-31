import {clone,AXES,PORTS,POLICY,MOCK_RF_ROUTES} from './schema.mjs';
import {HeraMCU45} from './model.mjs';
export function mockConfig(){return {format:'MOCK_NORMALIZED_MCU_CONFIG45',revision:'mock45-config1',ports:PORTS.map(port=>({port,assign:[6,7,10,11,...Array(12).fill(0)],min:Array(16).fill(1000),max:Array(16).fill(2000),trim:Array(16).fill(1500),invertMask:0,protocol:'STANDARD_SBUS',frequencyHz:50})),axes:AXES.map(axis=>({axis,min:0,max:4095,trim:2047,deadzone:40,inverted:false})),buttonMask:32767,mappingCoefficients:{x:Array(16).fill(0),y:Array(16).fill(0),index:Array.from({length:16},(_,i)=>i)},multiModeButtons:Array.from({length:6},(_,i)=>({button:'MMB'+(i+1),mode:'BISTATE',trigger:'PRESS',values:[0,2047,4095],step:1,rollover:false})),power:{lowVoltageMv:11000,highCurrentMa:10000,buzzer:true}};}
export function context45(suffix='a'){return {origin:POLICY.origin,session:'mock-session45-'+suffix,boot:'mock-boot45-'+suffix,target:'mock:mcu45-'+suffix};}
export const IDENTITY={uuid:'1234567890abcdef1234567890abcdef',dev:'deadbeef',ver:'00000003'};
export class MockPeer45 {
 constructor(configuration=mockConfig()){this.stored=clone(configuration);this.applied=clone(configuration);this.sequence=0;}
 packet(ctx,kind,data,transaction=null){return {...clone(ctx),sequence:this.sequence++,kind,transaction,data:clone(data)};}
 info(ctx){return this.packet(ctx,'INFO',IDENTITY);}
 read(ctx,transaction){return this.packet(ctx,'CONFIG',this.applied,transaction);}
 apply(c){this.applied=clone(c);}
 save(){this.stored=clone(this.applied);}
 reboot(){this.applied=clone(this.stored);this.sequence=0;}
}
export function driver(suffix='a',peer=new MockPeer45()){
 const ctx=context45(suffix),model=new HeraMCU45(ctx);let t=0;
 const doAction=(kind,data={},at)=>{t=at??t+1;return model.process({kind,t,data});};
 const rx=(kind,data,transaction=null,at)=>doAction('RX',peer.packet(ctx,kind,data,transaction),at);
 const bootstrap=()=>{doAction('CONNECT');rx('INFO',IDENTITY);const q=doAction('READ_CONFIG').body.result;rx('CONFIG',peer.applied,q.transaction);};
 const sources=(port='OUTPUT_PORT_1')=>{rx('POWER',{batteryMv:[12000,12000],adapterPlugged:false,warnings:[]});rx('RF',{port:MOCK_RF_ROUTES[port],status:'CONNECTED',rssiPercent:75});rx('CHANNELS',{port,bootMs:t+1,channels:Array(16).fill(1500)});};
 const ack=(operation,transaction,result='ACCEPTED',step=null,progress=null)=>rx('ACK',{operation,result,step,progress},transaction);
 return {ctx,model,peer,doAction,rx,bootstrap,sources,ack,get t(){return t;}};
}
