import{CodecGate09}from'./codec-gate09.mjs';
/** Root writer adaptation of frozen G5 relay; protocol algorithms retained, direct file writes removed. */
import{normalizeClockDiagnostics}from'../../../pilot/beta06g4/clock-diagnostic-adapter.mjs';
import{decodeWindowGroup}from'./video-windows.mjs';
import{jpegSize}from'./capture-schema.mjs';
import{cameraBasisNed}from'../scene/observer.mjs';
import{BrokerCapture}from'./broker-capture.mjs';

import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomBytes, randomUUID, createHash, timingSafeEqual } from 'node:crypto';
import { Relay01, encodePacket, decodePacket, exact, LIMITS } from '../../../media/big02/relay-core.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '../../..');
const PROFILE_PATH = path.join(REPO, 'media/big02/profile01.json');
export const MEDIA_READ_INPUTS=Object.freeze(['media/big02/profile01.json','media/big02/relay-core.mjs','planning/betasim-integrated01/product/viewer-codec09.mjs','planning/betasim-integrated01/product/codec-capabilities09.mjs',...['publisher.html','publisher.mjs','source-cadence.mjs','client.mjs','network-bootstrap.mjs','clock-lifecycle.mjs','network-key-diagnostic.mjs'].map(n=>'pilot/clockvideo05/media/'+n)]);
export const MEDIA_LIMITS = Object.freeze({body: LIMITS.chunk + LIMITS.headers + 4, runBody: 1024 * 2 ** 20, evidence: 15 * 2 ** 20, frames: 180, videoProofCommits:15000, reports: 8, controls: 96, rate: 150, bodyDeadlineMs: 1500, requestDeadlineMs: 2500, frameFreshMs: 1000, lifetimeMs: 2700000});
const nowMs = () => Number(process.hrtime.bigint()) / 1e6;
const hash = value => createHash('sha256').update(value).digest('hex');
const canonical = bytes => { const text = new TextDecoder('utf-8', {fatal:true}).decode(bytes); const q = JSON.parse(text); if (JSON.stringify(q) !== text) throw Error('CANONICAL_JSON_REQUIRED'); return q; };
const deepFreeze = value => { if (value && typeof value === 'object') { for (const child of Object.values(value)) deepFreeze(child); Object.freeze(value); } return value; };
const freezeCopy = value => deepFreeze(structuredClone(value));
const tokenEqual = (actual, expected) => typeof actual === 'string' && actual.length === expected.length && timingSafeEqual(Buffer.from(actual), Buffer.from(expected));
function clock(q) {
  exact(q, ['lowerMs','upperMs','sampledBrowserMs','validUntilBrowserMs','roundtripMs']);
  if (!Object.values(q).every(Number.isFinite) || q.upperMs < q.lowerMs || q.upperMs - q.lowerMs > 20 || q.roundtripMs < 0 || q.roundtripMs > 20 || q.validUntilBrowserMs - q.sampledBrowserMs !== 60000) throw Error('CLOCK_BOUND');
  return {...q};
}
function hostBounds(browserMs, calibration) {
  if (!Number.isFinite(browserMs) || !calibration || browserMs < calibration.sampledBrowserMs - 1000 || browserMs > calibration.validUntilBrowserMs) return null;
  return {lowerMs: browserMs + calibration.lowerMs, upperMs: browserMs + calibration.upperMs};
}

/** Independent localhost media service. No flight or payload command API. */
export async function createMediaServer({port=8895,writer,verifyGuard=()=>{},allowedOrigin='http://127.0.0.1:8896',schedule=true,staticAsset=null,frameProofValidator=null,engineeringSelection=null,targetNativeSourceSHA256=null,targetIdentityProvider=null}={}) {
  if(port!==8895||!writer||typeof frameProofValidator!=='function')throw Error('ROOT_MEDIA_WRITER_FIXED_ORIGIN_AND_ORIGINAL_FRAME_VALIDATOR_REQUIRED');verifyGuard();
  const mediaEpoch=randomUUID(),capture=new BrokerCapture(writer,'media-clock-'+mediaEpoch,{storedByteLimit:768*1024-36*1024}),proofCapture=new BrokerCapture(writer,'video-'+mediaEpoch+'-proof',{lane:'media',storedByteLimit:5.5*2**20-36*1024}),savedReports=new Map();let clockEvents=0;
  const clockJournal={append(kind,data){if(++clockEvents>8192)throw Error('MEDIA_CLOCK_EVENT_BOUND');return capture.append(kind,data);},snapshot(){return{fatal:capture.failed,events:clockEvents,head:capture.head,bytes:capture.bytes};},close:()=>capture.close()};
  const profiles = JSON.parse(await fs.readFile(PROFILE_PATH, 'utf8'));
  let relay = new Relay01(profiles.profiles.map(p => p.id));
  const sourceRuns=new Set(),sourceBoots=new Set();let sourceReplacements=0;
  const serverBoot = randomUUID(), viewerId = randomUUID();
  const bearer = {publisher:randomBytes(32).toString('hex'), viewer:randomBytes(32).toString('hex')};
  const codecGate=new CodecGate09({selection:engineeringSelection,profiles:profiles.profiles,targetSourceSHA256:targetNativeSourceSHA256,targetIdentityProvider,serverBoot,viewerId,clock:nowMs,record:(k,d)=>clockJournal.append(k,d),commit:()=>capture.flush()});const reasonCounts={},stageTotals={proofCommit:{count:0,totalMs:0,maximumMs:0,buckets:Array(8).fill(0)}};let diagnosticRows=0,diagnosticWriteFailure=null;function diagnosticAggregate(kind,key){key=String(key).slice(0,96);if(!Object.hasOwn(reasonCounts,key)&&Object.keys(reasonCounts).length>=32)key='OTHER_REASON_CLASS_BOUNDED';reasonCounts[key]=(reasonCounts[key]??0)+1;const n=reasonCounts[key];if(diagnosticRows<64&&(n&(n-1))===0){diagnosticRows++;try{clockJournal.append(kind,{reason:key,count:n,total:structuredClone(reasonCounts),scope:'ORIGINAL_SERVER_AGGREGATE_NO_GPU_CPU_CAUSE'});}catch(e){diagnosticWriteFailure=String(e.message).slice(0,180);}}}
  const frameProofs=new Map();const frames = new Map(), decoded = new Map(), configuredSessions = new Map(), pending = new Set(), requestTimes = [];
  let origin = `http://127.0.0.1:${port}`, sourceClock = null, bytesRead = 0, bytesSaved = 0, reports = 0, controls = 0, closed = false, writeChain = Promise.resolve(), guard, lifetime;
  let publisherCounters=null,exposure=null,exposureCount=0,sourceJPEGBytes=0,reportedSamples=0,videoProofCommits=0,videoTaskStopReason=null;
  let metrics = {requests:0, rejected:0, polls:0, clockRequests:0, decodedRegistrations:0, diskStop:false};
  const write = (name, value) => {
    const bytes = value instanceof Uint8Array ? Buffer.from(value) : Buffer.from(typeof value === 'string' ? value : JSON.stringify(value, null, 2) + '\n');
    if(/^report-0[1-8]\.json$/.test(name)&&bytes.length>512*1024)throw Error('MEDIA_PHYSICAL_REPORT512K');
    const operation = writeChain.then(async () => { if(bytesSaved+bytes.length>MEDIA_LIMITS.evidence)throw Error('MEDIA_EVIDENCE_QUOTA');verifyGuard();let originalRef;for(let at=0;at<bytes.length;at+=65536)originalRef=await writer.write('media/video-'+mediaEpoch+'-'+name,bytes.subarray(at,at+65536),{append:at>0});bytesSaved+=bytes.length;const receipt={file:name,sha256:hash(bytes),bytes:bytes.length,originalRef,durable:true};if(/^report-0[1-8]\.json$/.test(name))savedReports.set(name,{bytes:Buffer.from(bytes),originalRef,durable:true});return receipt; });
    writeChain = operation.catch(() => {}); return operation;
  };
  const diagnostic={observe(){},arm(){throw Error('OPTIONAL_KEY_DIAGNOSTIC_NOT_ENABLED');},status(){throw Error('OPTIONAL_KEY_DIAGNOSTIC_NOT_ENABLED');},bytes(){throw Error('OPTIONAL_KEY_DIAGNOSTIC_NOT_ENABLED');},save(){throw Error('OPTIONAL_KEY_DIAGNOSTIC_NOT_ENABLED');}};
  await write('launch.json', {format:'aeris-field01-media-launch',serverBoot,pid:process.pid,profileSha256:hash(await fs.readFile(PROFILE_PATH)),at:new Date().toISOString(),source:'SYNTHETIC',transport:'REAL_LOCALHOST_HTTP_TCP',limits:MEDIA_LIMITS,physicalLatency:'NOT_MEASURED',actualImages:0});
  function verifyFrame(metadata){if(!frameProofValidator)throw Error('ROOT_FRAME_PROOF_VALIDATOR_REQUIRED');const i=metadata?.intrinsics;if(!i||i.width!==1280||i.height!==720||!Number.isFinite(i.sensorHeightMm)||i.sensorHeightMm<=0||i.sensorHeightMm>100||!Number.isFinite(i.focalLengthMm)||i.focalLengthMm<4||i.focalLengthMm>500)throw Error('PAYLOAD_FRAME_INTRINSICS');const fov=2*Math.atan(i.sensorHeightMm/(2*i.focalLengthMm))*180/Math.PI;if(Math.abs(i.verticalFovDeg-fov)>1e-9)throw Error('PAYLOAD_FRAME_FOV');const basis=cameraBasisNed(metadata.aircraftQuaternionWxyz,metadata.gimbal);if(!Array.isArray(metadata.cameraPositionNedM)||!Array.isArray(metadata.aircraftPositionNedM)||!metadata.cameraPositionNedM.every((v,n)=>Number.isFinite(v)&&Math.abs(v-metadata.aircraftPositionNedM[n]-basis.mountNedM[n])<1e-9))throw Error('PAYLOAD_FRAME_ANALYTICAL_MOUNT');if(metadata.feed!==(relay.session?.feed==='thermal'?'thermal-look':'rgb'))throw Error('PAYLOAD_FRAME_FEED_NOT_RELABELLED');return frameProofValidator({...metadata,positionNedM:metadata.aircraftPositionNedM,quaternionWxyz:metadata.aircraftQuaternionWxyz});}
  function requiredVideoReadiness(){const view=codecGate.readiness();return closed||capture.failed||proofCapture.failed||diagnosticWriteFailure?{...view,ready:false,reason:'MEDIA_CLOSED_OR_EVIDENCE_FAILED'}:view;}
  function pendingExposure(){return exposure?{requestId:exposure.requestId,payloadId:exposure.payloadId,feed:exposure.feed==='thermal'?'thermal-look':'rgb'}:null;}
  function requestExposure({payloadId,feed,guard=()=>{}}){if(closed||exposure||exposureCount>=32||!relay.session||relay.session.feed!==feed)throw Error('SOURCE_EXPOSURE_ONE_PENDING_OR_SCOPE');guard();const requestId=randomUUID();exposureCount++;return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{if(exposure?.requestId===requestId){exposure=null;reject(Error('SOURCE_EXPOSURE_500MS_UNKNOWN_NO_RETRY'));}},500);exposure={requestId,payloadId,feed,guard,timer,resolve,reject,issuedHostMs:nowMs()};});}
  const wake = () => { for (const fn of pending) fn(); };
  const state = () => ({serverBoot,origin,engineeringSelection:structuredClone(engineeringSelection),videoReadiness:requiredVideoReadiness(),codecDiagnostics:{reasonCounts:{...reasonCounts},stageTotals:structuredClone(stageTotals),originalAggregateRows:diagnosticRows,diagnosticWriteFailure},relay:relay.state(),metrics:{...metrics},bytesRead,bytesSaved,reports,closed,videoProofCommits,videoTaskStopReason,sourceJPEGBytes,clockDiagnostics:clockJournal.snapshot(),sourceReplacements,sourceClock:sourceClock?{...sourceClock}:null,publisherCounters:publisherCounters?{...publisherCounters}:null,sourceKind:'SYNTHETIC',actualImages:0});
  async function readBody(req, max) {
    const chunks = []; let count = 0;
    const timer = setTimeout(() => req.destroy(Error('BODY_DEADLINE')), MEDIA_LIMITS.bodyDeadlineMs);
    try { for await (const chunk of req) { count += chunk.length; bytesRead += chunk.length; if (count > max || bytesRead > MEDIA_LIMITS.runBody) throw Error('BODY_OR_RUN_BYTE_BOUND'); chunks.push(chunk); } return Buffer.concat(chunks); } finally { clearTimeout(timer); }
  }
  function readFrame(frameRef) {
    const ref = typeof frameRef === 'string' ? frameRef : frameRef?.frameRef;
    const q = decoded.get(ref), s = relay.session;
    if (q && typeof frameRef === 'object') for (const key of ['run','boot','configId','feed','frameId','timestampUs']) if (frameRef[key] !== undefined && frameRef[key] !== q[key]) throw Error('FRAME_REFERENCE_IDENTITY');
    if (!q || !s || closed || q.configId !== s.configId || q.boot !== s.boot || q.run !== s.run || nowMs() - q.registeredHostMs > MEDIA_LIMITS.frameFreshMs || nowMs() - q.relayReceivedHostMs > MEDIA_LIMITS.frameFreshMs) throw Error('FRESH_DECODED_FRAME_REQUIRED');
    return freezeCopy(q);
  }
  const server = http.createServer(async (req,res) => {
    const receivedMs = nowMs(); metrics.requests++;
    function send(status, value, mime = 'application/json') {
      if (res.destroyed || res.writableEnded || res.headersSent) return;
      const bytes = value instanceof Uint8Array ? value : Buffer.from(mime === 'application/json' ? JSON.stringify(value) : String(value));
      res.writeHead(status, {'Content-Type':mime,'Content-Length':bytes.length,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Access-Control-Allow-Origin':allowedOrigin,'Vary':'Origin','Content-Security-Policy':`default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' ${allowedOrigin}; img-src 'self' blob: data:; object-src 'none'; base-uri 'none'; frame-ancestors ${allowedOrigin}`}); res.end(bytes);
    }
    try {
      if (closed) throw Error('MEDIA_CLOSED');
      if(clockJournal.snapshot().fatal)throw Error('CLOCK_JOURNAL_FAILED');if (req.headers.host !== new URL(origin).host || req.headers.origin && ![origin,allowedOrigin].includes(req.headers.origin)) throw Error('HOST_OR_ORIGIN');
      if (req.method === 'OPTIONS') { res.writeHead(204, {'Access-Control-Allow-Origin':allowedOrigin,'Access-Control-Allow-Methods':'GET,POST,OPTIONS','Access-Control-Allow-Headers':'Authorization,Content-Type,X-Media-Nonce','Access-Control-Max-Age':'60'}); return res.end(); }
      const url = new URL(req.url, origin);
      if(req.method==='GET'&&staticAsset){const selected=await staticAsset(url.pathname);if(selected)return send(200,selected.bytes,selected.mime??selected.type);}
      if (req.method === 'GET' && ['/publisher','/publisher.mjs','/source-cadence.mjs','/viewer.mjs','/client.mjs','/network-bootstrap.mjs','/clock-lifecycle.mjs','/network-key-diagnostic.mjs','/relay-core.mjs','/codec-capabilities09.mjs'].includes(url.pathname)) {
        const filename = url.pathname === '/publisher' ? 'publisher.html' : url.pathname.slice(1);
        const file = filename === 'relay-core.mjs' ? path.join(REPO,'media/big02/relay-core.mjs') : path.join(REPO,'pilot/clockvideo05/media',filename);
        const selectedFile=filename==='viewer.mjs'?path.join(REPO,'planning/betasim-integrated01/product/viewer-codec09.mjs'):filename==='codec-capabilities09.mjs'?path.join(REPO,'planning/betasim-integrated01/product/codec-capabilities09.mjs'):file;let bytes=await fs.readFile(selectedFile);if(filename==='publisher.html')bytes=Buffer.from(bytes.toString().replaceAll('8873','8895'));return send(200,bytes,filename.endsWith('.html')?'text/html; charset=utf-8':'text/javascript');
      }
      if (req.method === 'GET' && url.pathname === '/api/bootstrap') {
        const role = url.searchParams.get('role'); if (!['publisher','viewer'].includes(role)) throw Error('EXPLICIT_ROLE_REQUIRED');
        return send(200,{serverBoot,bearer:bearer[role],nonce:serverBoot,viewerId,profiles,origin,allowedOrigin,role,engineeringSelection:structuredClone(engineeringSelection),sourceKind:'SYNTHETIC',scope:'HOST_ONLY_NO_CAMERA_NO_RADIOMETRY',state:state()});
      }
      const role = req.headers.authorization?.startsWith('Bearer ') ? Object.keys(bearer).find(k => tokenEqual(req.headers.authorization.slice(7),bearer[k])) : null;
      if (!role || req.headers['x-media-nonce'] !== serverBoot || req.method !== 'POST' || ![origin,allowedOrigin].includes(req.headers.origin)) throw Error('BEARER_NONCE_OR_MUTATION_ORIGIN');
      while (requestTimes.length && receivedMs - requestTimes[0] >= 1000) requestTimes.shift();
      if (requestTimes.length >= MEDIA_LIMITS.rate) throw Error('MEDIA_REQUEST_RATE'); requestTimes.push(receivedMs);
      if (url.pathname === '/api/chunk') {
        codecGate.sourceAllowed(relay.session);
        if (role !== 'publisher' || req.headers['content-type'] !== 'application/octet-stream') throw Error('PUBLISHER_BINARY_REQUIRED');
        const {meta,data} = decodePacket(await readBody(req,MEDIA_LIMITS.body));
        let frameProof=null;if(frameProofValidator){frameProof=frameProofs.get(meta.configId+':'+meta.frameId);if(!frameProof||frameProof.timestampUs!==meta.timestampUs)throw Error('ORIGINAL_FDM_FRAME_PROOF_REQUIRED_BEFORE_PUBLISH');verifyFrame(frameProof.metadata);}
        const sourceBounds = hostBounds(meta.timestampUs / 1000,sourceClock);
        const rejectionAt=nowMs(),clockReject=!sourceBounds?'OUTSIDE_MAPPING_WINDOW':sourceBounds.lowerMs>rejectionAt+20?'FUTURE_GT20MS':rejectionAt-sourceBounds.upperMs>1000?'STALE_GT1000MS':null;if(clockReject){clockJournal.append('SOURCE_CLOCK_REJECT',{serverBoot,session:relay.session?{run:relay.session.run,boot:relay.session.boot,configId:relay.session.configId,feed:relay.session.feed,profileId:relay.session.profileId}:null,frameId:meta.frameId,timestampUs:meta.timestampUs,rejectionAtHostMonoMs:rejectionAt,reason:clockReject,sourceBounds,sourceClock:sourceClock?{...sourceClock}:null});throw Error('SOURCE_CLOCK_STALE_OR_FUTURE');}
        const receivedMonoNs=process.hrtime.bigint().toString();const result = relay.publish(meta,data,receivedMonoNs);if(!result.accepted)diagnosticAggregate('ORIGINAL_RELAY_REJECTION_AGGREGATE',result.reason);
        if (result.accepted) { const frameRef = hash(serverBoot + ':' + meta.configId + ':' + meta.frameId); frames.set(frameRef,freezeCopy({...meta,frameRef,sourceHostBounds:sourceBounds,relayReceivedHostMs:nowMs(),sourceClock:{...sourceClock},serverBoot,frameProof:frameProof?{metadata:frameProof.metadata,originalRef:frameProof.originalRef,proof:frameProof.proof}:null,provenance:'SYNTHETIC_ENCODED_SOURCE_BROWSER_SELF_REPORT'})); while (frames.size > MEDIA_LIMITS.frames) frames.delete(frames.keys().next().value); diagnostic.observe({...meta,relayReceivedMonoNs:receivedMonoNs,recoveryId:relay.recoveryId,frameRef,sourceHostBounds:sourceBounds},data,relay.session); wake(); }
        return send(200,result);
      }
      if (req.headers['content-type'] !== 'application/json') throw Error('JSON_REQUIRED');
      const q = canonical(await readBody(req,url.pathname==='/api/source-exposure'?Math.ceil(2*2**20*4/3)+16384:url.pathname === '/api/report' ? 512 * 1024 : 65536));
      if(url.pathname==='/api/source-exposure'){if(role!=='publisher'||!exposure)throw Error('SOURCE_EXPOSURE_ORIGINAL_PENDING_REQUIRED');exact(q,['requestId','videoFrameId','configId','metadata','jpegBase64']);const current=exposure;if(q.requestId!==current.requestId||q.configId!==relay.session?.configId||!Number.isSafeInteger(q.videoFrameId)||q.metadata?.payloadDeviceId!==current.payloadId||q.metadata.feed!==(current.feed==='thermal'?'thermal-look':'rgb')||typeof q.jpegBase64!=='string'||q.jpegBase64.length>Math.ceil(2*2**20*4/3))throw Error('SOURCE_EXPOSURE_REQUEST_CONTEXT');current.guard();const proof=frameProofs.get(q.configId+':'+q.videoFrameId);if(!proof||hash(JSON.stringify(proof.metadata))!==hash(JSON.stringify(q.metadata)))throw Error('SOURCE_EXPOSURE_MATCHED_DURABLE_FRAME_PROOF');if(proof.proof.sourceAgeUpperMs>250||proof.committedAtHostMs<current.issuedHostMs||nowMs()-proof.committedAtHostMs>500)throw Error('SOURCE_EXPOSURE_ORIGINAL_FRESH_COMMIT_REQUIRED');const original=Buffer.from(q.jpegBase64,'base64'),size=jpegSize(original);if(original.length>2*2**20||sourceJPEGBytes+original.length>2**20||original.toString('base64')!==q.jpegBase64||size.width!==1280||size.height!==720||nowMs()-current.issuedHostMs>500)throw Error('SOURCE_EXPOSURE_ORIGINAL_JPEG_BOUND');current.guard();sourceJPEGBytes+=original.length;clearTimeout(current.timer);exposure=null;current.resolve({requestId:q.requestId,videoFrameId:q.videoFrameId,metadata:freezeCopy(q.metadata),originalBytes:original,originalFrameProofRef:proof.originalRef,sourceSession:freezeCopy(relay.session)});return send(200,{acceptedForFileTransaction:true,fileDurable:false,sourceImageSHA256:hash(original),hardwareImages:0});}
      if(['/api/frame-proof','/api/frame-proofs'].includes(url.pathname)){if(role!=='publisher'||!frameProofValidator)throw Error('ROOT_PAYLOAD_CAMERA_PROOF_PROVIDER_REQUIRED');const batch=url.pathname==='/api/frame-proofs';exact(q,batch?['configId','frames']:['configId','frameId','timestampUs','metadata']);const list=batch?q.frames:[{frameId:q.frameId,timestampUs:q.timestampUs,metadata:q.metadata}];if(q.configId!==relay.session?.configId||!Array.isArray(list)||list.length<1||list.length>2)throw Error('PAYLOAD_FRAME_PROOF_BATCH2');if(videoTaskStopReason||videoProofCommits>=MEDIA_LIMITS.videoProofCommits||!proofCapture.canStageUncompressed(8192)){videoTaskStopReason='VIDEO_PROOF_TASK_RESERVE_EXHAUSTED_SOURCE_STOP_QUALITY_NOT_READY';relay.close();throw Error(videoTaskStopReason);}videoProofCommits++;const staged=[];for(const item of list){exact(item,['frameId','timestampUs','metadata']);if(!Number.isSafeInteger(item.frameId)||item.frameId<1||!Number.isSafeInteger(item.timestampUs)||item.timestampUs<0)throw Error('PAYLOAD_FRAME_PROOF_IDENTITY');const key=q.configId+':'+item.frameId;if(frameProofs.has(key)||staged.some(r=>r.key===key))throw Error('PAYLOAD_FRAME_PROOF_NO_REPLAY');const metadata=item.metadata;if(metadata?.format!=='aeris-sim-payload-video-frame'||metadata.version!==1||metadata.source!=='SEPARATE_PBR_PAYLOAD_CAMERA'||metadata.hardwareImages!==0||metadata.radiometric!==false||metadata.HeraCalibrated!==false)throw Error('PAYLOAD_CAMERA_PROOF_SCOPE');const proof=verifyFrame(metadata);if(proof?.proofKind!=='ROOT_PRIVATE_SCENE_RPC_ORIGINAL_FRAME'||!Number.isFinite(proof.sourceAgeUpperMs)||proof.sourceAgeUpperMs>250)throw Error('PAYLOAD_CAMERA_ROOT_ORIGINAL_250MS');const row={format:'aeris-video-frame-root-binding',version:1,configId:q.configId,frameId:item.frameId,timestampUs:item.timestampUs,rootFrame:metadata.frame,sampleHostNs:metadata.sampleHostNs,rawRef:metadata.rawRef,metadataSHA256:hash(JSON.stringify(metadata)),payloadDeviceId:metadata.payloadDeviceId,payloadCameraRevision:metadata.payloadCameraRevision,source:'SEPARATE_PBR_PAYLOAD_CAMERA',hardwareImages:0};if(Buffer.byteLength(JSON.stringify(row))>3072)throw Error('PAYLOAD_FRAME_BINDING_BUDGET3072');const record=proofCapture.append('SOURCE_FRAME_BOUND',row);staged.push({key,metadata,proof,row,record,timestampUs:item.timestampUs});}const proofCommitStart=nowMs(),commit=await proofCapture.beforeWire(),proofCommitMs=nowMs()-proofCommitStart,stage=stageTotals.proofCommit;stage.count++;stage.totalMs+=proofCommitMs;stage.maximumMs=Math.max(stage.maximumMs,proofCommitMs);stage.buckets[[1,5,10,20,50,100,250].findIndex(x=>proofCommitMs<=x)<0?7:[1,5,10,20,50,100,250].findIndex(x=>proofCommitMs<=x)]++;if(diagnosticRows<64&&(stage.count&(stage.count-1))===0){diagnosticRows++;clockJournal.append('ORIGINAL_PROOF_COMMIT_STAGE_AGGREGATE',{...stage,scope:'NODE_LOCAL_AWAIT_WRITER_DURATION_NOT_ROOT_CPU_OR_FS_ATTRIBUTION'});}for(const r of staged)r.proof=verifyFrame(r.metadata);const receipts=[];for(const r of staged){const originalRef={...commit.lastRef,logicalRowSHA256:r.record.sha256};frameProofs.set(r.key,freezeCopy({metadata:r.metadata,originalRef,proof:r.proof,committedAtHostMs:nowMs(),timestampUs:r.timestampUs}));while(frameProofs.size>180)frameProofs.delete(frameProofs.keys().next().value);receipts.push({frameId:r.row.frameId,committed:true,originalRef,metadataSHA256:r.row.metadataSHA256,hardwareImages:0});}return send(200,batch?{committed:true,frames:receipts}:receipts[0]);}
      if(url.pathname.startsWith('/api/diagnostic-')){if(role!=='viewer')throw Error('VIEWER_REQUIRED');if(url.pathname==='/api/diagnostic-arm'){exact(q,['session']);return send(200,await diagnostic.arm(q.session,()=>relay.session));}if(url.pathname==='/api/diagnostic-status'){exact(q,['id','session']);return send(200,await diagnostic.status(q.id,q.session,()=>relay.session));}if(url.pathname==='/api/diagnostic-key'){exact(q,['id','session']);return send(200,await diagnostic.bytes(q.id,q.session,()=>relay.session),'application/octet-stream');}if(url.pathname==='/api/diagnostic-report'){exact(q,['id','session','report']);return send(200,await diagnostic.save(q.id,q.session,()=>relay.session,q.report));}throw Error('KEY_DIAGNOSTIC_ROUTE');}
      if(url.pathname==='/api/clock-diagnostics'){const {events,normalizations}=normalizeClockDiagnostics(q,role,viewerId);for(const [index,event] of events.entries())clockJournal.append('BROWSER_CLOCK_EVENT',{serverBoot,role,event,...normalizations[index]?{sessionNormalization:normalizations[index]}:{}});return send(200,{saved:true,rows:events.length,dropped:q.dropped,diagnosticOnly:true});}
      if (url.pathname === '/api/clock') { exact(q,['browserSendMs']); if (!Number.isFinite(q.browserSendMs)) throw Error('CLOCK_REQUEST'); metrics.clockRequests++;const serverSentMs=nowMs();send(200,{serverBoot,serverReceivedMs:receivedMs,serverSentMs,domain:'NODE_HRTIME_MS'});clockJournal.append('CLOCK_PROBE_REPLY',{serverBoot,role,browserSendMs:q.browserSendMs,serverReceivedMs:receivedMs,serverSentMs});return; }
      if(url.pathname==='/api/codec-capabilities'){exact(q,['batch']);return send(200,await codecGate.capabilities(q.batch,role));}
      if(url.pathname==='/api/codec-readiness'){exact(q,[]);return send(200,codecGate.readiness());}
      if(url.pathname==='/api/decoder-frame'){if(role!=='viewer')throw Error('VIEWER_REQUIRED');exact(q,['capabilityId','targetEpoch','session','firstKey','warmKeyFrameId','latest','decoderOutputs','displayBrowserMs','viewerClock']);return send(200,await codecGate.decoded(q,frames,clock(q.viewerClock)));}
      if(url.pathname==='/api/receiver-ended'){if(role!=='viewer')throw Error('VIEWER_REQUIRED');exact(q,['capabilityId','targetEpoch','reason']);return send(200,await codecGate.end(q));}
      if (url.pathname === '/api/state') { exact(q,[]); return send(200,state()); }
      if (url.pathname === '/api/new-source') {
        if (role !== 'publisher' || ++controls > MEDIA_LIMITS.controls || sourceReplacements>=8) throw Error('PUBLISHER_SOURCE_REPLACEMENT_BOUND');
        exact(q,['previousConfigId','session','clock']);const previous=relay.session;
        if(!previous||q.previousConfigId!==previous.configId)throw Error('PREVIOUS_SOURCE_CONFIG_FENCE');
        if(q.session.run===previous.run||q.session.boot===previous.boot||sourceRuns.has(q.session.run)||sourceBoots.has(q.session.boot)||configuredSessions.has(q.session.configId)||configuredSessions.size>=32||q.session.viewerId!==viewerId)throw Error('NEW_SOURCE_IDENTITY_OR_REPLAY');
        codecGate.configure(q.session);const nextClock=clock(q.clock),nextRelay=new Relay01(profiles.profiles.map(p=>p.id));nextRelay.configure(q.session);
        const retired={run:previous.run,boot:previous.boot,configId:previous.configId};relay.close();relay=nextRelay;sourceClock=nextClock;clockJournal.append('SOURCE_CONFIGURED',{serverBoot,session:{...q.session},sourceClock:{...sourceClock},replacement:true});frames.clear();decoded.clear();publisherCounters=null;configuredSessions.set(q.session.configId,freezeCopy(q.session));sourceRuns.add(q.session.run);sourceBoots.add(q.session.boot);sourceReplacements++;wake();
        await write('source-replacement-'+String(sourceReplacements).padStart(2,'0')+'.json',{at:new Date().toISOString(),retired,admitted:{...q.session},allPreviousFramesInvalidated:true,authorityRestored:false,provenance:'EXPLICIT_PUBLISHER_START_COMPARE_AND_SWAP_NEW_BOOT'});
        return send(200,relay.state());
      }
      if (url.pathname === '/api/configure') {
        if (role !== 'publisher' || ++controls > MEDIA_LIMITS.controls) throw Error('PUBLISHER_CONTROL_BOUND');
        exact(q,['session','clock']); if(configuredSessions.has(q.session.configId)||configuredSessions.size>=32)throw Error('GLOBAL_CONFIG_REPLAY_OR_BOUND'); const candidateClock = clock(q.clock); if (q.session.viewerId !== viewerId) throw Error('VIEWER_TARGET'); codecGate.configure(q.session);const result = relay.configure(q.session); configuredSessions.set(q.session.configId,freezeCopy(q.session));sourceRuns.add(q.session.run);sourceBoots.add(q.session.boot); sourceClock = candidateClock;clockJournal.append('SOURCE_CONFIGURED',{serverBoot,session:{...q.session},sourceClock:{...sourceClock},replacement:false}); frames.clear(); decoded.clear(); wake(); return send(200,result);
      }
      if (url.pathname === '/api/source-clock') {
        if (role !== 'publisher') throw Error('PUBLISHER_REQUIRED'); exact(q,['configId','clock']); if (q.configId !== relay.session?.configId) throw Error('CONFIG_FENCE'); sourceClock = clock(q.clock);clockJournal.append('SOURCE_MAPPING_APPLIED',{serverBoot,configId:q.configId,sourceClock:{...sourceClock}}); return send(200,{updated:true});
      }
      if (url.pathname === '/api/publisher-counters') {
        if (role !== 'publisher') throw Error('PUBLISHER_REQUIRED'); exact(q,['configId','counts']); if (q.configId !== relay.session?.configId) throw Error('CONFIG_FENCE'); exact(q.counts,['source','encoded','published','sourceDrops','outputDrops','rejected','apiFailures']); if (!Object.values(q.counts).every(v=>Number.isSafeInteger(v)&&v>=0&&v<1000000)) throw Error('COUNTER_BOUND'); publisherCounters = {...q.counts}; return send(200,{updated:true});
      }
      if (url.pathname === '/api/next') {
        if (role !== 'viewer') throw Error('VIEWER_REQUIRED'); exact(q,['viewerId','configId']); if (q.viewerId !== viewerId || q.configId !== relay.session?.configId) throw Error('VIEWER_CONFIG_TARGET');
        if (pending.size >= 1) throw Error('ONE_PENDING_VIEWER'); metrics.polls++;
        let packet = relay.take(viewerId);
        if (!packet) { await new Promise(resolve => { let done = false; const finish = () => { if (done) return; done = true; clearTimeout(timer); pending.delete(finish); resolve(); }; const timer = setTimeout(finish,180); pending.add(finish); req.once('aborted',finish); res.once('close',finish); }); if (q.configId !== relay.session?.configId) throw Error('CONFIG_CHANGED'); packet = relay.take(viewerId); }
        if (!packet) return send(204,new Uint8Array(),'application/octet-stream');
        const frameRef = hash(serverBoot + ':' + packet.meta.configId + ':' + packet.meta.frameId), frame = frames.get(frameRef); if (!frame) throw Error('FRAME_RETENTION');
        return send(200,encodePacket({...packet.meta,frameRef,sourceHostBounds:frame.sourceHostBounds},packet.data),'application/octet-stream');
      }
      if (url.pathname === '/api/resync') { if (role !== 'viewer') throw Error('VIEWER_REQUIRED'); exact(q,['viewerId','configId']); if (q.configId !== relay.session?.configId) throw Error('CONFIG_FENCE'); return send(200,relay.resync(q.viewerId)); }
      if (url.pathname === '/api/pause') {
        if (role !== 'viewer' || ++controls > MEDIA_LIMITS.controls) throw Error('VIEWER_CONTROL_BOUND');exact(q,['milliseconds','viewerId','configId']);
        if(q.viewerId!==viewerId||q.configId!==relay.session?.configId)throw Error('PAUSE_CONFIG_TARGET');if(q.milliseconds!==500)throw Error('FIXED_FAULT_WINDOW');
        const hostStartedNs=process.hrtime.bigint(),hostStartedMs=Number(hostStartedNs)/1e6,result=relay.pause(500,hostStartedNs.toString());
        return send(200,{...result,pause:{configId:q.configId,hostStartedMs,hostResumeNotBeforeMs:hostStartedMs+500,durationMs:500,clockDomain:'NODE_HRTIME_MS'}});
      }
      if (url.pathname === '/api/decoded') {
        if (role !== 'viewer') throw Error('VIEWER_REQUIRED'); exact(q,['frameRef','displayBrowserMs','clock']); const frame = frames.get(q.frameRef); if (!frame || frame.configId !== relay.session?.configId || nowMs() - frame.relayReceivedHostMs > 1000) throw Error('FRAME_UNKNOWN_OR_STALE');
        const viewerClock = clock(q.clock), displayHostBounds = hostBounds(q.displayBrowserMs,viewerClock); if (!displayHostBounds || displayHostBounds.lowerMs > nowMs() + 20 || nowMs() - displayHostBounds.upperMs > 1000) throw Error('DISPLAY_CLOCK_STALE_OR_FUTURE');
        const record = {...frame,sourceRun:frame.run,sourceBoot:frame.boot,sourceTimestampUs:frame.timestampUs,referenceHostMonoMs:(frame.sourceHostBounds.lowerMs+frame.sourceHostBounds.upperMs)/2,sourceToHostLowerMs:frame.sourceClock.lowerMs,sourceToHostUpperMs:frame.sourceClock.upperMs,clockDomain:'NODE_HRTIME_MS',displayBrowserMs:q.displayBrowserMs,displayHostBounds,viewerClock,registeredHostMs:nowMs(),decodeEvidence:'VIEWER_SELF_REPORTED_WEBCODECS_CANVAS_NOT_INDEPENDENT_SENSOR_VERIFICATION'};
        if (decoded.has(q.frameRef)) throw Error('DECODED_FRAME_REPLAY'); decoded.set(q.frameRef,freezeCopy(record)); while (decoded.size > 32) decoded.delete(decoded.keys().next().value); metrics.decodedRegistrations++; return send(200,record);
      }
      if (url.pathname === '/api/report') {
        if (role !== 'viewer' || reports >= MEDIA_LIMITS.reports) throw Error('REPORT_QUOTA_OR_ROLE');
        const reportedSession=configuredSessions.get(q.configId),windows=q.format==='aeris-betasim-lossless-video-windows'?decodeWindowGroup(q):[q];let samples=0;for(const w of windows){if(w.format!=='aeris-field01-media-report'||w.serverBoot!==serverBoot||!reportedSession||w.run!==reportedSession.run||w.boot!==reportedSession.boot||w.feed!==reportedSession.feed||w.profileId!==reportedSession.profileId||!Array.isArray(w.samples)||w.samples.length>4096||w.sampleCount!==w.samples.length||w.sourceKind!=='SYNTHETIC')throw Error('REPORT_IDENTITY_OR_BOUND');samples+=w.sampleCount;}if(reportedSamples+samples>8*4096)throw Error('REPORT_AGGREGATE32768');reportedSamples+=samples;
        return send(200,await write(`report-${String(++reports).padStart(2,'0')}.json`,{...q,server:state(),receivedAt:new Date().toISOString(),provenance:'BROWSER_SELF_REPORT_REAL_LOCALHOST_TCP_NOT_PHYSICAL_LATENCY'}));
      }
      throw Error('NO_CONTROL_API_OR_UNKNOWN_ENDPOINT');
    } catch (error) { metrics.rejected++;diagnosticAggregate('ORIGINAL_MEDIA_HTTP_REJECTION_AGGREGATE',String(error.message).slice(0,96));send(400,{error:error.message,scope:'MEDIA_ONLY_NO_FLIGHT_AUTHORITY'}); }
  });
  server.requestTimeout = MEDIA_LIMITS.requestDeadlineMs; server.headersTimeout = 2500; server.keepAliveTimeout = 1000; server.maxConnections = 12;
  async function close() { if (closed) return writeChain; closed = true;if(exposure){clearTimeout(exposure.timer);exposure.reject(Error('SOURCE_MEDIA_CLOSED_PENDING_EXPOSURE_UNKNOWN'));exposure=null;} clearInterval(guard); clearTimeout(lifetime); relay.close(); wake(); await new Promise(resolve => { server.close(resolve); server.closeAllConnections(); }); const clockClosure=await clockJournal.close(),frameProofClosure=await proofCapture.close();await write('closure.json',{...state(),clockClosure,frameProofClosure,closedAt:new Date().toISOString()}); }
  async function listen() { await new Promise((resolve,reject) => { server.once('error',reject); server.listen(port,'127.0.0.1',resolve); }); origin = `http://127.0.0.1:${server.address().port}`; if (schedule) { guard = setInterval(async () => { try { verifyGuard();await capture.flush(); } catch { await close(); } },1000); lifetime = setTimeout(() => close(),MEDIA_LIMITS.lifetimeMs); } return {origin,serverBoot}; }
  return {requiredVideoReadiness,listen,close,readFrame,state,server,pendingExposure,requestExposure,readReport(name){const r=savedReports.get(name);if(!r)throw Error('ROOT_MEDIA_REPORT_NOT_COMMITTED');return{...r,bytes:Buffer.from(r.bytes)};},get relay(){return relay;},get origin(){return origin;},serverBoot};
}
