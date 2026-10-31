import {readdir} from 'node:fs/promises';import path from 'node:path';
import {read,write,bytes,hash,digest,exact,fail,LIMIT} from '../archive69/io.mjs';
export const GEN=/^g-[a-f0-9]{32}$/,OP=/^op-[a-f0-9]{32}$/;
export async function loadControl(dir){
 const events=[],begins=new Map(),pending=new Map(),frozen=new Map(),stages=new Map(),selections=[];let head='ROOT',seq=0,size=0,selected=null;
 for(const name of (await readdir(dir)).sort()){
  const raw=await read(path.join(dir,name),LIMIT.record);size+=raw.length;if(size>LIMIT.audit)fail('CONTROL_QUOTA');const r=JSON.parse(new TextDecoder('utf8',{fatal:true}).decode(raw));exact(r,['format','seq','previous','type','op','body']);if(!bytes(r).equals(raw)||r.format!=='rotate70-control/1'||r.seq!==++seq||r.previous!==head||name!==String(seq).padStart(8,'0')+'-'+hash(raw)+'.json'||!OP.test(r.op))fail('CONTROL_CHAIN_SCHEMA');
  if(r.type==='BEGIN'){
   exact(r.body,['kind','from','newGeneration','basis','parentSelectionSha256','sourceSha256','planSha256','supersedes']);const b=r.body;if(!['INIT','ROTATE','ROLLBACK'].includes(b.kind)||!GEN.test(b.newGeneration)||b.from!==null&&!GEN.test(b.from)||b.basis!==null&&!GEN.test(b.basis)||begins.has(r.op)||[...begins.values()].some(e=>e.body.newGeneration===b.newGeneration)||b.from!==(selected?.body.to??null)||b.parentSelectionSha256!==(selected?.hash??'ROOT')||!Array.isArray(b.supersedes))fail('BEGIN_BINDING');
   if(b.kind==='INIT'&&(selected||begins.size||b.from!==null||b.basis!==null)||b.kind==='ROTATE'&&(!selected||pending.size||b.basis!==b.from)||b.kind==='ROLLBACK'&&(!selected||!b.basis))fail('OPERATION_ORDER');
   if(new Set(b.supersedes).size!==b.supersedes.length||b.supersedes.some(op=>!pending.has(op)))fail('SUPERSEDE_UNKNOWN');
   if(b.kind!=='ROLLBACK'&&b.supersedes.length)fail('SUPERSEDE_KIND');begins.set(r.op,r);pending.set(r.op,r);
  }else{
   const begin=pending.get(r.op);if(!begin)fail('CONTROL_OPERATION_NOT_PENDING');const b=begin.body;
   if(r.type==='FREEZE'){
    exact(r.body,['generation','manifest','inspection','closure']);if(r.body.generation!==b.from||frozen.has(r.body.generation)||!['CLEAN_CLOSED','VERIFIED_PREFIX_UNCERTAIN'].includes(r.body.closure))fail('FREEZE_BINDING');frozen.set(r.body.generation,{...r,hash:hash(raw)});
   }else if(r.type==='STAGE'){
    exact(r.body,['generation','manifest','inspection','basis','seedRun']);if(r.body.generation!==b.newGeneration||r.body.basis!==b.basis||stages.has(r.op))fail('STAGE_BINDING');stages.set(r.op,{...r,hash:hash(raw)});
   }else if(r.type==='SELECT'){
    exact(r.body,['kind','from','to','basis','stageSha256','parentSelectionSha256','supersedes']);const s=r.body;
    if(s.kind!==b.kind||s.from!==b.from||s.to!==b.newGeneration||s.basis!==b.basis||s.parentSelectionSha256!==(selected?.hash??'ROOT')||s.stageSha256!==stages.get(r.op)?.hash||digest(s.supersedes)!==digest(b.supersedes)||b.from!==null&&!frozen.has(b.from)||b.basis!==null&&!frozen.has(b.basis))fail('SELECT_BINDING');
    pending.delete(r.op);for(const op of b.supersedes)pending.delete(op);selected={...r,hash:hash(raw)};selections.push(selected);
   }else fail('CONTROL_UNKNOWN_TYPE');
  }
  head=hash(raw);events.push(r);
 }
 return {events,begins,pending,frozen,stages,selections,selected,head,seq,size};
}
export async function appendControl(dir,control,type,op,body){const r={format:'rotate70-control/1',seq:control.seq+1,previous:control.head,type,op,body},raw=bytes(r);if(raw.length>LIMIT.record||control.size+raw.length>LIMIT.audit)fail('CONTROL_QUOTA');await write(path.join(dir,String(r.seq).padStart(8,'0')+'-'+hash(raw)+'.json'),raw);return {...r,hash:hash(raw)};}
