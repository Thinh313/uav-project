import {spawn} from 'node:child_process';import {fileURLToPath} from 'node:url';
export async function acquireLock(file){
 const child=spawn('python3',[fileURLToPath(new URL('./lock-holder.py',import.meta.url)),file],{stdio:['pipe','pipe','pipe']});let alive=true,released=false,exited;
 const exit=new Promise(resolve=>{exited=resolve;});child.once('exit',()=>{alive=false;exited();});child.once('error',()=>{alive=false;exited();});
 try{const ready=await new Promise((resolve,reject)=>{let text='';const timer=setTimeout(()=>reject(Error('LOCK_START_TIMEOUT')),3000);child.once('error',e=>{clearTimeout(timer);reject(e);});child.stdout.on('data',b=>{text+=b.toString();if(text.length>1024){clearTimeout(timer);reject(Error('LOCK_REPLY_BOUND'));}if(text.includes('\n')){clearTimeout(timer);try{const v=JSON.parse(text.split('\n')[0]);if(!v.ready)reject(Error(v.error??'LOCK_REFUSED'));else resolve(v);}catch(e){reject(e);}}});child.once('exit',()=>{clearTimeout(timer);if(!text.includes('\n'))reject(Error('LOCK_EARLY_EXIT'));});});
  return {pid:ready.pid,get alive(){return alive&&!released;},async release(){if(!released){released=true;child.stdin.end();}await exit;},onLoss(callback){child.once('exit',()=>{if(!released)callback();});}};
 }catch(e){released=true;child.stdin.end();if(alive)child.kill('SIGTERM');await exit;throw e;}
}
