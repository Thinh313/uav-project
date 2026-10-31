import {FullFramer,hex} from '../apstream40/wire.mjs';
import {assertManifest} from './contract.mjs';
export class Observations42 {
 constructor(m){assertManifest(m);this.context=Object.freeze(structuredClone(m));this.framer=new FullFramer();this.started=false;this.preamble=[];this.frames=[];this.latest={};this.parameters={};this.dead=false;this.last=-1;this.boot=new Map();this.seq=null;}
 loss(r){this.dead=true;this.reason=r;this.framer.close(r);}
 receive(bytes,at,t=at){try{return this.consume(bytes,at,t);}catch(e){this.loss(e.message);throw e;}}
 consume(bytes,at,t=at){
  if(this.dead||!Number.isSafeInteger(at)||at<0||at>t||t-at>1500||at<this.last)throw Error('LOST_OR_STALE_RECEIPT');this.last=at;
  if(!this.started){const k=bytes.findIndex(x=>x===253||x===254),p=k<0?bytes:bytes.slice(0,k);this.preamble.push(...p);if(this.preamble.length>1024||p.some(b=>![9,10,13].includes(b)&&(b<32||b>126)))throw Error('PREAMBLE_BOUND');if(k<0)return[];if(this.preamble.length&&!new TextDecoder().decode(Uint8Array.from(this.preamble)).includes('Init ArduCopter V4.7.1 (dbe79216)'))throw Error('BOOT_BANNER');this.started=true;bytes=bytes.slice(k);}
  const out=this.framer.push(bytes,at,t);
  for(const f of out){let label='ACCEPTED';if(f.system!==42||f.component!==1)label='FOREIGN';else if(!f.known||!f.crcVerified||f.signed)throw Error('UNVERIFIED_TARGET_FRAME');
   if(label==='ACCEPTED'&&f.id===148&&(f.fields.flight_sw_version!==67568127||String.fromCharCode(...f.fields.flight_custom_version)!=='dbe79216'))throw Error('FIRMWARE_CHANGED_EVEN_DUPLICATE');
   if(label==='ACCEPTED'&&this.seq!==null){const d=(f.seq-this.seq+256)%256;if(d===128)throw Error('SEQUENCE_AMBIGUOUS');if(d===0)label='DUPLICATE';else if(d>128)label='REORDERED';}
   this.frames.push({...f,label,at});if(this.frames.length>40000)throw Error('FRAME_CAPTURE_BOUND');if(label!=='ACCEPTED')continue;
   this.seq=f.seq;
   if('time_boot_ms'in f.fields){const v=f.fields.time_boot_ms,old=this.boot.get(f.id);if(old!==undefined&&(v-old+2**32)%2**32>=2**31)throw Error('BOOT_CLOCK_REGRESSION');this.boot.set(f.id,v);}
   if(f.id===0&&(f.fields.type!==2||f.fields.autopilot!==3))throw Error('WRONG_VEHICLE');
   if(f.id===148&&(f.fields.flight_sw_version!==67568127||String.fromCharCode(...f.fields.flight_custom_version)!=='dbe79216'||!(BigInt(f.fields.capabilities)&2n)||BigInt(f.fields.capabilities)&16n))throw Error('FIRMWARE_ENCODING_MISMATCH');
   this.latest[f.id]={...f,at};if(f.id===22)this.parameters[f.fields.param_id]={value:f.fields.param_value,type:f.fields.param_type,at,rawHex:f.rawHex,count:f.fields.param_count,index:f.fields.param_index};
  }return out;
 }
 fresh(t){const h=this.latest[0],v=this.latest[148];return !this.dead&&!!h&&!!v&&t>=h.at&&t-h.at<=1500;}
 snapshot(){return {context:structuredClone(this.context),dead:this.dead,reason:this.reason??null,preambleHex:hex(Uint8Array.from(this.preamble)),frames:this.frames.length,latest:structuredClone(this.latest),parameters:structuredClone(this.parameters),physicalAuthority:false};}
}
export function distance(lat,lon,h){const r=Math.PI/180,a=(lat/1e7-h.latitude/1e7)*r,b=(lon/1e7-h.longitude/1e7)*r;return Math.hypot(a,b*Math.cos(h.latitude/1e7*r))*6371000;}
