/** QA-only deterministic VM for the actual served bootstrap. No listener or network.
 * Timer dispatch is explicitly separate from elapsed time, so late callback races
 * cannot pass merely because a fake timer happened to run in a convenient order.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {randomUUID,createHash} from 'node:crypto';
import {ClientSession02} from '../../pilot/field02/client-session.mjs';

const hash = data => createHash('sha256').update(data).digest('hex');
export const deferred = () => {
  let resolve,reject;
  const promise = new Promise((yes,no) => { resolve=yes; reject=no; });
  return {promise,resolve,reject};
};
export async function drain(turns=32) {
  assert(Number.isSafeInteger(turns) && turns>0 && turns<=256);
  for(let i=0;i<turns;i++) await Promise.resolve();
}
export function observe(promise) {
  const result={state:'PENDING',value:null,error:null};
  Promise.resolve(promise).then(value=>{result.state='FULFILLED';result.value=value;},
    error=>{result.state='REJECTED';result.error=String(error?.message??error);});
  return result;
}

export function bootstrapFixture(sourcePath,{fetchImpl=null}={}) {
  const source=fs.readFileSync(sourcePath,'utf8');
  assert(Buffer.byteLength(source)<=64*1024,'BOUNDED_BOOTSTRAP_SOURCE');
  let time=0,nextTimer=0;
  const timers=new Map(),intervals=[],requests=[],revocations=[],events=[];
  const server=new ClientSession02({now:()=>time,onRevoke:value=>revocations.push({...value,at:time})});
  const listeners=new Map();
  const add=(name,fn)=>{const rows=listeners.get(name)??[];rows.push(fn);listeners.set(name,rows);};
  const browser={FIELD02Environment:{foreground:true},addEventListener:add,
    dispatchEvent(event){events.push({type:event.type,at:time});for(const fn of listeners.get(event.type)??[])fn(event);return true;}};
  const document={hidden:false,body:{dataset:{}},addEventListener:add};
  const response=(status,value)=>({ok:status>=200&&status<300,status,json:async()=>structuredClone(value)});
  async function defaultFetch(url,options={}) {
    if(url==='/api/bootstrap')return response(200,{ok:true,csrf:'qa-bootstrap-csrf'});
    if(url==='/api/client-session') {
      const body=JSON.parse(options.body);
      try { return response(200,{ok:true,result:server.action(body)}); }
      catch(error) { return response(409,{ok:false,error:error.message}); }
    }
    throw Error('UNDECLARED_QA_FETCH_ROUTE:'+url);
  }
  const context=vm.createContext({window:browser,document,
    location:{href:'http://127.0.0.1:8872/?android=field02&instance=qa-heartbeat-instance'},
    URL,crypto:{randomUUID},performance:{now:()=>time},AbortController,Event,
    setTimeout(fn,delay){assert(Number.isFinite(delay)&&delay>=0);const id=++nextTimer;timers.set(id,{id,fn,due:time+delay});return id;},
    clearTimeout(id){timers.delete(id);},
    setInterval(fn,delay){assert(Number.isFinite(delay)&&delay>0);const timer={fn,delay};intervals.push(timer);return timer;},
    clearInterval(timer){const n=intervals.indexOf(timer);if(n>=0)intervals.splice(n,1);},
    fetch:async(url,options={})=>{
      assert(typeof url==='string');const body=options.body?JSON.parse(options.body):null;
      requests.push({url,body,at:time,signal:options.signal});
      return fetchImpl?fetchImpl({url,options,body,at:time,defaultFetch,response}):defaultFetch(url,options);
    }});
  const exposure='\n;globalThis.__qa={bounded,requestLife,getSession:()=>session};';
  vm.runInContext(source+exposure,context,{filename:sourcePath,timeout:1000});
  assert.equal(typeof context.__qa.bounded,'function');
  assert.equal(typeof context.__qa.requestLife,'function');
  assert.equal(typeof browser.field02LifecycleDiagnostics,'function');
  return {browser,document,server,requests,revocations,events,intervals,qa:context.__qa,
    source:{path:sourcePath,bytes:Buffer.byteLength(source),sha256:hash(source),
      effectiveTestExposureSha256:hash(source+exposure)},
    now:()=>time,setTime(value){assert(Number.isFinite(value)&&value>=time,'QA_CLOCK_MUST_NOT_REWIND');time=value;},
    dispatchDue(){let calls=0;for(const item of [...timers.values()].sort((a,b)=>a.due-b.due)){
      if(item.due>time||!timers.has(item.id))continue;
      timers.delete(item.id);assert(++calls<=128,'QA_TIMER_DISPATCH_BOUND');item.fn();
    }return calls;},
    heartbeatTick(){const tick=intervals.filter(x=>x.delay===750);assert.equal(tick.length,1,'EXACT_HEARTBEAT750');tick[0].fn();},
    diagnostics:()=>structuredClone(browser.field02LifecycleDiagnostics()),
    context:()=>browser.field02ClientContext(),
    boot:()=>browser.fieldBootstrap01(),
    timersPending:()=>timers.size,
    classification:'ACTUAL_BOOTSTRAP_VM_WITH_REAL_CLIENT_SESSION_CLASS;FAKE_DOM_CLOCK_FETCH;NO_HTTP_TCP_OR_ANDROID_PROOF'};
}
