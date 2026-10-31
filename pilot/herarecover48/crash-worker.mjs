// Test-only owned child: parent kills this exact PID after a durable boundary.
import {readFile,writeFile} from 'node:fs/promises';
import {stage} from './store.mjs';
import {inspect,plan} from './recovery.mjs';
const [root,boundary,marker]=process.argv.slice(2),b=JSON.parse(await readFile('evidence/herarecover48/pending-source-bundle3.json','utf8')),p=plan(b,inspect(b).pending,b.sha256);
await stage(root,b,p,{planSha256:p.sha256,acknowledge:'RETAIN_ALL_NO_PENDING_EXECUTION',hook:async k=>{if(k===boundary){await writeFile(marker,JSON.stringify({pid:process.pid,boundary}),{flag:'wx'});await new Promise(r=>setTimeout(r,45000));}}});
