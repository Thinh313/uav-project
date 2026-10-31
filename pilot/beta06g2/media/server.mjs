import{normalizeClockDiagnostics}from'../clock-diagnostic-adapter.mjs';
import {createClockJournal,validateClockEvents} from '../../clockvideo05/media/clock-journal.mjs';
import {keyDiagnosticStore} from '../../clockvideo05/media/key-diagnostic-store.mjs';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomBytes, randomUUID, createHash, timingSafeEqual } from 'node:crypto';
import { Relay01, encodePacket, decodePacket, exact, LIMITS } from '../../../media/big02/relay-core.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(HERE, '../../..');
const PROFILE_PATH = path.join(REPO, 'media/big02/profile01.json');
export const MEDIA_LIMITS = Object.freeze({body: LIMITS.chunk + LIMITS.headers + 4, runBody: 1024 * 2 ** 20, evidence: 128 * 2 ** 20, frames: 180, reports: 8, controls: 96, rate: 150, bodyDeadlineMs: 1500, requestDeadlineMs: 2500, frameFreshMs: 1000, lifetimeMs: 1800000});
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
export async function createMediaServer({port = 8873, out, allowedOrigin = 'http://127.0.0.1:8872', schedule = true} = {}) {
  if (!out) throw Error('EXPLICIT_EVIDENCE_ROOT_REQUIRED');
  out = path.resolve(out);
  if (!out.startsWith(path.join(REPO, 'evidence/beta06/generation02/'))) throw Error('OWNED_EVIDENCE_PATH_REQUIRED');
  const free = async () => { const s = await fs.statfs(REPO, {bigint:true}); return s.bavail * s.bsize; };
  if (await free() < 20n * 1024n ** 3n + 128n * 1024n ** 2n) throw Error('MEDIA_DISK_ADMISSION');
  await fs.mkdir(out, {recursive:false});
  const clockJournal=createClockJournal(out);
  const profiles = JSON.parse(await fs.readFile(PROFILE_PATH, 'utf8'));
  let relay = new Relay01(profiles.profiles.map(p => p.id));
  const sourceRuns=new Set(),sourceBoots=new Set();let sourceReplacements=0;
  const serverBoot = randomUUID(), viewerId = randomUUID();
  const bearer = {publisher:randomBytes(32).toString('hex'), viewer:randomBytes(32).toString('hex')};
  const frames = new Map(), decoded = new Map(), configuredSessions = new Map(), pending = new Set(), requestTimes = [];
  let origin = `http://127.0.0.1:${port}`, sourceClock = null, bytesRead = 0, bytesSaved = 0, reports = 0, controls = 0, closed = false, writeChain = Promise.resolve(), guard, lifetime;
  let publisherCounters = null;
  let metrics = {requests:0, rejected:0, polls:0, clockRequests:0, decodedRegistrations:0, diskStop:false};
  const write = (name, value) => {
    const bytes = value instanceof Uint8Array ? Buffer.from(value) : Buffer.from(typeof value === 'string' ? value : JSON.stringify(value, null, 2) + '\n');
    const operation = writeChain.then(async () => { if (bytesSaved + bytes.length > MEDIA_LIMITS.evidence) throw Error('MEDIA_EVIDENCE_QUOTA'); await fs.writeFile(path.join(out,name), bytes, {flag:'wx',mode:0o600}); bytesSaved += bytes.length; return {file:name,sha256:hash(bytes)}; });
    writeChain = operation.catch(() => {}); return operation;
  };
  const diagnosticWrite=async(name,value)=>{const receipt=await write(name,value);const h=await fs.open(path.join(out,name),'r');try{await h.sync();}finally{await h.close();}const dir=await fs.open(out,'r');try{await dir.sync();}finally{await dir.close();}return receipt;};
  const diagnostic=keyDiagnosticStore({serverBoot,write:diagnosticWrite,isEnabled:out.startsWith(path.join(REPO,'evidence/field02/repair01/'))});
  await write('launch.json', {format:'aeris-field01-media-launch',serverBoot,pid:process.pid,profileSha256:hash(await fs.readFile(PROFILE_PATH)),at:new Date().toISOString(),source:'SYNTHETIC',transport:'REAL_LOCALHOST_HTTP_TCP',limits:MEDIA_LIMITS,physicalLatency:'NOT_MEASURED',actualImages:0});
  const wake = () => { for (const fn of pending) fn(); };
  const state = () => ({serverBoot,origin,relay:relay.state(),metrics:{...metrics},bytesRead,bytesSaved,reports,closed,clockDiagnostics:clockJournal.snapshot(),sourceReplacements,sourceClock:sourceClock?{...sourceClock}:null,publisherCounters:publisherCounters?{...publisherCounters}:null,sourceKind:'SYNTHETIC',actualImages:0});
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
      res.writeHead(status, {'Content-Type':mime,'Content-Length':bytes.length,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Access-Control-Allow-Origin':allowedOrigin,'Vary':'Origin','Content-Security-Policy':`default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' blob: data:; object-src 'none'; base-uri 'none'; frame-ancestors ${allowedOrigin}`}); res.end(bytes);
    }
    try {
      if (closed) throw Error('MEDIA_CLOSED');
      if(clockJournal.snapshot().fatal)throw Error('CLOCK_JOURNAL_FAILED');if (req.headers.host !== new URL(origin).host || req.headers.origin && ![origin,allowedOrigin].includes(req.headers.origin)) throw Error('HOST_OR_ORIGIN');
      if (req.method === 'OPTIONS') { res.writeHead(204, {'Access-Control-Allow-Origin':allowedOrigin,'Access-Control-Allow-Methods':'GET,POST,OPTIONS','Access-Control-Allow-Headers':'Authorization,Content-Type,X-Media-Nonce','Access-Control-Max-Age':'60'}); return res.end(); }
      const url = new URL(req.url, origin);
      if (req.method === 'GET' && ['/publisher','/publisher.mjs','/source-cadence.mjs','/viewer.mjs','/client.mjs','/network-bootstrap.mjs','/clock-lifecycle.mjs','/network-key-diagnostic.mjs','/relay-core.mjs'].includes(url.pathname)) {
        const filename = url.pathname === '/publisher' ? 'publisher.html' : url.pathname.slice(1);
        const file = filename === 'relay-core.mjs' ? path.join(REPO,'media/big02/relay-core.mjs') : path.join(REPO,'pilot/clockvideo05/media',filename);
        return send(200, await fs.readFile(file), filename.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/javascript');
      }
      if (req.method === 'GET' && url.pathname === '/api/bootstrap') {
        const role = url.searchParams.get('role'); if (!['publisher','viewer'].includes(role)) throw Error('EXPLICIT_ROLE_REQUIRED');
        return send(200,{serverBoot,bearer:bearer[role],nonce:serverBoot,viewerId,profiles,origin,allowedOrigin,role,sourceKind:'SYNTHETIC',scope:'HOST_ONLY_NO_CAMERA_NO_RADIOMETRY',state:state()});
      }
      const role = req.headers.authorization?.startsWith('Bearer ') ? Object.keys(bearer).find(k => tokenEqual(req.headers.authorization.slice(7),bearer[k])) : null;
      if (!role || req.headers['x-media-nonce'] !== serverBoot || req.method !== 'POST' || ![origin,allowedOrigin].includes(req.headers.origin)) throw Error('BEARER_NONCE_OR_MUTATION_ORIGIN');
      while (requestTimes.length && receivedMs - requestTimes[0] >= 1000) requestTimes.shift();
      if (requestTimes.length >= MEDIA_LIMITS.rate) throw Error('MEDIA_REQUEST_RATE'); requestTimes.push(receivedMs);
      if (url.pathname === '/api/chunk') {
        if (role !== 'publisher' || req.headers['content-type'] !== 'application/octet-stream') throw Error('PUBLISHER_BINARY_REQUIRED');
        const {meta,data} = decodePacket(await readBody(req,MEDIA_LIMITS.body));
        const sourceBounds = hostBounds(meta.timestampUs / 1000,sourceClock);
        const rejectionAt=nowMs(),clockReject=!sourceBounds?'OUTSIDE_MAPPING_WINDOW':sourceBounds.lowerMs>rejectionAt+20?'FUTURE_GT20MS':rejectionAt-sourceBounds.upperMs>1000?'STALE_GT1000MS':null;if(clockReject){clockJournal.append('SOURCE_CLOCK_REJECT',{serverBoot,session:relay.session?{run:relay.session.run,boot:relay.session.boot,configId:relay.session.configId,feed:relay.session.feed,profileId:relay.session.profileId}:null,frameId:meta.frameId,timestampUs:meta.timestampUs,rejectionAtHostMonoMs:rejectionAt,reason:clockReject,sourceBounds,sourceClock:sourceClock?{...sourceClock}:null});throw Error('SOURCE_CLOCK_STALE_OR_FUTURE');}
        const receivedMonoNs=process.hrtime.bigint().toString();const result = relay.publish(meta,data,receivedMonoNs);
        if (result.accepted) { const frameRef = hash(serverBoot + ':' + meta.configId + ':' + meta.frameId); frames.set(frameRef,freezeCopy({...meta,frameRef,sourceHostBounds:sourceBounds,relayReceivedHostMs:nowMs(),sourceClock:{...sourceClock},serverBoot,provenance:'SYNTHETIC_ENCODED_SOURCE_BROWSER_SELF_REPORT'})); while (frames.size > MEDIA_LIMITS.frames) frames.delete(frames.keys().next().value); diagnostic.observe({...meta,relayReceivedMonoNs:receivedMonoNs,recoveryId:relay.recoveryId,frameRef,sourceHostBounds:sourceBounds},data,relay.session); wake(); }
        return send(200,result);
      }
      if (req.headers['content-type'] !== 'application/json') throw Error('JSON_REQUIRED');
      const q = canonical(await readBody(req,url.pathname === '/api/report' ? 512 * 1024 : 65536));
      if(url.pathname.startsWith('/api/diagnostic-')){if(role!=='viewer')throw Error('VIEWER_REQUIRED');if(url.pathname==='/api/diagnostic-arm'){exact(q,['session']);return send(200,await diagnostic.arm(q.session,()=>relay.session));}if(url.pathname==='/api/diagnostic-status'){exact(q,['id','session']);return send(200,await diagnostic.status(q.id,q.session,()=>relay.session));}if(url.pathname==='/api/diagnostic-key'){exact(q,['id','session']);return send(200,await diagnostic.bytes(q.id,q.session,()=>relay.session),'application/octet-stream');}if(url.pathname==='/api/diagnostic-report'){exact(q,['id','session','report']);return send(200,await diagnostic.save(q.id,q.session,()=>relay.session,q.report));}throw Error('KEY_DIAGNOSTIC_ROUTE');}
      if(url.pathname==='/api/clock-diagnostics'){const {events,normalizations}=normalizeClockDiagnostics(q,role,viewerId);for(const [index,event] of events.entries())clockJournal.append('BROWSER_CLOCK_EVENT',{serverBoot,role,event,...normalizations[index]?{sessionNormalization:normalizations[index]}:{}});return send(200,{saved:true,rows:events.length,dropped:q.dropped,diagnosticOnly:true});}
      if (url.pathname === '/api/clock') { exact(q,['browserSendMs']); if (!Number.isFinite(q.browserSendMs)) throw Error('CLOCK_REQUEST'); metrics.clockRequests++;const serverSentMs=nowMs();send(200,{serverBoot,serverReceivedMs:receivedMs,serverSentMs,domain:'NODE_HRTIME_MS'});clockJournal.append('CLOCK_PROBE_REPLY',{serverBoot,role,browserSendMs:q.browserSendMs,serverReceivedMs:receivedMs,serverSentMs});return; }
      if (url.pathname === '/api/state') { exact(q,[]); return send(200,state()); }
      if (url.pathname === '/api/new-source') {
        if (role !== 'publisher' || ++controls > MEDIA_LIMITS.controls || sourceReplacements>=8) throw Error('PUBLISHER_SOURCE_REPLACEMENT_BOUND');
        exact(q,['previousConfigId','session','clock']);const previous=relay.session;
        if(!previous||q.previousConfigId!==previous.configId)throw Error('PREVIOUS_SOURCE_CONFIG_FENCE');
        if(q.session.run===previous.run||q.session.boot===previous.boot||sourceRuns.has(q.session.run)||sourceBoots.has(q.session.boot)||configuredSessions.has(q.session.configId)||configuredSessions.size>=32||q.session.viewerId!==viewerId)throw Error('NEW_SOURCE_IDENTITY_OR_REPLAY');
        const nextClock=clock(q.clock),nextRelay=new Relay01(profiles.profiles.map(p=>p.id));nextRelay.configure(q.session);
        const retired={run:previous.run,boot:previous.boot,configId:previous.configId};relay.close();relay=nextRelay;sourceClock=nextClock;clockJournal.append('SOURCE_CONFIGURED',{serverBoot,session:{...q.session},sourceClock:{...sourceClock},replacement:true});frames.clear();decoded.clear();publisherCounters=null;configuredSessions.set(q.session.configId,freezeCopy(q.session));sourceRuns.add(q.session.run);sourceBoots.add(q.session.boot);sourceReplacements++;wake();
        await write('source-replacement-'+String(sourceReplacements).padStart(2,'0')+'.json',{at:new Date().toISOString(),retired,admitted:{...q.session},allPreviousFramesInvalidated:true,authorityRestored:false,provenance:'EXPLICIT_PUBLISHER_START_COMPARE_AND_SWAP_NEW_BOOT'});
        return send(200,relay.state());
      }
      if (url.pathname === '/api/configure') {
        if (role !== 'publisher' || ++controls > MEDIA_LIMITS.controls) throw Error('PUBLISHER_CONTROL_BOUND');
        exact(q,['session','clock']); if(configuredSessions.has(q.session.configId)||configuredSessions.size>=32)throw Error('GLOBAL_CONFIG_REPLAY_OR_BOUND'); const candidateClock = clock(q.clock); if (q.session.viewerId !== viewerId) throw Error('VIEWER_TARGET'); const result = relay.configure(q.session); configuredSessions.set(q.session.configId,freezeCopy(q.session));sourceRuns.add(q.session.run);sourceBoots.add(q.session.boot); sourceClock = candidateClock;clockJournal.append('SOURCE_CONFIGURED',{serverBoot,session:{...q.session},sourceClock:{...sourceClock},replacement:false}); frames.clear(); decoded.clear(); wake(); return send(200,result);
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
        const reportedSession = configuredSessions.get(q.configId);
        if (q.format !== 'aeris-field01-media-report' || q.serverBoot !== serverBoot || !reportedSession || q.run !== reportedSession.run || q.boot !== reportedSession.boot || q.feed !== reportedSession.feed || q.profileId !== reportedSession.profileId || !Array.isArray(q.samples) || q.samples.length > 4096 || q.sampleCount !== q.samples.length || q.sourceKind !== 'SYNTHETIC') throw Error('REPORT_IDENTITY_OR_BOUND');
        return send(200,await write(`report-${String(++reports).padStart(2,'0')}.json`,{...q,server:state(),receivedAt:new Date().toISOString(),provenance:'BROWSER_SELF_REPORT_REAL_LOCALHOST_TCP_NOT_PHYSICAL_LATENCY'}));
      }
      throw Error('NO_CONTROL_API_OR_UNKNOWN_ENDPOINT');
    } catch (error) { metrics.rejected++; send(400,{error:error.message,scope:'MEDIA_ONLY_NO_FLIGHT_AUTHORITY'}); }
  });
  server.requestTimeout = MEDIA_LIMITS.requestDeadlineMs; server.headersTimeout = 2500; server.keepAliveTimeout = 1000; server.maxConnections = 12;
  async function close() { if (closed) return writeChain; closed = true; clearInterval(guard); clearTimeout(lifetime); relay.close(); wake(); await new Promise(resolve => { server.close(resolve); server.closeAllConnections(); }); const clockClosure=clockJournal.close();await write('closure.json',{...state(),clockClosure,closedAt:new Date().toISOString()}); }
  async function listen() { await new Promise((resolve,reject) => { server.once('error',reject); server.listen(port,'127.0.0.1',resolve); }); origin = `http://127.0.0.1:${server.address().port}`; if (schedule) { guard = setInterval(async () => { try { if (await free() < 20n * 1024n ** 3n + 128n * 1024n ** 2n) { metrics.diskStop = true; await close(); } } catch { await close(); } },1000); lifetime = setTimeout(() => close(),MEDIA_LIMITS.lifetimeMs); } return {origin,serverBoot}; }
  return {listen,close,readFrame,state,server,get relay(){return relay;},get origin(){return origin;},serverBoot};
}
if (process.argv[1] === fileURLToPath(import.meta.url)) { const out = process.argv[2]; const app = await createMediaServer({out}); console.log(JSON.stringify(await app.listen())); for (const signal of ['SIGINT','SIGTERM']) process.once(signal,() => app.close()); }
