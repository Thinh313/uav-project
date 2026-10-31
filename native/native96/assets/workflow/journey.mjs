import {defaultForm, checkedForm, compileForm, draftBody, restoreBody, sha} from './editor.mjs';
import {PINS} from './pins.mjs';

export const LIMITS = Object.freeze({bytes:262144, history:4, events:256});
const terminal = p => p === 'COMPLETED_MOCK' || p.startsWith('INTERRUPTED_');
const active = p => ['RUNNING_MOCK','AWAITING_MOCK_LANDING'].includes(p);
const keys = (o, expected) => {
  if (!o || Object.keys(o).sort().join() !== expected.slice().sort().join()) throw Error('Schema keys');
};
const reportKeys = ['format','version','session','missionForm','missionSha256','compiledRaw','sourceId','phase','cursor','events','eventChainTail','media','flightExecutionProven','physicalMediaVerified','authorityRestorable'];
const eventKeys = ['n','session','missionSha256','epoch','kind','elapsedMs','cursor','phase','previousSha256'];

// Independent semantic replay: a rehashed fabricated completion must still fail.
export async function validateReport(r) {
  keys(r, reportKeys);
  if (r.format !== 'aeris-native33-mock-session' || r.version !== 1 || r.sourceId !== PINS.coreSourceId ||
      !/^[a-f0-9-]{36}$/.test(r.session) || r.flightExecutionProven !== false ||
      r.physicalMediaVerified !== false || r.authorityRestorable !== false ||
      !Array.isArray(r.media) || r.media.length || !Array.isArray(r.events) ||
      !r.events.length || r.events.length > LIMITS.events) throw Error('Report scope/bound');
  const c = await compileForm(r.missionForm);
  if (c.compiledRaw !== r.compiledRaw || c.missionSha256 !== r.missionSha256) throw Error('Mission/form lineage');
  let phase = 'EMPTY', cursor = 0, home = false, datum = false, tail = null, epoch = null, clock = -1, inspected=null;
  const epochs = new Set();
  for (let i=0; i<r.events.length; i++) {
    const e = r.events[i]; keys(e,['body','canonicalBody','sha256']); keys(e.body,eventKeys);
    const b = e.body;
    if (JSON.stringify(b) !== e.canonicalBody || await sha(e.canonicalBody) !== e.sha256 ||
        b.n !== i+1 || b.session !== r.session || b.missionSha256 !== r.missionSha256 ||
        b.previousSha256 !== tail || !/^[a-f0-9-]{36}$/.test(b.epoch) ||
        !Number.isSafeInteger(b.elapsedMs) || b.elapsedMs < 0) throw Error('Event chain/identity');
    if (b.epoch !== epoch) {
      if (epochs.has(b.epoch) || (i>0 && b.kind !== 'INTERRUPTED_RESTART')) throw Error('Epoch discontinuity');
      epochs.add(b.epoch); epoch=b.epoch; clock=-1;
    }
    if (b.elapsedMs < clock || terminal(phase)) throw Error('Clock/terminal event');
    clock=b.elapsedMs;
    switch (b.kind) {
      case 'COMPILED': if (phase !== 'EMPTY') throw Error('Compile sequence'); phase='COMPILED_DRAFT'; break;
      case 'PREFLIGHT_CHECK': if (!['COMPILED_DRAFT','PREFLIGHT_CONFIRM'].includes(phase)) throw Error('Inspect sequence'); home=datum=false; inspected=b.elapsedMs; phase='PREFLIGHT_CONFIRM'; break;
      case 'HOME_CONFIRMED': if (phase !== 'PREFLIGHT_CONFIRM' || b.elapsedMs-inspected>30000) throw Error('Home sequence'); home=true; break;
      case 'DATUM_CONFIRMED': if (phase !== 'PREFLIGHT_CONFIRM' || b.elapsedMs-inspected>30000) throw Error('Datum sequence'); datum=true; break;
      case 'MOCK_STARTED': if (phase !== 'PREFLIGHT_CONFIRM' || !home || !datum || b.elapsedMs-inspected>30000) throw Error('Start sequence'); phase='RUNNING_MOCK'; break;
      case 'ACK_NOT_EXECUTION': if (phase !== 'RUNNING_MOCK') throw Error('ACK sequence'); break;
      case 'POINT_OBSERVED': if (phase !== 'RUNNING_MOCK') throw Error('Progress sequence'); cursor++; if (cursor === c.geometry.waypoints.length) phase='AWAITING_MOCK_LANDING'; break;
      case 'LANDING_OBSERVED': if (phase !== 'AWAITING_MOCK_LANDING') throw Error('Landing sequence'); phase='COMPLETED_MOCK'; break;
      case 'INTERRUPTED_RESTART': case 'INTERRUPTED_BACKGROUND': case 'INTERRUPTED_LINK': case 'INTERRUPTED_NEW_PLAN': case 'INTERRUPTED_DRAFT_EDIT':
        if (phase === 'EMPTY') throw Error('Interruption sequence'); phase=b.kind; break;
      default: throw Error('Unknown event');
    }
    if (b.cursor !== cursor || b.phase !== phase) throw Error('Event state mismatch');
    tail=e.sha256;
  }
  if (r.phase !== phase || r.cursor !== cursor || r.eventChainTail !== tail) throw Error('Report tail/state');
  return r;
}

export async function validateWorkspace(raw) {
  if (typeof raw !== 'string' || new TextEncoder().encode(raw).length > LIMITS.bytes) throw Error('Workspace byte bound');
  const w=JSON.parse(raw); keys(w,['format','version','sourceId','operational','authorityRestorable','draft','history','current']);
  if (w.format !== 'aeris-native33-workspace' || w.version !== 1 || w.sourceId !== PINS.coreSourceId ||
      w.operational !== false || w.authorityRestorable !== false || !Array.isArray(w.history) || w.history.length > LIMITS.history) throw Error('Workspace scope/version');
  await restoreBody(JSON.stringify(w.draft));
  const ids=new Set();
  for (const r of [...w.history,...(w.current ? [w.current]:[])]) {
    await validateReport(r); if (ids.has(r.session)) throw Error('Repeated session'); ids.add(r.session);
  }
  if (w.history.some(r=>!terminal(r.phase))) throw Error('Unclosed history');
  if(w.current && !terminal(w.current.phase) && JSON.stringify(w.current.missionForm)!==JSON.stringify(w.draft.form)) throw Error('Active draft/mission mismatch');
  return w;
}

async function append(r,kind,t,epoch,phase=r.phase,cursor=r.cursor) {
  if (r.events.length >= LIMITS.events) throw Error('Event limit; evidence retained');
  const last=r.events.at(-1)?.body;
  if (!Number.isSafeInteger(t) || t<0 || last && last.epoch === epoch && t<last.elapsedMs) throw Error('Clock regression');
  const body={n:r.events.length+1,session:r.session,missionSha256:r.missionSha256,epoch,kind,elapsedMs:t,cursor,phase,previousSha256:r.eventChainTail};
  const canonicalBody=JSON.stringify(body), digest=await sha(canonicalBody);
  r.events.push({body,canonicalBody,sha256:digest}); r.eventChainTail=digest; r.phase=phase; r.cursor=cursor;
}

export class DurableJourney {
  constructor(storage) {
    this.storage=storage; this.epoch=crypto.randomUUID(); this.form=defaultForm();
    this.workspace=null; this.token='ROOT'; this.revision=0; this.bundle=null; this.observation=null;
    this.home=this.datum=false; this.focused=true; this.blocked=true; this.dirty=true; this.locked=false;
  }
  get phase() { return this.blocked ? 'STORAGE_UNCONFIRMED' : this.bundle ? this.workspace.current.phase : 'DRAFT'; }
  get running() { return this.bundle && active(this.workspace.current.phase); }
  revoke() { this.observation=null; this.home=this.datum=false; }
  guardClock(t) {
    const last=this.workspace?.current?.events.at(-1)?.body;
    if(!Number.isSafeInteger(t)||t<0||last?.epoch===this.epoch&&t<last.elapsedMs){this.blocked=true;this.revoke();throw Error('Clock regression; reload required');}
  }
  async exclusive(fn) { if(this.locked) throw Error('Operation busy'); this.locked=true; try{return await fn();}finally{this.locked=false;} }
  async commit(w) {
    const raw=JSON.stringify(w);
    try {
      await validateWorkspace(raw);
      const d=await this.storage('save',this.token,raw);
      const exact=new TextDecoder().decode(Uint8Array.from(atob(d.bodyBase64??''),c=>c.charCodeAt(0)));
      if (!d.ok || d.pending || exact!==raw || !/^[a-f0-9]{64}$/.test(d.token) || !Number.isSafeInteger(d.revision) || d.revision<this.revision) throw Error('Commit reply unknown/mismatched');
      this.workspace=w; this.token=d.token; this.revision=d.revision; this.dirty=false;
    } catch(e) { this.blocked=true; this.revoke(); throw Error('Chưa xác nhận lưu; đọc lại rõ ràng, không tự retry: '+e.message); }
  }
  async load(t) { return this.exclusive(async()=>{
    this.blocked=true; this.bundle=null; this.revoke(); this.epoch=crypto.randomUUID();
    const d=await this.storage('load','ROOT','');
    if(!d.ok || d.pending || d.authorityRestorable!==false ||
       !/^(ROOT|[a-f0-9]{64})$/.test(d.token) || !Number.isSafeInteger(d.revision) ||
       d.revision<0 || (d.bodyBase64 ? d.token==='ROOT'||d.revision===0 : d.token!=='ROOT'||d.revision!==0)) throw Error('Pending/invalid head; bảo toàn bằng chứng');
    const w=d.bodyBase64 ? await validateWorkspace(new TextDecoder().decode(Uint8Array.from(atob(d.bodyBase64),c=>c.charCodeAt(0)))) :
      {format:'aeris-native33-workspace',version:1,sourceId:PINS.coreSourceId,operational:false,authorityRestorable:false,draft:JSON.parse(await draftBody(defaultForm())),history:[],current:null};
    this.token=d.token; this.revision=d.revision; this.workspace=w; this.form=structuredClone(w.draft.form); this.dirty=!d.bodyBase64;
    if(w.current && !terminal(w.current.phase)) {
      const next=structuredClone(w); await append(next.current,'INTERRUPTED_RESTART',t,this.epoch,'INTERRUPTED_RESTART'); await this.commit(next);
    }
    this.blocked=false; return w.current?.phase;
  }); }
  edit(form) {
    if(this.blocked || this.locked || this.running) throw Error('Draft locked/storage unavailable');
    this.form=checkedForm(form); this.bundle=null; this.revoke(); this.dirty=true;
  }
  async save(t) { return this.exclusive(async()=>{
    if(this.blocked) throw Error('Storage unavailable'); this.guardClock(t);
    const changed=this.dirty, w=structuredClone(this.workspace); w.draft=JSON.parse(await draftBody(this.form));
    if(changed && w.current && !terminal(w.current.phase)) await append(w.current,'INTERRUPTED_DRAFT_EDIT',t,this.epoch,'INTERRUPTED_DRAFT_EDIT');
    await this.commit(w); if(changed) {this.bundle=null;this.revoke();}
  }); }
  async compile(t) { return this.exclusive(async()=>{
    if(this.blocked || this.running || !this.focused) throw Error('Không compile ở trạng thái này'); this.guardClock(t);
    this.bundle=null; this.revoke(); const c=await compileForm(this.form), w=structuredClone(this.workspace);
    if(w.current) {
      if(w.history.length >= LIMITS.history) throw Error('History quota; giữ nguyên hồ sơ, không tự xóa');
      if(!terminal(w.current.phase)) await append(w.current,'INTERRUPTED_NEW_PLAN',t,this.epoch,'INTERRUPTED_NEW_PLAN');
      w.history.push(w.current);
    }
    w.draft=JSON.parse(await draftBody(this.form));
    w.current={format:'aeris-native33-mock-session',version:1,session:crypto.randomUUID(),missionForm:structuredClone(this.form),missionSha256:c.missionSha256,compiledRaw:c.compiledRaw,sourceId:PINS.coreSourceId,phase:'EMPTY',cursor:0,events:[],eventChainTail:null,media:[],flightExecutionProven:false,physicalMediaVerified:false,authorityRestorable:false};
    await append(w.current,'COMPILED',t,this.epoch,'COMPILED_DRAFT'); await this.commit(w); this.bundle=c;
  }); }
  ready(t) { return !!(this.bundle && this.observation!==null && this.focused && !this.blocked && this.home && this.datum && t>=this.observation && t-this.observation<=30000 && this.phase==='PREFLIGHT_CONFIRM'); }
  async transition(kind,t) { return this.exclusive(async()=>{
    if(this.blocked || !this.bundle || !this.focused) throw Error('Cần compile/preflight mới'); this.guardClock(t);
    if(this.workspace.current.events.length>=LIMITS.events){this.blocked=true;this.revoke();throw Error('Event limit; evidence retained, reload required');}
    const w=structuredClone(this.workspace), r=w.current; let p=r.phase, cursor=r.cursor;
    if(terminal(p)) throw Error('Phiên đã kết thúc; tạo nhiệm vụ mới');
    switch(kind) {
      case 'PREFLIGHT_CHECK': if(!['COMPILED_DRAFT','PREFLIGHT_CONFIRM'].includes(p))throw Error('Không đối chiếu khi đang chạy'); p='PREFLIGHT_CONFIRM'; break;
      case 'HOME_CONFIRMED': case 'DATUM_CONFIRMED': if(p!=='PREFLIGHT_CONFIRM'||this.observation===null||t<this.observation||t-this.observation>30000)throw Error('Đối chiếu stale'); break;
      case 'MOCK_STARTED': if(!this.ready(t))throw Error('Preflight thiếu/stale'); p='RUNNING_MOCK';break;
      case 'ACK_NOT_EXECUTION': if(p!=='RUNNING_MOCK')throw Error('Không có phiên chạy');break;
      case 'POINT_OBSERVED': if(p!=='RUNNING_MOCK')throw Error('Không tiến tuyến');cursor++;if(cursor===this.bundle.geometry.waypoints.length)p='AWAITING_MOCK_LANDING';break;
      case 'LANDING_OBSERVED': if(p!=='AWAITING_MOCK_LANDING')throw Error('Chưa đủ tuyến và landing');p='COMPLETED_MOCK';break;
      case 'INTERRUPTED_LINK': p=kind;break;
      default: throw Error('Action refused');
    }
    await append(r,kind,t,this.epoch,p,cursor); await this.commit(w);
    if(kind==='PREFLIGHT_CHECK') {this.observation=t;this.home=this.datum=false;}
    if(kind==='HOME_CONFIRMED')this.home=true;
    if(kind==='DATUM_CONFIRMED')this.datum=true;
    if(terminal(p))this.revoke();
  }); }
  async background(t) {
    this.focused=false; this.revoke();
    if(this.blocked || !this.bundle || terminal(this.workspace.current.phase))return;
    // Wait for a previously admitted save; never overtake its head token.
    if(this.locked) { this.backgroundPending=t; return; }
    // Prepared gates are volatile. Do not start an unnecessary background write
    // competing with the next Activity/page's restart checkpoint.
    if(!active(this.workspace.current.phase))return;
    return this.exclusive(async()=>{
      const w=structuredClone(this.workspace); if(terminal(w.current.phase))return;
      const time=Math.max(t,w.current.events.at(-1).body.elapsedMs);
      await append(w.current,'INTERRUPTED_BACKGROUND',time,this.epoch,'INTERRUPTED_BACKGROUND'); await this.commit(w);
    });
  }
  async finishBackground() { const t=this.backgroundPending;this.backgroundPending=undefined;if(t!==undefined)await this.background(t); }
  focus() {this.focused=true;this.revoke();}
}
