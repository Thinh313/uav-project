import {readFile,writeFile,mkdir,copyFile,readdir} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {validateCapsule44} from './assets/workflow/capsule.mjs';
import {journal82} from './server.mjs';
const E='evidence/cockpit82';const cases=[];
for(const n of ['android-draft-saved01','android-restart-readonly01','android-cold-root02','android-swangle-ready03']){
 const raw=await readFile(E+'/'+n+'-capsule.json','utf8'),c=await validateCapsule44(raw);assert.equal(c.authorityRestorable,false);assert.equal(c.journey.draft.form.altitude,'31');assert.equal(c.journey.draft.form.speed,'1.1');cases.push({name:n,pass:true,scope:'Actual Android journal independently semantic replayed; no current-flight claim'});
}
const a=JSON.parse(await readFile(E+'/android-draft-saved01.json','utf8'));for(const n of ['android-restart-readonly01','android-cold-root02','android-swangle-ready03'])assert.equal(JSON.parse(await readFile(E+'/'+n+'.json','utf8')).head,a.head);
cases.push({name:'Android restart/coldboot exact HEAD and31/1.1 persisted; authorityRestorable=false',pass:true});
const host=await journal82('load','.local/cockpit82/preview');assert(host.ok&&!host.pending&&host.revision===12);const c=await validateCapsule44(Buffer.from(host.bodyBase64,'base64').toString());assert.equal(c.journey.current.phase,'COMPLETED_MOCK');assert.equal(c.journey.current.cursor,2);assert.equal(c.authorityRestorable,false);assert(c.journey.current.events.some(x=>x.body.kind==='ACK_NOT_EXECUTION'));
await writeFile(E+'/host-final-capsule.json',Buffer.from(host.bodyBase64,'base64'));await writeFile(E+'/host-final-load.json',JSON.stringify(host,null,2)+'\n');await mkdir(E+'/host-journal-snapshot');for(const n of await readdir('.local/cockpit82/preview'))if(n==='HEAD'||n.endsWith('.bin'))await copyFile('.local/cockpit82/preview/'+n,E+'/host-journal-snapshot/'+n);
cases.push({name:'Browser UI complete mock with2observed points and ACK_NOT_EXECUTION, Java journal semantic replay, r12/no pending',pass:true});
await writeFile(E+'/final-semantic-qa.json',JSON.stringify({pass:cases.length,fail:0,cases,limitations:'Android full preflight/Fly/review not completed in this task; emulator diagnostics retained'},null,2)+'\n');console.log(JSON.stringify({pass:cases.length,fail:0}));
