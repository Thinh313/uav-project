import {writeFile} from 'node:fs/promises';
import {Store50} from './manager.mjs';
const [root,boundary,marker]=process.argv.slice(2),s=new Store50(root),a=await s.sample(),b=await s.sample(),pick=await s.choosePlan(a.workspaceId);await s.choose(pick,{planSha256:pick.sha256,acknowledge:'INTERRUPT_OLD_SESSION_NO_REPLAY'});const e=await s.exportUnit('GROUP',b.groupId);
async function pause(k){if(k===boundary){await writeFile(marker,JSON.stringify({pid:process.pid,boundary,groupId:b.groupId,exportId:e.exportId,packSha256:e.packSha256}),{flag:'wx'});await new Promise(r=>setTimeout(r,45000));}}
if(boundary==='IMPORT_CHUNK_WRITTEN')await s.importLocal(e.exportId,e.packSha256,{hook:pause});else{const i=await s.importLocal(e.exportId,e.packSha256),p=await s.cleanupPlan(e.exportId,i.importId);await s.cleanup(p,{planSha256:p.sha256,typedUnitId:b.groupId,acknowledge:'KEEP_ARCHIVES_REMOVE_ONLY_HOT_REPLICA'},{hook:pause});}
