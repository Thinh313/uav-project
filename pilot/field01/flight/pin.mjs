import {aliases} from './isolated-loader.mjs';import fs from 'node:fs';import path from 'node:path';import {createHash} from 'node:crypto';
const root=process.cwd(),files={},seen=new Set();
function scan(n){n=aliases[n]??n;if(seen.has(n))return;seen.add(n);const q=path.join(root,n);const b=fs.readFileSync(q);files[n]=createHash('sha256').update(b).digest('hex');if(n.endsWith('.mjs'))for(const m of b.toString().matchAll(/(?:from|import)\s*\(?['"](\.[^'"]+)['"]/g))scan(path.normalize(path.join(path.dirname(n),m[1])));}
for(const n of ['pilot/field01/flight/flight01.mjs','pilot/field01/flight/isolated-loader.mjs','pilot/field01/flight/runtime.py','pilot/field01/flight/sitl.parm','pilot/field01/flight/pin.mjs','pilot/field01/flight/verify.mjs'])scan(n);
fs.writeFileSync('evidence/field01/flight/source-pins.json',JSON.stringify({format:'field01-flight-source-pins',aliases,files},null,2)+'\n');console.log(JSON.stringify({pinned:Object.keys(files).length}));
