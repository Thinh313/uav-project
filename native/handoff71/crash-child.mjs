import {readFile} from 'node:fs/promises';import {HandoffManager} from './manager.mjs';
const [configFile,point]=process.argv.slice(2),config=JSON.parse(await readFile(configFile)),m=await HandoffManager.open(config);
const stop=async p=>{if(p===point){console.log(JSON.stringify({pid:process.pid,lockPid:m.lock.pid,archiveLockPid:m.archive.lock.pid,point,jobs:[...m.ledger.jobs.keys()]}));await new Promise(()=>{});}};
if(point==='ARCHIVE69_IMPORT_FILE')m.archive.fault=p=>stop(p==='IMPORT_FILE'?'ARCHIVE69_IMPORT_FILE':p);else m.fault=stop;
if(config.job)await m.receive(config.job);else await m.start(config.generation);throw Error('BOUNDARY_NOT_REACHED');
