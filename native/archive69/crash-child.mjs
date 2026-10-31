import {ArchiveManager} from './manager.mjs';import {readFile} from 'node:fs/promises';
const [dir,configFile,point]=process.argv.slice(2),config=JSON.parse(await readFile(configFile)),m=await ArchiveManager.open({dir,fault:async p=>{if(p===point){console.log(JSON.stringify({pid:process.pid,lockPid:m.lock.pid,point}));await new Promise(()=>{});}}});
if(point.startsWith('IMPORT'))await m.import(config.exportId);else{const p=await m.plan(config.generation,config.exportId,config.importId);await m.cleanup(p.planSha256,p.phrase);}throw Error('CRASH_BOUNDARY_NOT_REACHED');
