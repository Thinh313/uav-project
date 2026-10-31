import {readFile,readdir,writeFile,statfs} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
export async function sourceHashes(){const result={};for(const dir of ['pilot/apstream40','pilot/flightadapter39','pilot/apflight36','pilot/mavflight37','pilot/firmware38'])for(const n of await readdir(dir))if(n.endsWith('.mjs')){const p=dir+'/'+n;result[p]=createHash('sha256').update(await readFile(p)).digest('hex');}return result;}
export async function append(stem,obj){const s=await statfs('.');if(s.bavail*s.bsize<20*2**30+65536)throw Error('DISK_FLOOR');let n=1;while(existsSync(`evidence/apstream40/${stem}${n}.json`))n++;const path=`evidence/apstream40/${stem}${n}.json`;await writeFile(path,JSON.stringify(obj,null,2)+'\n',{flag:'wx'});return path;}
