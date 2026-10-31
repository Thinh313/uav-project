import {readFile} from 'node:fs/promises';import {MockAnchor,Ledger} from './ledger.mjs';
const c=JSON.parse(await readFile(process.env.A73_WORKER_CONFIG)),anchor=await MockAnchor.open({dir:c.anchorDir}),ledger=await Ledger.open({dir:c.ledgerDir,role:'receiver',policy:c.policy,anchor,fault:async phase=>{if(phase===c.killAt)process.kill(process.pid,'SIGKILL');}});
try{await ledger.append('ADMIT',c.admission,c.atMs);}finally{await ledger.close();await anchor.close();}
