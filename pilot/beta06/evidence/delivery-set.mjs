/** Async immutable FIELD01 delivery folder; one accepted SITL raw archive + synthetic capture TARs.
 * Copies only explicitly selected files. Python performs independent readonly cross-check before return.
 */
import * as fs from 'node:fs/promises';
import { constants as C } from 'node:fs';
import { resolve,join,dirname,parse } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { randomUUID } from 'node:crypto';
import { jsonBytes,sha256,validId,validSha } from '../../field02/evidence/schema.mjs';
const run=promisify(execFile),HERE=dirname(fileURLToPath(import.meta.url)),ROOT=resolve(HERE,'../../..'),OWNED=join(ROOT,'evidence/beta06')+'/';
export const DELIVERY_LIMITS=Object.freeze({flightBytes:32*2**20,captureBytes:4*2**20,totalBytes:64*2**20,maxCaptures:16,indexBytes:131072});
async function directory(path){path=resolve(path);let current=parse(path).root;for(const part of path.slice(current.length).split('/').filter(Boolean)){
  current=join(current,part);const st=await fs.lstat(current);if(st.isSymbolicLink()||!st.isDirectory())throw Error('DELIVERY_DIRECTORY_TYPE_OR_SYMLINK');}return path;}
async function read(path,max){path=resolve(path);await directory(dirname(path));const h=await fs.open(path,C.O_RDONLY|C.O_NOFOLLOW);try{
  const st=await h.stat();if(!st.isFile()||st.size<1||st.size>max)throw Error('DELIVERY_INPUT_BOUND');const b=await h.readFile();
  if(b.length!==st.size||b.length>max)throw Error('DELIVERY_INPUT_CHANGED');return b;
}finally{await h.close();}}
async function write(path,b){const h=await fs.open(path,C.O_WRONLY|C.O_CREAT|C.O_EXCL|C.O_NOFOLLOW,0o444);try{await h.writeFile(b);await h.sync();}finally{await h.close();}}
async function dirsync(path){const h=await fs.open(path,C.O_RDONLY|C.O_NOFOLLOW);try{await h.sync();}finally{await h.close();}}

export async function exportDeliverySet({out,deliveryId=randomUUID(),flight,captureArchives,receiverId='field02-evaluator',senderId='aeris-field02-synthetic'}={}){
  if(typeof out!=='string'||!out.startsWith(OWNED)||resolve(out)!==out)throw Error('NEW_OWNED_DELIVERY_DIRECTORY_REQUIRED');
  if(![deliveryId,receiverId,senderId].every(validId)||!flight||!validSha(flight.manifestSha256)||!/^s[a-f0-9]{20}$/.test(flight.expectedRun??''))throw Error('DELIVERY_IDENTITY_OR_ACCEPTED_SITL_RUN');
  if(!Array.isArray(captureArchives)||captureArchives.length<1||captureArchives.length>DELIVERY_LIMITS.maxCaptures||new Set(captureArchives.map(p=>resolve(p))).size!==captureArchives.length)throw Error('DELIVERY_CAPTURE_COUNT_OR_DUPLICATE_PATH');
  await directory(dirname(out));
  const flightBytes=await read(flight.archive,DELIVERY_LIMITS.flightBytes),captures=[];let total=flightBytes.length;
  for(const archive of captureArchives){const bytes=await read(archive,DELIVERY_LIMITS.captureBytes);total+=bytes.length;if(total>DELIVERY_LIMITS.totalBytes-DELIVERY_LIMITS.indexBytes)throw Error('DELIVERY_TOTAL_BOUND');captures.push(bytes);}
  const index={schemaVersion:1,kind:'FIELD01_DELIVERY_SET',deliveryId,receiverId,senderId,sourceKind:'SYNTHETIC',actualImages:0,authorityRestorable:false,
    flight:{path:'flight.tar',sizeBytes:flightBytes.length,sha256:sha256(flightBytes),manifestSha256:flight.manifestSha256,receiverId:'FIELD01_FLIGHT_RECEIVER_V1',run:flight.expectedRun},
    captures:captures.map((b,i)=>({path:`capture-${String(i+1).padStart(2,'0')}.tar`,sizeBytes:b.length,sha256:sha256(b)}))};
  const ib=jsonBytes(index);if(ib.length>DELIVERY_LIMITS.indexBytes||total+ib.length>DELIVERY_LIMITS.totalBytes)throw Error('DELIVERY_TOTAL_BOUND');
  await fs.mkdir(out,{mode:0o700});await dirsync(dirname(out));
  // Partial/invalid candidate folders are retained; never overwrite or auto-delete evidence.
  await write(join(out,'flight.tar'),flightBytes);
  for(let i=0;i<captures.length;i++)await write(join(out,index.captures[i].path),captures[i]);
  await write(join(out,'index.json'),ib);await dirsync(out);
  const indexSha256=sha256(ib);
  const checked=await run('python3',['-B',join(ROOT,'pilot/field02/evidence/receive-set.py'),out,'--index-sha256',indexSha256,'--receiver',receiverId,'--sender',senderId,'--check-only'],
    {cwd:ROOT,timeout:60000,maxBuffer:131072});
  const receipt=JSON.parse(checked.stdout.trim());if(receipt.status!=='VALIDATED_NO_LEDGER_WRITE')throw Error('DELIVERY_READONLY_CHECK_FAILED');
  return{out,indexPath:join(out,'index.json'),indexSha256,totalBytes:total+ib.length,receipt,actualImages:0,authorityRestorable:false};
}

if(process.argv[1]===fileURLToPath(import.meta.url)){
  try{console.log(JSON.stringify(await exportDeliverySet(JSON.parse(process.argv[2]))));}
  catch(e){console.error(JSON.stringify({status:'REFUSED',error:e.message,receiver:e.stdout?.trim()??null,actualImages:0,authorityRestorable:false}));process.exitCode=1;}
}
