import {open,lstat,realpath,mkdir,readdir,statfs} from 'node:fs/promises';
import {constants} from 'node:fs';
import path from 'node:path';
import {createHash,randomBytes} from 'node:crypto';
import {canonical,exact} from '../cockpit66/portable/cyber65/contracts.mjs';
export {canonical,exact};
export const hash=b=>createHash('sha256').update(b).digest('hex');
export const bytes=x=>Buffer.from(canonical(x));
export const digest=x=>hash(bytes(x));
export const id=prefix=>prefix+'-'+randomBytes(16).toString('hex');
export const fail=s=>{throw Error(s);};
export const LIMIT={floor:20*1024**3,margin:32*1024**2,store:16*1024**2,package:24*1024**2,workspace:32*1024**2,audit:512*1024,record:32768,entries:34};
export async function directory(p){const st=await lstat(p);if(!st.isDirectory()||st.isSymbolicLink()||await realpath(p)!==path.resolve(p))fail('DIRECTORY_ALIAS');}
export async function syncDir(p){const f=await open(p,'r');try{await f.sync();}finally{await f.close();}}
export async function createDir(p){await mkdir(p);await syncDir(p);await syncDir(path.dirname(p));}
export async function read(p,max=LIMIT.package){const s=await lstat(p);if(!s.isFile()||s.isSymbolicLink()||s.nlink!==1||s.size>max)fail('BOUNDED_SINGLE_REGULAR_FILE');const f=await open(p,constants.O_RDONLY|constants.O_NOFOLLOW);try{const s2=await f.stat();if(s2.ino!==s.ino||s2.dev!==s.dev||s2.nlink!==1)fail('FILE_RACE');const b=await f.readFile();if(b.length>max)fail('READ_BOUND');return b;}finally{await f.close();}}
export async function write(p,b){const f=await open(p,constants.O_CREAT|constants.O_EXCL|constants.O_WRONLY|constants.O_NOFOLLOW,0o600);try{let at=0;while(at<b.length){const r=await f.write(b,at,b.length-at,null);if(!r.bytesWritten)fail('ZERO_WRITE');at+=r.bytesWritten;}await f.sync();}finally{await f.close();}await syncDir(path.dirname(p));}
export async function readJSON(p,max=LIMIT.record){const b=await read(p,max),v=JSON.parse(new TextDecoder('utf8',{fatal:true}).decode(b));if(!bytes(v).equals(b))fail('NONCANONICAL_JSON');return v;}
export async function treeBytes(p){await directory(p);let n=0;for(const e of await readdir(p,{withFileTypes:true})){const f=path.join(p,e.name),s=await lstat(f);if(s.isSymbolicLink())fail('TREE_SYMLINK');if(s.isDirectory())n+=await treeBytes(f);else{if(!s.isFile()||s.nlink!==1)fail('TREE_INODE');n+=s.size;}}return n;}
export async function disk(p,required=0,available){const st=await statfs(p,{bigint:true}),free=available??Number(st.bavail*st.bsize);if(free<LIMIT.floor+LIMIT.margin+required)fail('DISK_FLOOR_OR_RESERVE');return free;}
export function permittedRoot(p){const x=path.resolve(p),base=path.resolve('.');if(![path.join(base,'.local/archive69')+path.sep,path.join(base,'evidence/archive69')+path.sep].some(a=>x.startsWith(a)))fail('ISOLATED_WORKSPACE_REQUIRED');return x;}
