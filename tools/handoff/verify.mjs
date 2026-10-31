import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'handoff/SOURCE-MANIFEST.json')));
let checked=0;
for(const row of manifest.files){
 const p=path.resolve(root,row.path);
 if(!p.startsWith(root+path.sep))throw Error('PATH_OUTSIDE_REPO');
 const stat=fs.lstatSync(p);
 const raw=stat.isSymbolicLink()?Buffer.from(fs.readlinkSync(p)):fs.readFileSync(p);
 if(stat.isSymbolicLink()&&!fs.realpathSync(p).startsWith(root+path.sep))throw Error('LINK_OUTSIDE_REPO');
 if(crypto.createHash('sha256').update(raw).digest('hex')!==row.sha256)throw Error('SHA256_MISMATCH:'+row.path);
 checked++;
}
console.log(JSON.stringify({status:'PASS_SOURCE_BYTES_ONLY',checked,base:manifest.privateSourceCommit,scope:'Not an APK, runtime, hardware or flight acceptance'},null,2));
