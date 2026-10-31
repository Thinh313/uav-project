import {Store} from './store.mjs';
const s=new Store(process.argv[2]),hookPoint=process.argv[3];await s.load();await s.append({type:'STEP',atMs:1000010,data:{kind:'ACK_ONLY'}},{hook:async name=>{if(name===hookPoint){console.log('HOOK '+name);setInterval(()=>{},1000);await new Promise(()=>{})}}});
