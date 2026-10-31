// Independent, transport-free engineering model. No socket or flight command API.
const copy = v => structuredClone(v);
const id = v => typeof v === 'string' && /^[A-Za-z0-9_-]{1,64}$/.test(v);
const uint = (v, min, max) => Number.isInteger(v) && v >= min && v <= max;
const number = v => typeof v === 'number' && Number.isFinite(v);
const terminal = new Set(['REJECTED', 'OBSERVED_SIMULATION', 'UNKNOWN', 'TIMED_OUT_UNCERTAIN']);
export const POLICY = Object.freeze({heartbeatMs:3000, authorityMs:10000, deadlineMs:2000, history:256, maxPayloads:8});
export function validateRoute(r) {
  if (!r || !id(r.aircraftId) || !uint(r.systemId,1,255)) throw Error('Aircraft identity invalid');
  const c = r.camera, g = r.gimbal;
  if (!c || !uint(c.componentId,1,255) || !uint(c.deviceId,0,6) || !['component','proxy'].includes(c.kind)) throw Error('Camera route invalid');
  if (c.kind === 'component' && (c.componentId < 7 || c.deviceId !== 0)) throw Error('Camera component route invalid');
  if (c.kind === 'proxy' && (c.componentId !== 1 || c.deviceId < 1)) throw Error('Proxy camera must be explicitly addressed');
  if (g && (!uint(g.managerComponentId,1,255) || !uint(g.deviceId,1,255))) throw Error('Gimbal route invalid');
  return copy(r);
}
const cameraKey = r => `${r.aircraftId}/${r.systemId}/${r.camera.componentId}/${r.camera.deviceId}`;
const gimbalKey = r => r.gimbal && `${r.aircraftId}/${r.systemId}/${r.gimbal.managerComponentId}/${r.gimbal.deviceId}`;
export function validateCapabilities(c, route) {
  if (!c || !['capture','zoom','focus','gimbal'].every(k=>typeof c[k]==='boolean')) throw Error('Unknown capabilities');
  if (c.gimbal && !route.gimbal) throw Error('Gimbal manager missing');
  for (const [key,lo,hi] of [['zoomRange',1,100],['pitchRange',-180,180],['yawRange',-180,180]]) {
    if ((key==='zoomRange' ? c.zoom : c.gimbal) && (!Array.isArray(c[key]) || c[key].length!==2 || !c[key].every(number) || c[key][0]<lo || c[key][1]>hi || c[key][0]>=c[key][1])) throw Error('Capability limits invalid');
  }
  return copy(c);
}
export class PayloadSession {
  #s; #now; #last = -Infinity; #count = 0; #adapter;
  constructor({aircraftId='SIM-HERA', sessionId='sim-01', now=()=>performance.now(), adapter}={}) {
    if (!id(aircraftId) || !id(sessionId)) throw Error('Session identity invalid');
    if (adapter?.kind !== 'simulation' || typeof adapter.send !== 'function') throw Error('Real transport unavailable: observed configuration and hardware gates required');
    this.#now=now; this.#adapter=adapter;
    this.#s={format:'aeris-payload-simulation',version:1,origin:'SIMULATION',aircraftId,sessionId,link:false,selected:null,payloads:[],commands:[],events:[],droppedEvents:0,droppedCommands:0,aircraft:{mode:'DISCONNECTED',altitudeM:null,datum:'relative-to-synthetic-home',origin:'SIMULATION'},physicalMedia:[]};
  }
  #time() {const n=this.#now(); if (!number(n)||n<0||n<this.#last) throw Error('Monotonic clock invalid'); this.#last=n; return n;}
  #event(type,detail) {
    const e={index:++this.#count,atMs:this.#time(),sessionId:this.#s.sessionId,type,...copy(detail)};
    this.#s.events.push(e); if(this.#s.events.length>POLICY.history){this.#s.events.shift();this.#s.droppedEvents++;}
  }
  #payload(payloadId){const p=this.#s.payloads.find(p=>p.id===payloadId);if(!p)throw Error('Payload not discovered');return p;}
  connect() {if(this.#s.link)throw Error('Already connected');this.#s.link=true;this.#s.aircraft.mode='HOLD_SIMULATION';this.#s.aircraft.altitudeM=42;this.#event('AIRCRAFT_CONNECTED',{origin:'SIMULATION'});}
  disconnect() {
    this.#s.link=false;this.#s.aircraft.mode='DISCONNECTED';this.#s.aircraft.altitudeM=null;
    for(const p of this.#s.payloads){p.connected=false;p.discovered=false;p.authority=null;p.stream.live=false;this.#invalidate(p.id,'aircraft link lost');}
    this.#s.sessionId=`sim-${++this.#count}`;this.#event('AIRCRAFT_DISCONNECTED',{});
  }
  discover({id:payloadId,label,route,capabilities,streams}) {
    if(!this.#s.link)throw Error('Aircraft disconnected');
    route=validateRoute(route);capabilities=validateCapabilities(capabilities,route);
    if(!id(payloadId)||typeof label!=='string'||label.length<1||label.length>80||route.aircraftId!==this.#s.aircraftId)throw Error('Payload identity invalid');
    if(!Array.isArray(streams)||streams.length<1||streams.length>4||streams.some(s=>!id(s.id)||!['colour','thermal','survey'].includes(s.type))||new Set(streams.map(s=>s.id)).size!==streams.length)throw Error('Stream metadata invalid');
    if(this.#s.payloads.some(p=>p.id!==payloadId&&(cameraKey(p.route)===cameraKey(route)||(gimbalKey(route)&&gimbalKey(p.route)===gimbalKey(route)))))throw Error('Ambiguous duplicate route');
    const previous=this.#s.payloads.find(p=>p.id===payloadId);
    if(previous&&previous.discovered)throw Error('Explicit disconnect before rediscovery');
    if(!previous&&this.#s.payloads.length>=POLICY.maxPayloads)throw Error('Simulation payload limit');
    const n=this.#time();const p={id:payloadId,discoveryId:`discovery-${++this.#count}`,label,route,capabilities,streams:copy(streams),connected:true,discovered:true,lastHeartbeatMs:n,authority:null,gimbalFault:false,stream:{id:streams[0].id,live:true,lastFrameMs:n},settings:{zoom:capabilities.zoom?capabilities.zoomRange[0]:null,focus:null,pitchDeg:capabilities.gimbal?Math.max(capabilities.pitchRange[0],Math.min(capabilities.pitchRange[1],0)):null,yawDeg:capabilities.gimbal?Math.max(capabilities.yawRange[0],Math.min(capabilities.yawRange[1],0)):null},captureReceipts:0};
    if(previous)this.#s.payloads[this.#s.payloads.indexOf(previous)]=p;else this.#s.payloads.push(p);
    if(!this.#s.selected)this.#s.selected=payloadId;
    this.#event('DISCOVERED',{payloadId,route,capabilities,origin:'SIMULATION'});return copy(p);
  }
  select(payloadId) {this.#payload(payloadId);this.#s.selected=payloadId;this.#event('VIEW_SELECTED',{payloadId});}
  heartbeat(payloadId) {const p=this.#payload(payloadId);if(!this.#s.link||!p.connected||!p.discovered)throw Error('Explicit rediscovery required');p.lastHeartbeatMs=this.#time();}
  frame(payloadId) {const p=this.#payload(payloadId);if(p.connected&&p.stream.live)p.stream.lastFrameMs=this.#time();}
  stream(payloadId,streamId) {const p=this.#payload(payloadId);if(!p.streams.some(s=>s.id===streamId))throw Error('Unknown stream');p.stream.id=streamId;p.stream.lastFrameMs=this.#time();this.#event('STREAM_SELECTED',{payloadId,streamId});}
  authority(payloadId,owner) {
    const p=this.#payload(payloadId),n=this.#time();
    if(!this.#s.link||!p.discovered||!p.connected||n-p.lastHeartbeatMs>POLICY.heartbeatMs)throw Error('Discovery/heartbeat required');
    if(!['operator','mission','none'].includes(owner))throw Error('Authority invalid');
    const changed=(p.authority?.owner||'none')!==owner;
    p.authority=owner==='none'?null:{owner,atMs:n,origin:'SIMULATION_MANAGER_STATUS'};
    if(owner!=='operator')this.#invalidate(payloadId,'control authority lost');
    if(changed)this.#event('AUTHORITY_OBSERVED',{payloadId,owner});
  }
  fault(payloadId,type,on=true) {
    if(typeof on!=='boolean')throw Error('Fault flag invalid');const p=this.#payload(payloadId);
    if(type==='video')p.stream.live=!on;
    else if(type==='gimbal'){p.gimbalFault=on;if(on)this.#invalidate(payloadId,'gimbal fault','gimbal');}
    else if(type==='link'){if(!on)throw Error('Use explicit rediscovery');p.connected=false;p.discovered=false;p.authority=null;p.stream.live=false;this.#invalidate(payloadId,'payload disconnected');}
    else throw Error('Unknown fault');
    this.#event('FAULT',{payloadId,faultType:type,on});
  }
  #invalidate(payloadId,reason,operation) {for(const c of this.#s.commands)if(c.payloadId===payloadId&&!terminal.has(c.state)&&(!operation||c.operation===operation)){c.state='UNKNOWN';c.reason=reason;this.#event('COMMAND_UNCERTAIN',{commandId:c.id,reason});}}
  eligible(payloadId,operation) {
    const p=this.#payload(payloadId),n=this.#time();
    if(!this.#s.link)return 'Aircraft disconnected';
    if(!p.discovered||!p.connected)return 'Rediscover payload';
    if(n-p.lastHeartbeatMs>POLICY.heartbeatMs)return 'Payload heartbeat stale';
    if(!p.authority||p.authority.owner!=='operator'||n-p.authority.atMs>POLICY.authorityMs)return 'Acquire fresh control authority';
    if(!['capture','zoom','focus','gimbal'].includes(operation)||!p.capabilities[operation])return 'Operation unsupported';
    if(operation==='gimbal'&&p.gimbalFault)return 'Gimbal fault';
    if(this.#s.commands.some(c=>c.payloadId===payloadId&&!terminal.has(c.state)))return 'Await pending outcome';
    return null;
  }
  command(payloadId,operation,args={}) {
    this.tick();const reason=this.eligible(payloadId,operation);if(reason)throw Error(reason);
    const p=this.#payload(payloadId);
    if(!args||typeof args!=='object'||Array.isArray(args))throw Error('Arguments invalid');
    const keys=operation==='capture'?[]:operation==='zoom'?['value']:operation==='focus'?['value']:['pitchDeg','yawDeg'];
    if(Object.keys(args).length!==keys.length||!keys.every(k=>Object.hasOwn(args,k)))throw Error('Arguments invalid');
    if(operation==='zoom'&&(!number(args.value)||args.value<p.capabilities.zoomRange[0]||args.value>p.capabilities.zoomRange[1]))throw Error('Zoom out of range');
    if(operation==='focus'&&!['auto','near','far'].includes(args.value))throw Error('Focus mode invalid');
    if(operation==='gimbal'&&(!number(args.pitchDeg)||!number(args.yawDeg)||args.pitchDeg<p.capabilities.pitchRange[0]||args.pitchDeg>p.capabilities.pitchRange[1]||args.yawDeg<p.capabilities.yawRange[0]||args.yawDeg>p.capabilities.yawRange[1]))throw Error('Gimbal angles out of range');
    if(this.#s.commands.length>=POLICY.history){const i=this.#s.commands.findIndex(c=>terminal.has(c.state));if(i<0)throw Error('Command capacity');this.#s.commands.splice(i,1);this.#s.droppedCommands++;}
    const n=this.#time(),c={id:`cmd-${++this.#count}`,payloadId,discoveryId:p.discoveryId,sessionId:this.#s.sessionId,route:copy(p.route),operation,args:copy(args),state:'REQUESTED',requestedAtMs:n,deadlineMs:n+POLICY.deadlineMs,origin:'SIMULATION',units:{pitchDeg:'degree',yawDeg:'degree',zoom:'factor'}};
    this.#s.commands.push(c);this.#event('COMMAND_REQUESTED',{command:copy(c)});
    try{this.#adapter.send(copy(c),message=>this.feedback(message));}catch(e){c.state='UNKNOWN';c.reason='Adapter send failed';this.#event('SEND_FAILED',{commandId:c.id});}
    return copy(c);
  }
  feedback(m) {
    this.tick();const c=this.#s.commands.find(c=>c.id===m?.commandId);
    if(!c||terminal.has(c.state)||m.sessionId!==c.sessionId||m.discoveryId!==c.discoveryId||m.payloadId!==c.payloadId||JSON.stringify(m.route)!==JSON.stringify(c.route)||m.operation!==c.operation){this.#event('FEEDBACK_IGNORED',{reason:'mismatched, late or unknown feedback'});return false;}
    const p=this.#payload(c.payloadId);
    if(!this.#s.link||!p.discovered||!p.connected||p.discoveryId!==c.discoveryId||this.#time()-p.lastHeartbeatMs>POLICY.heartbeatMs||!p.authority||p.authority.owner!=='operator'||this.#time()-p.authority.atMs>POLICY.authorityMs){this.#invalidate(p.id,'feedback without fresh authority/link');return false;}
    if(m.type==='ack'&&c.state==='REQUESTED'&&['accepted','denied'].includes(m.result)){
      c.state=m.result==='accepted'?'ACK_ACCEPTED':'REJECTED';this.#event('COMMAND_ACK',{commandId:c.id,result:m.result});return true;
    }
    if(m.type==='observation'&&c.state==='ACK_ACCEPTED'&&m.origin==='SIMULATION'&&JSON.stringify(m.values)===JSON.stringify(c.args)){
      c.state='OBSERVED_SIMULATION';c.observedAtMs=this.#time();
      if(c.operation==='zoom')p.settings.zoom=c.args.value;
      if(c.operation==='focus')p.settings.focus=c.args.value;
      if(c.operation==='gimbal')Object.assign(p.settings,c.args);
      if(c.operation==='capture'){p.captureReceipts++;c.capture={origin:'SYNTHETIC_RECEIPT',physicalImage:false,mediaSha256:null};}
      this.#event('COMMAND_OBSERVED_SIMULATION',{commandId:c.id,capture:c.capture??null});return true;
    }
    this.#event('FEEDBACK_IGNORED',{reason:'invalid ACK/observation sequence or values'});return false;
  }
  tick() {const n=this.#time();for(const c of this.#s.commands)if(!terminal.has(c.state)&&n>=c.deadlineMs){c.state='TIMED_OUT_UNCERTAIN';this.#event('COMMAND_TIMEOUT',{commandId:c.id,noAutomaticRetry:true});}}
  snapshot() {this.tick();const n=this.#time(),s=copy(this.#s);for(const p of s.payloads){p.controlFresh=p.connected&&p.discovered&&n-p.lastHeartbeatMs<=POLICY.heartbeatMs;p.frameFresh=p.connected&&p.stream.live&&n-p.stream.lastFrameMs<=POLICY.heartbeatMs;p.authorityFresh=!!p.authority&&n-p.authority.atMs<=POLICY.authorityMs;}return s;}
  review() {const s=this.snapshot();return {...s,createdAt:new Date().toISOString(),complete:s.droppedEvents===0&&s.droppedCommands===0,physicalCaptureVerified:false,evidenceScope:'IN_MEMORY_SIMULATION_ONLY; not an execution archive or accepted survey handoff',policy:POLICY};}
}
