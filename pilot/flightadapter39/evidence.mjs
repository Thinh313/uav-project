import {readFile,readdir,writeFile,statfs} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
export async function sourceHashes(){const result={};for(const dir of ['pilot/flightadapter39','pilot/apflight36','pilot/mavflight37','pilot/firmware38'])for(const f of await readdir(dir))if(f.endsWith('.mjs')){const p=dir+'/'+f;result[p]=createHash('sha256').update(await readFile(p)).digest('hex');}return result;}
export async function append(stem,data){const s=await statfs('.');if(s.bavail*s.bsize<20*2**30+65536)throw Error('DISK_FLOOR');let n=1;
 while(existsSync(`evidence/flightadapter39/${stem}${n}.json`))n++;
 const path=`evidence/flightadapter39/${stem}${n}.json`;await writeFile(path,JSON.stringify(data,null,2)+'\n',{flag:'wx'});return path;}
