/** Read-only evidence fence before the single host TCP connection. No console probe. */
import fs from'node:fs';import{createHash}from'node:crypto';
const LIMIT=2*2**20,markers={waiting:'Waiting for connection',serial0:'SERIAL0 on TCP port 5760'},hash=b=>createHash('sha256').update(b).digest('hex');
export function assertSerialReadinessProof(q,launch,streams){
 const p=q?.proof;
 if(Object.keys(p?.streams??{}).sort().join()!=='stderr,stdout'||Object.keys(streams??{}).sort().join()!=='stderr,stdout'||Object.keys(p?.markers??{}).sort().join()!=='serial0,waiting')throw Error('EXACT_TWO_ORIGINAL_ATTACHED_STREAMS_REQUIRED');
 if(!/^[a-f0-9]{64}$/.test(launch?.containerId??'')||q?.containerId!==launch?.containerId||q?.serial0ListeningObserved!==true||q?.noTCPProbeOrRetry!==true||q?.basis!=='BOUNDED_SAME_ATTEMPT_DUAL_STREAM_ATTACHED_CONSOLE_BEFORE_ONE_HOST_CONNECTION'||p?.attempt!=='attach:'+launch.containerId||p?.noCrossStreamConcatenation!==true||p?.serialConsoleOnly!==true||p?.telemetryFirmwareExecutionFlightProven!==false||p?.perStreamTailBoundBytes!==65536||p?.perStreamCaptureBoundBytes!==LIMIT)throw Error('SAME_ATTEMPT_SERIAL_CONSOLE_PROOF_REQUIRED');
 for(const stream of ['stdout','stderr']){
  const s=p.streams?.[stream],b=streams?.[stream];if(!s||!Buffer.isBuffer(b)||b.length>LIMIT||!Number.isSafeInteger(s.retainedPrefixBytes)||s.retainedPrefixBytes<0||s.retainedPrefixBytes>b.length||s.path!=='diagnostics/attach-'+stream+'.bin'||s.captureFsyncedBeforeRead!==true||hash(b.subarray(0,s.retainedPrefixBytes))!==s.retainedPrefixSha256)throw Error('SERIAL_STREAM_PREFIX_COUNT_SHA_REQUIRED');
 }
 for(const[k,text]of Object.entries(markers)){const m=p.markers?.[k],s=p.streams?.[m?.stream],b=streams?.[m?.stream];if(!m||!['stdout','stderr'].includes(m.stream)||!s||m.marker!==text||!Number.isSafeInteger(m.offsetBytes)||m.offsetBytes<0||m.offsetBytes+Buffer.byteLength(text)>s.retainedPrefixBytes||b.subarray(m.offsetBytes,m.offsetBytes+Buffer.byteLength(text)).toString()!==text)throw Error('ORIGINAL_STREAM_MARKER_PROVENANCE_REQUIRED');}
 return{serialConsoleOnly:true,telemetryFirmwareExecutionFlightProven:false};
}
export function requireSerialReadiness(out,launch){
 const streams={};for(const stream of ['stdout','stderr']){const path=out+'/diagnostics/attach-'+stream+'.bin',s=fs.lstatSync(path);if(!s.isFile()||s.isSymbolicLink()||s.size>LIMIT)throw Error('BOUNDED_REGULAR_ATTACHED_STREAM_REQUIRED');streams[stream]=fs.readFileSync(path);}
 const readyPath=out+'/guest-ready.json',r=fs.lstatSync(readyPath);if(!r.isFile()||r.isSymbolicLink()||r.size>16384)throw Error('BOUNDED_REGULAR_SERIAL_PROOF_REQUIRED');return assertSerialReadinessProof(JSON.parse(fs.readFileSync(readyPath)),launch,streams);
}
