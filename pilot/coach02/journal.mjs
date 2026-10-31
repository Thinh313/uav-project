import fs from'node:fs';import path from'node:path';import{createHash,randomUUID}from'node:crypto';import{fileURLToPath}from'node:url';
import{canonical}from'../coach01/replay.mjs';import{diskGuard}from'../coach01/store.mjs';import{CONTRACT,PROFILES,EXERCISES,need}from'./contract.mjs';import{createState,apply,assess,effectiveView}from'./engine.mjs';
export const hash=x=>createHash('sha256').update(x).digest('hex');
const ROOT=fileURLToPath(new URL('../../',import.meta.url));
function bytesIn(dir){let total=0;for(const n of fs.readdirSync(dir)){const p=path.join(dir,n),s=fs.lstatSync(p);need(!s.isSymbolicLink(),'TRAINING_SYMLINK');if(s.isDirectory())total+=bytesIn(p);else{need(s.isFile(),'TRAINING_FILE_KIND');total+=s.size;}}return total;}
export function guardRoot(root,extra=0){need(diskGuard()-extra>=10*2**30+256*2**20,'TRAINING_DISK_RESERVE');root=path.resolve(root);need(root.startsWith(path.join(ROOT,'evidence/coach02/')),'TRAINING_ROOT');fs.mkdirSync(root,{recursive:true});need(!fs.lstatSync(root).isSymbolicLink(),'TRAINING_ROOT_LINK');need(bytesIn(root)+extra<=CONTRACT.maxStoreBytes,'TRAINING_QUOTA');return root;}
function syncDir(dir){const fd=fs.openSync(dir,'r');try{fs.fsyncSync(fd);}finally{fs.closeSync(fd);}}
export function writeExclusive(root,p,bytes){guardRoot(root,bytes.length);const fd=fs.openSync(p,'wx',0o600);try{fs.writeFileSync(fd,bytes);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}syncDir(path.dirname(p));}
function regular(p,max){const s=fs.lstatSync(p);need(s.isFile()&&!s.isSymbolicLink()&&s.size<=max,'TRAINING_REGULAR_BOUND');return fs.readFileSync(p);}
export class Journal{
 constructor(root,context,challenge,hostMs){
  const initial=createState(context,challenge,hostMs);this.root=guardRoot(root);this.dir=path.join(this.root,context.sessionId);need(!fs.existsSync(this.dir),'TRAINING_EXCLUSIVE_RUN');fs.mkdirSync(this.dir);syncDir(this.root);this.file=path.join(this.dir,'journal.jsonl');this.fd=fs.openSync(this.file,'wx',0o600);syncDir(this.dir);this.state=initial;this.head='0'.repeat(64);this.count=0;this.bytes=0;this.poisoned=false;
  try{this.append('START',{context,challenge,hostMs,contract:CONTRACT,profile:PROFILES[context.profileId],exercise:EXERCISES[context.exerciseId]});}catch(e){this.close();throw e;}
 }
 persist(bytes){let offset=0;while(offset<bytes.length){const n=fs.writeSync(this.fd,bytes,offset,bytes.length-offset);need(n>0,'TRAINING_SHORT_WRITE');offset+=n;}fs.fsyncSync(this.fd);}
 append(kind,data){
  need(!this.poisoned,'TRAINING_WRITER_POISONED');const row={n:this.count+1,previous:this.head,kind,data};row.sha256=hash(canonical(row));const bytes=Buffer.from(canonical(row)+'\n');
  need(row.n<=CONTRACT.maxRows&&this.bytes+bytes.length<=CONTRACT.maxRunBytes,'TRAINING_RUN_BOUND');guardRoot(this.root,bytes.length);
  try{this.persist(bytes);}catch(e){this.poisoned=true;throw e;}
  this.count++;this.head=row.sha256;this.bytes+=bytes.length;return row;
 }
 action(action,hostMs){
  need(!this.poisoned,'TRAINING_WRITER_POISONED');need(!this.state.finished,'TRAINING_ALREADY_CLOSED');const candidate=apply(this.state,action,hostMs);this.append('ACTION',{hostMs,action,outcome:candidate.outcome,state:candidate.state});this.state=candidate.state;
  if(this.state.finished){const receipt={format:'manual02-durable-closure',sessionId:this.state.context.sessionId,head:this.head,rows:this.count,authorityRestorable:false};try{writeExclusive(this.root,path.join(this.dir,'closure.json'),Buffer.from(canonical(receipt)));}catch(e){this.poisoned=true;throw e;}}
  return{...candidate.outcome,state:effectiveView(this.state,hostMs),durableRecord:this.count,head:this.head};
 }
 close(){if(this.fd!==null){fs.closeSync(this.fd);this.fd=null;}}
}
export function replay(rows){
 need(Array.isArray(rows)&&rows.length>0&&rows.length<=CONTRACT.maxRows,'TRAINING_ROWS');let head='0'.repeat(64),state=null,context=null;
 for(let i=0;i<rows.length;i++){
  const{sha256,...row}=rows[i];need(row.n===i+1&&row.previous===head&&sha256===hash(canonical(row)),'TRAINING_CHAIN');head=sha256;
  if(i===0){need(row.kind==='START'&&canonical(row.data.contract)===canonical(CONTRACT),'TRAINING_CONTRACT');const d=row.data;need(canonical(d.profile)===canonical(PROFILES[d.context.profileId])&&canonical(d.exercise)===canonical(EXERCISES[d.context.exerciseId]),'TRAINING_PROFILE_VERSION');context=d.context;state=createState(context,d.challenge,d.hostMs);}
  else{need(!state.finished,'TRAINING_AFTER_CLOSURE');need(row.kind==='ACTION','TRAINING_ROW_KIND');const d=row.data,next=apply(state,d.action,d.hostMs);need(canonical(next.outcome)===canonical(d.outcome)&&canonical(next.state)===canonical(d.state),'TRAINING_RECOMPUTE');state=next.state;}
 }
 return{head,state,context,review:assess(context,rows,state)};
}
function finalizedReview(replayed,closure){if(closure)need(closure.format==='manual02-durable-closure'&&closure.head===replayed.head&&closure.rows>0&&closure.sessionId===replayed.context.sessionId&&closure.authorityRestorable===false&&replayed.state.finished,'TRAINING_CLOSURE_CONTEXT');const review=structuredClone(replayed.review);const committed=closure?.format==='manual02-durable-closure'&&closure.head===replayed.head&&closure.rows>0&&closure.sessionId===replayed.context.sessionId&&closure.authorityRestorable===false;
 review.gates.durableClosureDeclared=committed;
 if(!committed){review.verdict='INCOMPLETE';review.limits.push('Closure receipt missing: no committed completion claim');}
 review.integrity='HASH_CHAIN_AND_MODEL_REPLAY_NOT_SOURCE_AUTHENTICATION';return review;
}
export function packageRows(rows,closure=null){const r=replay(rows);if(closure)need(closure.rows===rows.length,'CLOSURE_ROWS');const body={format:'aeris-manual02-package',version:1,source:'MOCK_REFERENCE_MODEL',operational:false,authorityRestorable:false,rows,head:r.head,closure,review:finalizedReview(r,closure)};return{...body,sha256:hash(canonical(body))};}
export function makePackage(root,id){need(/^m[a-f0-9]{32}$/.test(id),'TRAINING_ID');root=guardRoot(root);const dir=path.join(root,id);need(!fs.lstatSync(dir).isSymbolicLink(),'TRAINING_RUN_LINK');const raw=regular(path.join(dir,'journal.jsonl'),CONTRACT.maxRunBytes).toString();need(raw.endsWith('\n'),'TRAINING_TORN');const rows=raw.trimEnd().split('\n').map(JSON.parse),p=path.join(dir,'closure.json'),closure=fs.existsSync(p)?JSON.parse(regular(p,4096)):null;return packageRows(rows,closure);}
export function verifyPackage(bytes){
 need(bytes.length<=16*2**20,'TRAINING_PACKAGE_BOUND');const b=JSON.parse(bytes),{sha256,...body}=b;need(b.format==='aeris-manual02-package'&&b.version===1&&b.source==='MOCK_REFERENCE_MODEL'&&b.operational===false&&b.authorityRestorable===false&&sha256===hash(canonical(body)),'TRAINING_PACKAGE_SCOPE_DIGEST');
 const r=replay(b.rows);need(r.head===b.head&&(!b.closure||b.closure.rows===b.rows.length)&&canonical(finalizedReview(r,b.closure))===canonical(b.review),'TRAINING_PACKAGE_REVIEW');return{status:'VERIFIED_MOCK_REPLAY',sessionId:r.context.sessionId,sha256,review:b.review,authorityRestorable:false,sourceAuthenticated:false};
}
export function listRuns(root){root=guardRoot(root);const runs=[],issues=[],received=[];for(const n of fs.readdirSync(root).filter(n=>/^m[a-f0-9]{32}$/.test(n))){try{const p=makePackage(root,n);runs.push({sessionId:n,exerciseId:p.review.context.exerciseId,operatorId:p.review.context.operatorId,sourceKind:p.review.context.sourceKind,verdict:p.review.verdict,steps:p.review.observedSteps,sha256:p.sha256});}catch(e){issues.push({sessionId:n,error:e.message});}}for(const n of fs.readdirSync(root).filter(n=>/^received-[a-f0-9]{64}\.json$/.test(n))){try{const bytes=regular(path.join(root,n),16*2**20),id=n.slice(9,-5);need(hash(bytes)===id,'RECEIVED_SOURCE_HASH');const p=verifyPackage(bytes);received.push({archiveId:id,sessionId:p.sessionId,verdict:p.review.verdict,sha256:p.sha256});}catch(e){issues.push({file:n,error:e.message});}}return{runs,received,issues,authorityRestorable:false};}
export function createContext(input,hostBoot){return{sessionId:'m'+randomUUID().replaceAll('-',''),hostBoot,operatorId:input.operatorId,sourceClockId:input.sourceClockId,sourceKind:input.sourceKind,exerciseId:input.exerciseId,profileId:input.profileId};}

export function readReceived(root,id){need(/^[a-f0-9]{64}$/.test(id),'RECEIVED_ID');root=guardRoot(root);const bytes=regular(path.join(root,'received-'+id+'.json'),16*2**20);need(hash(bytes)===id,'RECEIVED_SOURCE_HASH');verifyPackage(bytes);return JSON.parse(bytes);}
