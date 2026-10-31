import {statfsSync,statSync,readdirSync} from 'node:fs';
import {writeFile} from 'node:fs/promises';
import path from 'node:path';
export const FLOOR=20*1024**3,BUDGET=16*1024**2;
export function allocated(dir){let n=0;for(const entry of readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,entry.name);if(entry.isDirectory())n+=allocated(p);else if(entry.isFile())n+=statSync(p).blocks*512;else throw Error('NAMESPACE_SPECIAL_FILE');}return n;}
export function admission(bytes=0){const s=statfsSync('.',{bigint:true}),free=Number(s.bavail*s.bsize),used=allocated('pilot/heramcu45')+allocated('evidence/heramcu45');if(free-bytes<FLOOR+1024**2)throw Error('HOST_20GIB_FLOOR_RESERVE');if(used+bytes+8192>BUDGET)throw Error('HERAMCU45_16MIB_BUDGET');return {freeBytes:free,allocatedBytes:used,floorBytes:FLOOR,budgetBytes:BUDGET};}
export async function receipt(name,value,{compact=false}={}){const text=JSON.stringify(value,null,compact?0:2)+'\n';admission(Buffer.byteLength(text));await writeFile('evidence/heramcu45/'+name,text,{flag:'wx'});}
