import{FullFramer,unhex}from'../apstream40/wire.mjs';import{parameterFrame,decodeParameter}from'../firmware38/wire.mjs';import{SCHEMA,VERSION,BUILD}from'../preflight43/profile.mjs';
export class FlightGuard{
 constructor(link){this.link=link;this.framer=new FullFramer();this.started=false;this.prefix=[];}
 receive(bytes,at){let b=new Uint8Array(bytes);if(!this.started){const k=b.findIndex(x=>x===253||x===254),p=k<0?b:b.slice(0,k);this.prefix.push(...p);if(this.prefix.length>1024||p.some(x=>![9,10,13].includes(x)&&(x<32||x>126)))throw Error('FLIGHT_PREFIX_BOUND');if(k<0)return;if(this.prefix.length&&!new TextDecoder().decode(Uint8Array.from(this.prefix)).includes('Init ArduCopter V4.7.1 (dbe79216)'))throw Error('FLIGHT_WRONG_BANNER');this.started=true;b=b.slice(k)}
  for(const f of this.framer.push(b,at,at)){if(f.system!==42||f.component!==1)continue;if(!f.crcVerified||f.signed||!f.known)throw Error('FLIGHT_UNVERIFIED_SELECTED_FRAME');if(f.id===0&&(f.fields.autopilot!==3||f.fields.type!==2))throw Error('FLIGHT_WRONG_AUTOPILOT');if(f.id===148&&(f.fields.flight_sw_version!==VERSION||String.fromCharCode(...f.fields.flight_custom_version)!==BUILD))throw Error('FLIGHT_FIRMWARE_CHANGED');const l=this.link;if(!l.inspectionActive&&f.id===22&&SCHEMA[f.fields.param_id]){const n=f.fields.param_id,p=parameterFrame(unhex(f.rawHex)),v=decodeParameter(p.valueBytes,p.fields.param_type,'C_CAST');if(p.fields.param_type!==SCHEMA[n][0]||v!==l.inspectionGate.assessment.parameters[n])throw Error('FLIGHT_TYPED_PARAMETER_CHANGED:'+n)}
   if(f.id===242&&l.boundHome){const h=l.boundHome;if(f.fields.latitude!==Math.round(h.lat*1e7)||f.fields.longitude!==Math.round(h.lon*1e7)||f.fields.altitude!==Math.round(h.amsl*1000))throw Error('HOME_CHANGED_AFTER_ARM_REVIEW');}
  }
 }
}
