import {mkdir,readdir,lstat,open,statfs,readFile} from 'node:fs/promises';
import path from 'node:path';
import {stable,sha} from './common.mjs';
import {replay,record,Workspace} from './workspace.mjs';
const FLOOR=20*2**30,RESERVE=16*2**20,CAP=16*2**20,MAX=2*2**20;
export class Store{
 constructor(root){this.root=path.resolve(root);this.records=[];this.bytes=0;this.error=null;this.w=new Workspace();}
 async admission(extra=0){const s=await statfs(path.dirname(this.root),{bigint:true}),free=Number(s.bavail*s.bsize);if(free-extra<FLOOR+RESERVE)throw Error('HOST_FLOOR_20GIB');if(this.bytes+extra>CAP||this.records.length>=64)throw Error('WORKSPACE_QUOTA_KEEP_EVIDENCE');return {freeBytes:free,bytes:this.bytes,capBytes:CAP,records:this.records.length,maxRecords:64};}
 async load(){
  await mkdir(this.root,{recursive:true});let p=this.root;while(p!==path.dirname(p)){const s=await lstat(p);if(!s.isDirectory()||s.isSymbolicLink())throw Error('STORE_PARENT_LINK');p=path.dirname(p)}
  const names=(await readdir(this.root)).sort(),records=[];this.bytes=0;
  for(let n=0;n<names.length;n++){const name=names[n];if(name!=='r-'+String(n+1).padStart(4,'0')+'.json')throw Error('UNKNOWN_OR_MISSING_JOURNAL_FILE');const p=path.join(this.root,name),s=await lstat(p);if(!s.isFile()||s.isSymbolicLink()||s.nlink!==1||s.size>MAX)throw Error('JOURNAL_FILE_TYPE_OR_SIZE');this.bytes+=s.size;if(this.bytes>CAP||n>=64)throw Error('WORKSPACE_QUOTA');records.push(JSON.parse(await readFile(p,'utf8')));}
  this.w=await replay(records);this.records=records;return this.w;
 }
 async append(event,{hook=async()=>{}}={}){
  if(this.error)throw Error('STORE_LATCHED_'+this.error);const disk=new Store(this.root);try{await disk.load();if(stable(disk.records)!==stable(this.records))throw Error('STORE_CHANGED_RELOAD')}catch(e){this.error=e.message;throw e}const candidate=await replay(this.records);await candidate.apply(event);const r=record(this.records,event,candidate),b=Buffer.from(stable(r)+'\n');if(b.length>MAX)throw Error('RECORD_SIZE');await this.admission(b.length);
  const filename=path.join(this.root,'r-'+String(r.sequence).padStart(4,'0')+'.json');let f;
  try{await hook('BEFORE_CREATE');f=await open(filename,'wx',0o600);await hook('AFTER_CREATE');await f.writeFile(b);await hook('AFTER_WRITE');await f.sync();await f.close();f=null;const dir=await open(this.root,'r');try{await dir.sync()}finally{await dir.close()}await hook('AFTER_SYNC');
   const read=await readFile(filename);if(sha(read.toString())!==sha(b.toString()))throw Error('WRITE_READBACK');this.records.push(r);this.w=candidate;this.bytes+=b.length;return r;
  }catch(e){this.error=e.message;throw e}finally{await f?.close()}
 }
}
