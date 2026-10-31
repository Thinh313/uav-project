import {POLICY,exact} from './schema.mjs';
/** Mock NDJSON carrier ONLY. Not MAVLink/USB framing, no physical codec. */
export function encodeMockAction(action){const b=Buffer.from(JSON.stringify({format:'MOCK_NDJSON_HERAMCU45',version:1,action})+'\n');if(b.length>POLICY.envelopeBytes)throw Error('MOCK_ENVELOPE_BOUND');return b;}
export class MockFramer45 {
 constructor(){this.buffer=Buffer.alloc(0);this.invalid=false;this.closed=false;this.received=0;this.frames=0;}
 fail(reason){this.invalid=true;throw Error(reason);}
 push(bytes){if(this.invalid||this.closed)throw Error('MOCK_FRAMER_TERMINAL');if(!(bytes instanceof Uint8Array)||bytes.length>POLICY.framerBufferBytes)this.fail('CHUNK_BOUND');const combined=Buffer.concat([this.buffer,bytes]);if(combined.length>POLICY.framerBufferBytes)this.fail('FRAMER_BUFFER_BOUND');this.received+=bytes.length;const result=[];let from=0;
  for(let i=0;i<combined.length;i++)if(combined[i]===10){const line=combined.subarray(from,i);if(line.length+1>POLICY.envelopeBytes)this.fail('MOCK_ENVELOPE_BOUND');try{const text=new TextDecoder('utf-8',{fatal:true}).decode(line),e=JSON.parse(text);exact(e,['format','version','action']);if(e.format!=='MOCK_NDJSON_HERAMCU45'||e.version!==1)this.fail('MOCK_CARRIER_SCOPE');result.push(e.action);this.frames++;}catch(e){this.fail(e.message);}from=i+1;}
  this.buffer=combined.subarray(from);if(this.buffer.length>=POLICY.envelopeBytes)this.fail('INCOMPLETE_MOCK_ENVELOPE_BOUND');return result;
 }
 close(){if(this.invalid||this.closed)throw Error('MOCK_FRAMER_TERMINAL');if(this.buffer.length)this.fail('INCOMPLETE_MOCK_FRAME_RETAINED');this.closed=true;return {status:'CLOSED_MOCK',received:this.received,frames:this.frames};}
 snapshot(){return {invalid:this.invalid,closed:this.closed,received:this.received,frames:this.frames,pendingHex:this.buffer.toString('hex'),carrier:'MOCK_NDJSON_NOT_MAVLINK'};}
}
