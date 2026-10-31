import fs from'node:fs';import path from'node:path';import{randomUUID}from'node:crypto';import{fileURLToPath}from'node:url';
import{CONTRACT,EXERCISES,PROFILES,need}from'./contract.mjs';import{Journal,createContext,makePackage,verifyPackage,listRuns,guardRoot,writeExclusive,hash,readReceived}from'./journal.mjs';import{effectiveView}from'./engine.mjs';
const HERE=path.dirname(fileURLToPath(import.meta.url)),ROOT=fileURLToPath(new URL('../../',import.meta.url));
export function trainingAPI({root=path.join(ROOT,'evidence/coach02/workspace01')}={}){
 root=path.resolve(root);need(root.startsWith(path.join(ROOT,'evidence/coach02/')),'TRAINING_ROOT');const hostBoot=randomUUID();let active=null,busy=false;
 const assets={'/manual/':['manual.html','text/html'],'/manual/manual.mjs':['manual.mjs','text/javascript'],'/manual/manual.css':['manual.css','text/css'],'/manual/nav.css':['nav.css','text/css'],'/manual/input.mjs':['input.mjs','text/javascript'],'/manual/contract.mjs':['contract.mjs','text/javascript']};
 async function handle(req,send,{origin,csrf}){
  try{
   if(req.method==='GET'){
    if(assets[req.url]){const[f,t]=assets[req.url];return send(200,fs.readFileSync(path.join(HERE,f)),t);}
    if(req.url.startsWith('/api/training/'))guardRoot(root);
    if(req.url==='/api/training/state')return send(200,{hostBoot,contract:CONTRACT,exercises:EXERCISES,profiles:PROFILES,active:active?effectiveView(active.state,performance.now()):null,csrf,operational:false,physicalHidVerified:false});
    if(req.url==='/api/training/history')return send(200,listRuns(root));
    const received=req.url.match(/^\/api\/training\/received\/([a-f0-9]{64})$/);if(received)return send(200,readReceived(root,received[1]));
    const m=req.url.match(/^\/api\/training\/package\/(m[a-f0-9]{32})$/);if(m)return send(200,makePackage(root,m[1]));
    return send(404,{error:'NO_TRAINING_ROUTE'});
   }
   need(req.method==='POST','TRAINING_METHOD');need(req.headers.origin===origin&&req.headers['x-coach-csrf']===csrf,'TRAINING_ORIGIN_CSRF');need(!busy,'TRAINING_BUSY_NO_QUEUE');busy=true;
   try{
    const chunks=[];let size=0;const limit=req.url==='/api/training/import'?16*2**20:16384;need(Number(req.headers['content-length']??0)<=limit,'TRAINING_BODY_BOUND');const alarm=setTimeout(()=>req.destroy(Error('TRAINING_BODY_TIMEOUT')),8000);
    try{for await(const b of req){size+=b.length;need(size<=limit,'TRAINING_BODY_BOUND');chunks.push(b);}}finally{clearTimeout(alarm);}
    const bytes=Buffer.concat(chunks),input=JSON.parse(bytes);
    if(req.url==='/api/training/start'){
     need(!active||active.state.finished,'CLOSE_ACTIVE_TRAINING');need(fs.readdirSync(root).filter(n=>/^m[a-f0-9]{32}$/.test(n)).length<16,'TRAINING_RUN_QUOTA');
     active?.close();const t1=performance.now(),context=createContext(input,hostBoot),challenge={nonce:randomUUID(),t1,t2:performance.now()};active=new Journal(root,context,challenge,challenge.t2);
     return send(200,{context,challenge,state:effectiveView(active.state,performance.now()),durableRecord:active.count,head:active.head,authorityRestorable:false});
    }
    if(req.url==='/api/training/action'){
     need(active&&!active.poisoned,'NO_LIVE_TRAINING');need(input.kind!=='hostAbort','HOST_ACTION_PRIVATE');if(input.kind==='challenge'){input.serverNonce=randomUUID();input.t1=performance.now();input.t2=performance.now();}if(['neutral','grant','tick'].includes(input.kind)&&active.state.context.sourceKind==='BROWSER_KEYBOARD_MOCK')need(Array.isArray(input.heldCodes),'KEYBOARD_SNAPSHOT_REQUIRED');const result=active.action(input,performance.now());result.state=effectiveView(active.state,performance.now());return send(200,{...result,authorityRestorable:false});
    }
    if(req.url==='/api/training/abandon'){need(active&&!active.state.finished,'NO_PENDING_TRAINING');const result=active.action({kind:'hostAbort',hostBoot,reason:'OBSERVER_RESTART',observerClockId:input.sourceClockId},performance.now());return send(200,{...result,authorityRestorable:false});}
    if(req.url==='/api/training/import'){
     const checked=verifyPackage(bytes),archiveId=hash(bytes),name='received-'+archiveId+'.json',p=path.join(root,name);
     if(fs.existsSync(p))need(!fs.lstatSync(p).isSymbolicLink()&&fs.lstatSync(p).isFile()&&hash(fs.readFileSync(p))===hash(bytes),'TRAINING_IMPORT_COLLISION');else{need(fs.readdirSync(root).filter(n=>n.startsWith('received-')).length<32,'TRAINING_INBOX_QUOTA');writeExclusive(root,p,bytes);}
     return send(200,{...checked,archiveId,activeRestored:false});
    }
    return send(404,{error:'NO_TRAINING_CONTROL_ROUTE'});
   }finally{busy=false;}
  }catch(e){return send(400,{error:e.message,automaticRetry:false,authorityRestored:false});}
 }
 return{handle,close(){active?.close();active=null;},hostBoot};
}
