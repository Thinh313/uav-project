/** Single-process, async fsync-before-return FIELD01 journal. No authority restoration.
 * Root and parent directories must be controlled by the operator (Node has no openat).
 * Static symlinks are refused; O_NOFOLLOW protects all file opens. Never deletes pending data.
 */
import * as fs from 'node:fs/promises';
import { constants as C } from 'node:fs';
import { resolve, join, parse } from 'node:path';
import { randomUUID } from 'node:crypto';
import { canonicalize, jsonBytes, sha256, validId, exact, fail, inspectJpeg, validateSidecar, validateLink, makeTar } from './schema.mjs';
const ZERO='0'.repeat(64);
export const DEFAULT_LIMITS=Object.freeze({maxBytes:128*1024*1024,maxCaptures:16,maxRecords:2048,maxHandoffs:16,maxImageBytes:4*1024*1024,maxJsonBytes:131072});
const copy = v => JSON.parse(canonicalize(v));

async function guardedDirectory(path, create=false) {
  const absolute=resolve(path), base=parse(absolute).root;
  let current=base;
  for (const part of absolute.slice(base.length).split('/').filter(Boolean)) {
    current=join(current,part);
    let stat;
    try { stat=await fs.lstat(current); }
    catch(e) { if(e.code!=='ENOENT'||!create) throw e; await fs.mkdir(current,{mode:0o700}); stat=await fs.lstat(current); }
    if(!stat.isDirectory()||stat.isSymbolicLink()) fail('DIRECTORY_SYMLINK_OR_TYPE');
  }
  return absolute;
}
async function readBounded(path,limit) {
  await guardedDirectory(resolve(path,'..'));
  const h=await fs.open(path,C.O_RDONLY|C.O_NOFOLLOW);
  try { const st=await h.stat(); if(!st.isFile()||st.size>limit) fail('FILE_TYPE_OR_LIMIT');
    const bytes=await h.readFile(); if(bytes.length!==st.size||bytes.length>limit) fail('FILE_CHANGED_OR_LIMIT'); return bytes;
  } finally { await h.close(); }
}
async function diskUsage(root, maxEntries=4096) {
  let total=0, count=0;
  async function walk(dir) {
    await guardedDirectory(dir);
    for(const entry of await fs.readdir(dir,{withFileTypes:true})) {
      if(++count>maxEntries) fail('STORE_ENTRY_LIMIT');
      const path=join(dir,entry.name), st=await fs.lstat(path);
      if(st.isSymbolicLink()) fail('STORE_SYMLINK');
      if(st.isDirectory()) await walk(path); else if(st.isFile()) total+=st.size; else fail('STORE_FILE_TYPE');
    }
  }
  await walk(root); return total;
}

export async function Store01({root,limits={},hooks={}}={}) {
  if(typeof root!=='string'||!root) fail('ROOT_REQUIRED');
  const lim={...DEFAULT_LIMITS,...limits};
  for(const key of Object.keys(lim)) if(!Object.hasOwn(DEFAULT_LIMITS,key)||!Number.isSafeInteger(lim[key])||lim[key]<1||lim[key]>DEFAULT_LIMITS[key]) fail('LIMITS_CANNOT_RELAX');
  root=await guardedDirectory(root,true);
  let readOnly=false, poisoned=false, issue=null, closed=false, bytes=0, records=[], head=ZERO, tail=Promise.resolve();
  let lockHandle=null, lockIdentity=null, walHandle=null;
  const captures=new Map(), transfers=new Map(), lockPath=join(root,'writer.lock'), walPath=join(root,'journal.jsonl');
  const nonce=randomUUID();
  const tick=async stage => { if(hooks.at) await hooks.at(stage); };
  const sync=async (handle,stage) => { await tick(stage); await handle.sync(); };
  const syncDir=async (dir,stage) => { await guardedDirectory(dir); const h=await fs.open(dir,C.O_RDONLY|C.O_NOFOLLOW); try{await sync(h,stage);}finally{await h.close();} };
  async function immutable(path,data,stage) {
    await guardedDirectory(resolve(path,'..'));
    const h=await fs.open(path,C.O_WRONLY|C.O_CREAT|C.O_EXCL|C.O_NOFOLLOW,0o400);
    try{await h.writeFile(data); bytes+=data.length; await sync(h,stage);}finally{await h.close();}
  }
  try {
    lockHandle=await fs.open(lockPath,C.O_WRONLY|C.O_CREAT|C.O_EXCL|C.O_NOFOLLOW,0o600);
    lockIdentity=await lockHandle.stat();
    const lock=jsonBytes({schemaVersion:1,pid:process.pid,nonce,authority:'NONE'});
    await lockHandle.writeFile(lock); await sync(lockHandle,'lock.fsync'); await syncDir(root,'lock.directory.fsync');
  } catch(e) {
    if(e.code==='EEXIST'||e.code==='ELOOP') {readOnly=true;issue='WRITER_LOCK_PRESENT_MANUAL_RECOVERY_REQUIRED';}
    else {readOnly=true;poisoned=true;issue=`LOCK_UNCERTAIN:${e.message}`;}
  }
  try {
    bytes=await diskUsage(root);
    if(bytes>lim.maxBytes) fail('STORE_QUOTA');
    let raw;
    try{raw=await readBounded(walPath,lim.maxBytes);}catch(e){if(e.code!=='ENOENT')throw e;raw=Buffer.alloc(0);}
    if(raw.length && raw[raw.length-1]!==10) fail('JOURNAL_TORN_TAIL');
    for(const line of raw.toString('utf8').split('\n').filter(Boolean)) {
      if(records.length>=lim.maxRecords||Buffer.byteLength(line)>lim.maxJsonBytes+2048) fail('JOURNAL_LIMIT');
      const rec=JSON.parse(line), {hash,...base}=rec;
      if(!exact(rec,['schemaVersion','seq','previousHash','kind','data','hash']) || rec.schemaVersion!==1 ||
          rec.seq!==records.length+1 || rec.previousHash!==head || hash!==sha256(jsonBytes(base)) || canonicalize(rec)!==line) fail('JOURNAL_CHAIN');
      records.push(rec);head=hash;
      if(rec.kind==='CAPTURE_INTENT') {if(captures.has(rec.data.captureId))fail('JOURNAL_CAPTURE_DUPLICATE');captures.set(rec.data.captureId,{state:'PENDING',intent:rec});}
      if(rec.kind==='CAPTURE_COMMITTED') {const v=captures.get(rec.data.captureId);if(!v||v.state!=='PENDING')fail('JOURNAL_CAPTURE_ORDER');v.state='COMMITTED';v.result=rec;}
      if(rec.kind==='HANDOFF_INTENT') {if(transfers.has(rec.data.transferId))fail('JOURNAL_TRANSFER_DUPLICATE');transfers.set(rec.data.transferId,{state:'PENDING',intent:rec});}
      if(rec.kind==='HANDOFF_COMMITTED') {const v=transfers.get(rec.data.transferId);if(!v||v.state!=='PENDING')fail('JOURNAL_TRANSFER_ORDER');v.state='COMMITTED';v.result=rec;}
    }
    if(captures.size>lim.maxCaptures||transfers.size>lim.maxHandoffs) fail('STORE_OBJECT_LIMIT');
    if(!readOnly) {
      walHandle=await fs.open(walPath,C.O_WRONLY|C.O_CREAT|C.O_APPEND|C.O_NOFOLLOW,0o600);
      await sync(walHandle,'journal.open.fsync'); await syncDir(root,'journal.directory.fsync');
      await guardedDirectory(join(root,'captures'),true); await guardedDirectory(join(root,'handoffs'),true);
      await syncDir(root,'layout.directory.fsync');
    }
  }catch(e){readOnly=true;poisoned=true;issue=`STORE_OBSERVATION_ONLY:${e.message}`;}

  function writable(){if(closed)fail('STORE_CLOSED');if(readOnly||poisoned)fail(issue||'STORE_READ_ONLY');}
  function quota(extra,slots=1){if(bytes+extra>lim.maxBytes)fail('STORE_QUOTA');if(records.length+slots>lim.maxRecords)fail('RECORD_QUOTA');}
  function enqueue(fn){const result=tail.then(fn);tail=result.catch(()=>{});return result;}
  async function record(kind,data,expectedHead) {
    writable(); if(expectedHead!==undefined&&expectedHead!==head)fail('STALE_EXPECTED_HEAD');
    const base={schemaVersion:1,seq:records.length+1,previousHash:head,kind,data};
    const result={...base,hash:sha256(jsonBytes(base))}, serialized=Buffer.from(canonicalize(result)+'\n');
    quota(serialized.length);
    try {await tick('journal.before.write');await walHandle.writeFile(serialized);bytes+=serialized.length;await sync(walHandle,'journal.fsync');}
    catch(e){poisoned=true;issue=`JOURNAL_WRITE_UNCERTAIN:${e.message}`;throw new Error(issue);}
    records.push(result);head=result.hash;return copy(result);
  }
  function append(kind,data,{expectedHead}={}) {
    if(typeof kind!=='string'||!/^[A-Z][A-Z0-9_]{0,63}$/.test(kind)||/^(CAPTURE|HANDOFF)_/.test(kind)) return Promise.reject(new Error('RECORD_KIND'));
    let cloned;try{cloned=copy(data);if(jsonBytes(cloned).length>lim.maxJsonBytes)fail('JSON_SIZE');}catch(e){return Promise.reject(e);}
    return enqueue(()=>record(kind,cloned,expectedHead));
  }
  async function readInternal(id) {
    if(!validId(id))fail('CAPTURE_ID');const entry=captures.get(id);if(!entry||entry.state!=='COMMITTED')fail('CAPTURE_NOT_COMMITTED');
    const dir=join(root,'captures',id), originalBytes=await readBounded(join(dir,'original.jpg'),lim.maxImageBytes);
    const sidecarBytes=await readBounded(join(dir,'sidecar.json'),lim.maxJsonBytes), manifestBytes=await readBounded(join(dir,'manifest.json'),lim.maxJsonBytes);
    const manifest=JSON.parse(manifestBytes.toString('utf8')), sidecar=JSON.parse(sidecarBytes.toString('utf8'));
    const receipt=entry.result.data;
    if(sha256(originalBytes)!==receipt.originalSha256||sha256(sidecarBytes)!==receipt.sidecarSha256||sha256(manifestBytes)!==receipt.manifestSha256||
        !manifestBytes.equals(jsonBytes(manifest))||!sidecarBytes.equals(jsonBytes(sidecar))||!inspectJpeg(originalBytes))fail('CAPTURE_FILE_INTEGRITY');
    validateSidecar(sidecar,id,originalBytes);validateLink(manifest.link,sidecar);
    if(manifest.captureId!==id||manifest.originalSha256!==receipt.originalSha256||manifest.sidecarSha256!==receipt.sidecarSha256)fail('CAPTURE_MANIFEST_BINDING');
    return {originalBytes,sidecar,manifest,receipt:{...copy(receipt),wal:{seq:entry.result.seq,hash:entry.result.hash}}};
  }
  function commit(captureId,{originalBytes,sidecar,link,guard}={}) {
    let original,s,l,sb;
    try {if(!validId(captureId)||!(originalBytes instanceof Uint8Array)||originalBytes.length>lim.maxImageBytes)fail('CAPTURE_INPUT');
      original=Buffer.from(originalBytes);s=copy(sidecar);l=copy(link);sb=jsonBytes(s);if(!inspectJpeg(original))fail('ORIGINAL_JPEG_STRUCTURE');
      validateSidecar(s,captureId,original);validateLink(l,s);
    }catch(e){return Promise.reject(e);}
    return enqueue(async()=>{
      writable();if(guard!==undefined&&typeof guard!=='function')fail('GUARD_TYPE');guard?.();
      if(captures.has(captureId))fail('CAPTURE_REPLAY');if(captures.size>=lim.maxCaptures)fail('CAPTURE_QUOTA');
      const manifest={schemaVersion:1,kind:'FIELD01_LOCAL_CAPTURE',captureId,frameId:s.frameId,context:s.context,link:l,
        originalSha256:sha256(original),sidecarSha256:sha256(sb),actualImages:0,authenticity:'NOT_ATTESTED'};
      const mb=jsonBytes(manifest);quota(original.length+sb.length+mb.length+8192,2);
      const intent=await record('CAPTURE_INTENT',{captureId,frameId:s.frameId,context:s.context,link:l},undefined);
      captures.set(captureId,{state:'PENDING',intent});
      try {
        const dir=join(root,'captures',captureId);await fs.mkdir(dir,{mode:0o700});await syncDir(join(root,'captures'),'capture.parent.fsync');
        await immutable(join(dir,'original.jpg'),original,'capture.original.fsync');
        await immutable(join(dir,'sidecar.json'),sb,'capture.sidecar.fsync');
        await immutable(join(dir,'manifest.json'),mb,'capture.manifest.fsync');await syncDir(dir,'capture.directory.fsync');
        guard?.();
        const receipt={status:'COMMITTED',captureId,originalSha256:sha256(original),sidecarSha256:sha256(sb),manifestSha256:sha256(mb),
          actualImages:0,authenticity:'NOT_ATTESTED',authority:'NONE'};
        const rec=await record('CAPTURE_COMMITTED',receipt);captures.get(captureId).state='COMMITTED';captures.get(captureId).result=rec;
        return {...copy(receipt),wal:{seq:rec.seq,hash:rec.hash}};
      }catch(e){poisoned=true;issue=`CAPTURE_PENDING_UNCERTAIN:${e.message}`;throw new Error(issue);}
    });
  }
  function handoff(captureId,{transferId,senderId,receiverId}={}) {
    if(![captureId,transferId,senderId,receiverId].every(validId))return Promise.reject(new Error('HANDOFF_IDENTITY'));
    return enqueue(async()=>{
      writable();if(transfers.has(transferId))fail('TRANSFER_REPLAY');if(transfers.size>=lim.maxHandoffs)fail('HANDOFF_QUOTA');
      const capture=await readInternal(captureId), sidecarBytes=jsonBytes(capture.sidecar);
      const base={schemaVersion:1,kind:'FIELD01_SYNTHETIC_HANDOFF',sourceKind:'SYNTHETIC',actualImages:0,
        transferId,senderId,receiverId,captureId,frameId:capture.sidecar.frameId,context:capture.sidecar.context,link:capture.manifest.link,
        files:[{path:'original.jpg',sizeBytes:capture.originalBytes.length,sha256:sha256(capture.originalBytes)},
          {path:'sidecar.json',sizeBytes:sidecarBytes.length,sha256:sha256(sidecarBytes)}]};
      const manifest={...base,packageId:sha256(jsonBytes(base))};
      const tar=makeTar([['original.jpg',capture.originalBytes],['sidecar.json',sidecarBytes],['manifest.json',jsonBytes(manifest)]]);
      quota(tar.length+8192,2);
      const intent=await record('HANDOFF_INTENT',{transferId,captureId,packageId:manifest.packageId});transfers.set(transferId,{state:'PENDING',intent});
      try {
        await immutable(join(root,'handoffs',`${transferId}.tar`),tar,'handoff.file.fsync');await syncDir(join(root,'handoffs'),'handoff.directory.fsync');
        const receipt={status:'EXPORTED',transferId,captureId,receiverId,packageId:manifest.packageId,tarSha256:sha256(tar),
          actualImages:0,authenticity:'NOT_ATTESTED',authority:'NONE'};
        const rec=await record('HANDOFF_COMMITTED',receipt);transfers.get(transferId).state='COMMITTED';transfers.get(transferId).result=rec;
        return {bytes:tar,manifest,receipt:{...receipt,wal:{seq:rec.seq,hash:rec.hash}}};
      }catch(e){poisoned=true;issue=`HANDOFF_PENDING_UNCERTAIN:${e.message}`;throw new Error(issue);}
    });
  }
  function snapshot(){return {root,readOnly,poisoned,closed,issue,head,recordCount:records.length,bytes,
    captures:[...captures].map(([captureId,v])=>({captureId,state:v.state,frameId:v.intent.data.frameId,context:copy(v.intent.data.context)})),
    handoffs:[...transfers].map(([transferId,v])=>({transferId,state:v.state})),actualImages:0,authority:'NONE'};}
  async function review(){await tail;const rows=[];for(const [captureId,v]of captures){if(v.state==='PENDING'){rows.push({captureId,state:'PENDING',actualImages:0});continue;}
    try{const p=await readInternal(captureId);rows.push({captureId,state:'COMMITTED',sidecar:p.sidecar,receipt:p.receipt});}
    catch(e){rows.push({captureId,state:'QUARANTINE',reason:e.message,actualImages:0});}}
    return {snapshot:snapshot(),rows,actualImages:0,authority:'NONE'};}
  async function close(){await tail;if(closed)return;closed=true;await walHandle?.close();await lockHandle?.close();
    if(lockIdentity){const st=await fs.lstat(lockPath).catch(()=>null);if(st&&!st.isSymbolicLink()&&st.dev===lockIdentity.dev&&st.ino===lockIdentity.ino){
      const lock=JSON.parse((await readBounded(lockPath,4096)).toString('utf8'));if(lock.nonce===nonce){await fs.unlink(lockPath);await syncDir(root,'close.directory.fsync');}}}}
  return {append,commit,handoff,read:async id=>{await tail;return readInternal(id);},review,snapshot,records:()=>copy(records),close};
}
