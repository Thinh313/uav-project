import fs from'node:fs';import path from'node:path';import{fileURLToPath,pathToFileURL}from'node:url';import{createHash}from'node:crypto';
const ROOT=fileURLToPath(new URL('../../',import.meta.url)),name='pilot/beta06g17/flight/qualified/mock.mjs',file=path.join(ROOT,name),hash=s=>createHash('sha256').update(s).digest('hex');let loaded=null,attestation=null;
/** Async scheduling seam for an in-process mock peer, never used for actual ArduPilot. */
export async function connectFairMock(capture,plan){
 if(!loaded){const original=fs.readFileSync(file,'utf8'),pins=JSON.parse(fs.readFileSync(path.join(ROOT,'evidence/beta06/generation17/flight-pins01.json')));if(hash(original)!==pins.files[name])throw Error('MOCK_PEER_PIN_DRIFT');let source=original;
  const a='if(this.writable)queueMicrotask(()=>{',b='if(this.writable)this.dispatch(()=>{';if(source.split(a).length!==2)throw Error('MOCK_PACKET_EXACT_COUNT');source=source.replace(a,b);
  const telemetryBefore='this.telemetry();if(f.command===176&&f.param2===3)this.fly();',telemetryAfter='if([176,400].includes(f.command))this.telemetry();if(f.command===176&&f.param2===3)this.fly();';if(source.split(telemetryBefore).length!==2)throw Error('MOCK_READONLY_TELEMETRY_ANCHOR');source=source.replace(telemetryBefore,telemetryAfter);
  const at=' packet(id,f){',methods=` dispatch(fn){this.delivery??=[];if(this.delivery.length>=256){this.deliveryError='MOCK_DELIVERY_QUOTA_NO_SILENT_DROP';this.destroy();return;}this.delivery.push(fn);this.peakDelivery=Math.max(this.peakDelivery??0,this.delivery.length);if(!this.draining){this.draining=true;setImmediate(()=>this.drainOne());}}
 drainOne(){if(!this.writable){this.draining=false;return;}const fn=this.delivery.shift();if(fn){fn();this.delivered=(this.delivered??0)+1;}if(this.delivery.length)setImmediate(()=>this.drainOne());else this.draining=false;}
`;
  if(source.split(at).length!==2)throw Error('MOCK_METHOD_ANCHOR');source=source.replace(at,methods+at);
  const before='await l.until(()=>l.freshness(0));return l;',after='try{await l.until(()=>l.freshness(0));return l;}catch(e){l.close63();throw e;}';if(source.split(before).length!==2)throw Error('MOCK_CONNECT_CLOSURE_ANCHOR');source=source.replace(before,after);
  let inverse=source.replace(after,before).replace(methods+at,at).replace(telemetryAfter,telemetryBefore).replace(b,a);if(inverse!==original)throw Error('MOCK_INVERSE_NOT_EXACT');
  source=source.replace("from'./link.mjs'",'from '+JSON.stringify(new URL('./link.mjs',import.meta.url).href));
  source=source.replace("WP_SPD:9}","WP_SPD:9,MIS_RESTART:2}");
  source=source.replace("if(f.command===176&&f.param2===3)this.fly();","if(f.command===176&&f.param2===3&&!this.flying){this.flying=true;this.fly();}if(f.command===176&&f.param2===6)this.returnHome();");
  source=source.replace("if(!this.writable)return;this.packet(42","while(this.writable&&this.mode===5)await new Promise(r=>setTimeout(r,20));if(!this.writable||this.mode===6)return;this.packet(42");
  source=source.replace(" destroy(){"," async returnHome(){await new Promise(r=>setTimeout(r,150));if(!this.writable)return;this.position={lat:this.home.lat,lon:this.home.lon,height:0};this.armed=false;this.telemetry();}\n destroy(){");
  source=source.replace(/from\s*(['"])(\.[^'"]+)\1/g,(_,q,p)=>'from '+JSON.stringify(new URL(p,pathToFileURL(file)).href));
  attestation={originalPath:name,originalSha256:hash(original),effectiveSha256:hash(source),inverseExact:false,legacySchedulingInverseExact:true,scope:'REVISED_MOCK_PEER_NOT_ARDUPILOT_OR_PHYSICS',telemetry:'PERIODIC_200MS_AND_FLIGHT_STATE_CHANGE_NO_EXTRA_BURST_ON_READONLY_COMMAND',maxPendingPackets:256,policy:'ALL_GENERATED_PACKETS_FIFO_OVERFLOW_CLOSES_PEER'};loaded=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
 }
 const link=await loaded.connectMock(capture,plan);link.mockDeliveryAttestation={...attestation};return link;
}
export function transportAttestation(){return attestation?{...attestation}:null;}
