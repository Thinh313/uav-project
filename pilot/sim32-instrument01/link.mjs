import {SitlLink} from '../../services/sitl.mjs';
import {readFileSync,appendFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {DEFAULT_SURVEY,surveyPackage,localFrame,DEMO_ORIGIN} from '../../app/core/survey.mjs';
import {execFileSync} from 'node:child_process';
import {encode} from '../../services/mavlink.mjs';
export function request({altitude=6,speed=1.5,size=12,name='SIM32 reference survey'}={}){
 if(!Number.isFinite(altitude)||altitude<5||altitude>20||!Number.isFinite(speed)||speed<.5||speed>3||!Number.isFinite(size)||size<11||size>30||typeof name!=='string'||name.length>80)throw Error('Simulator mission bounds');
 const f=localFrame(DEMO_ORIGIN);return surveyPackage({...DEFAULT_SURVEY,name,polygon:[{x:0,y:0},{x:size,y:0},{x:size,y:size},{x:0,y:size}].map(p=>f.reverse(p)),altitude,speed,sideOverlap:20,frontOverlap:20});
}
export class SimulationLink extends SitlLink{
 constructor(run){super({port:5784,timeoutMs:12000});if(!/^[a-zA-Z0-9]{1,32}$/.test(run))throw Error('Run ID');this.run=run;this.rawPath=`evidence/sim32-instrument01/runs/${run}/mavlink.jsonl`;this.rows=0;this.rawBytes=0;this.captureError=null;this.dead=false;this.physicsPath=`.local/sim32-instrument01/${run}/physics.json`;this.rawHash=createHash('sha256');}
 record(kind,data){if(this.captureError)throw Error(this.captureError);const row=JSON.stringify({index:++this.rows,hostMonotonicMs:performance.now(),hostMonotonicNs:process.hrtime.bigint().toString(),utc:new Date().toISOString(),run:this.run,kind,data})+'\n';this.rawBytes+=Buffer.byteLength(row);if(this.rawBytes>16*1024**2){this.captureError='MAVLink evidence bound reached';throw Error(this.captureError);}appendFileSync(this.rawPath,row,{flag:'a'});this.rawHash.update(row);}
 attest(){
  const base=`evidence/sim32-instrument01/runs/${this.run}/`,launch=JSON.parse(readFileSync(base+'launch.json','utf8'));
  const info=JSON.parse(execFileSync('docker',['inspect','aeris-sim32-instrument01'],{encoding:'utf8',timeout:5000}))[0];
  if(launch.run!==this.run||info.Id!==launch.containerId||!info.State.Running||info.Config.Labels['aeris.task']!=='sim32-instrument01'||info.Config.Labels['aeris.run']!==this.run||info.Image!==launch.imageId||info.HostConfig.NetworkMode!=='bridge')throw Error('Owned simulator attestation failed');
  for(const [p,hash] of Object.entries(launch.modulePins))if(createHash('sha256').update(readFileSync(p)).digest('hex')!==hash)throw Error('Simulator source changed during run');
  if(createHash('sha256').update(readFileSync(launch.binaryPath)).digest('hex')!==launch.binarySha256)throw Error('Autopilot binary changed');
  for(const [p,hash] of Object.entries(launch.referenceModulePins))if(createHash('sha256').update(readFileSync(p)).digest('hex')!==hash)throw Error('Read-only reference changed');
  for(const [p,hash] of Object.entries(launch.apSourcePins))if(createHash('sha256').update(readFileSync(p)).digest('hex')!==hash)throw Error('AP stage source changed');
  const port=info.NetworkSettings.Ports['5760/tcp'];if(port?.length!==1||port[0].HostIp!=='127.0.0.1'||port[0].HostPort!=='5784')throw Error('Endpoint ownership mismatch');
  const identity=JSON.parse(readFileSync(base+'backend-identity.json','utf8'));if(identity.pid!==launch.backendPid||identity.run!==this.run)throw Error('Backend identity mismatch');
  const cmd=execFileSync('ps',['-p',String(identity.pid),'-o','command='],{encoding:'utf8',timeout:3000});if(!cmd.includes('/pilot/sim32-instrument01/backend.py '+this.run+' '))throw Error('Backend process mismatch');
  this.record('OWNED_ENDPOINT_ATTESTED',{containerId:info.Id,backendPid:identity.pid,binarySha256:launch.binarySha256});
 }
 async connect(){this.attest();const p=super.connect();this.socket.on('data',bytes=>{try{this.record('AP_RX_CHUNK',{rawHex:bytes.toString('hex')});}catch(e){this.captureError=e.message;this.socket?.destroy();}});return p;}
 send(id,fields={}){
  if(this.dead)throw Error('Expired simulator adapter');if(![0,20,76,44,73,43,51,47].includes(id))throw Error('MAVLink send outside simulator allowlist');if(id!==0&&(fields.target_system!==42||fields.target_component!==1))throw Error('Foreign aircraft target');if(id===76&&![512,511,176,400].includes(fields.command))throw Error('Unsupported control command');this.record('GCS_TX_REQUEST',{id,fields,rawHex:encode(id,fields,{seq:this.sequence}).toString('hex')});return super.send(id,fields);
 }
 receive(m){try{if(m.system===42&&m.component===1)this.record('AP_RX_FRAME',m);super.receive(m);}catch(e){this.captureError=e.message;this.socket?.destroy();}}
 physics(){const v=JSON.parse(readFileSync(this.physicsPath,'utf8'));if(v.run!==this.run||Date.now()-Date.parse(v.receivedAtUtc)>1500||Date.now()<Date.parse(v.receivedAtUtc))throw Error('Physics stale or foreign');return v;}
 async readSimulatorConfiguration(){
  const expected={FS_GCS_ENABLE:1,FS_GCS_TIMEOUT:5,FS_OPTIONS:16,RTL_ALT_M:6,RTL_SPEED_MS:3,WP_SPD:2,WP_ACC:1,LAND_SPD_MS:.6,SIM_RATE_HZ:1200,SIM_SPEEDUP:Number(process.env.SIM32_SPEEDUP??1)};
  const promise=this.beginPending('parameters',{names:Object.keys(expected),values:{}});for(const name of Object.keys(expected))this.send(20,this.target({param_id:name,param_index:-1}));
  const values=await promise;const pass=Object.entries(expected).every(([k,v])=>Math.abs(values[k].value-v)<1e-5);this.simConfiguration={expected,values,pass,at:Date.now()};this.record('SIMULATOR_PROFILE_READ_ONLY',this.simConfiguration);if(!pass)throw Error('Simulator parameter mismatch');return this.simConfiguration;
 }
 async command(name){this.physics();return super.command(name);}
 async upload(pkg){this.physics();return super.upload(pkg);}
 review(){return {format:'aeris-sim32-review',version:1,run:this.run,at:new Date().toISOString(),simulation:true,physicsCalibration:'PROVISIONAL_NOT_HERA',media:[],physicalMediaVerified:false,flightExecutionProven:false,simulationExecution:this.execution.state,recordComplete:!this.captureError,mavlinkRows:this.rows,mavlinkBytes:this.rawBytes,source:this.journal()};}
}
