import {spawn} from 'node:child_process';import {readFile,writeFile,mkdir,rm,readdir,copyFile} from 'node:fs/promises';
import path from 'node:path';import {journal} from './server.mjs';import {draftBody,defaultForm} from './editor.mjs';import {validateCapsule} from './capsule.mjs';import {PINS} from './pins.mjs';
const E=path.resolve('evidence/airspace35');let attempt=1;for(;;attempt++){try{await readFile(E+'/crash'+attempt+'.json')}catch{break}}
const root=path.resolve('native/flightops35/.crash-qa-'+attempt),evidence=E+'/crash'+attempt;await mkdir(root);await mkdir(evidence);
const checks=[],children=[];let owned=null;const check=(name,v)=>{checks.push({name,pass:!!v});if(!v)throw Error(name)};
const capsule=async name=>JSON.stringify({format:'aeris-native35-workspace',version:1,operational:false,authorityRestorable:false,journey:{format:'aeris-native33-workspace',version:1,sourceId:PINS.coreSourceId,operational:false,authorityRestorable:false,draft:JSON.parse(await draftBody({...defaultForm(),name})),history:[],current:null},airspaceSnapshots:[],flightops:[]});
try{
  const old=await capsule('Draft gốc'),next=await capsule('Draft mới');
  for(const phase of ['RECORD_PUBLISHED','HEAD_PENDING','HEAD_COMMITTED']){
    const store=path.join(root,phase),marker=path.join(root,phase+'.marker'),first=await journal('save',store,'ROOT',old);
    owned=spawn('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin/java',['-cp',path.resolve('native/flightops35/dist/journal-host.jar'),'vn.rtr.aeris.flightops35.CrashMain',store,first.token,phase,marker],{stdio:['pipe','pipe','pipe']});
    const pid=owned.pid;children.push(pid);let errors='';owned.stderr.on('data',b=>errors+=b);
    const ended=new Promise(resolve=>owned.once('exit',(code,signal)=>resolve({code,signal})));
    owned.stdin.end(next);let seen=false;
    for(let i=0;i<100;i++){try{seen=(await readFile(marker,'utf8'))===phase;if(seen)break}catch{}if(owned.exitCode!==null)break;await new Promise(r=>setTimeout(r,50))}
    check('owned JVM reached boundary '+phase,seen);check('own child alive before kill '+phase,owned.exitCode===null);
    owned.kill('SIGKILL');const exit=await ended;owned=null;check('actual SIGKILL '+phase,exit.signal==='SIGKILL');
    const recovered=await journal('load',store),body=Buffer.from(recovered.bodyBase64,'base64').toString();
    check('exact committed capsule '+phase,body===(phase==='HEAD_COMMITTED'?next:old));await validateCapsule(body);
    check('immutable failed revision preserved '+phase,(await readdir(store)).filter(n=>n.endsWith('.bin')).length===2);
    check('pending disclosure '+phase,recovered.pending===(phase==='HEAD_PENDING'));
    if(recovered.pending){let refused=false;try{await journal('save',store,recovered.token,next)}catch{refused=true}check('pending never automatically published '+phase,refused)}
    const dest=path.join(evidence,phase);await mkdir(dest);for(const name of await readdir(store))await copyFile(path.join(store,name),path.join(dest,name));
    await writeFile(dest+'/receipt.json',JSON.stringify({ownedPID:pid,exit,previousToken:first.token,recovered,stderr:errors,scope:'Actual host JVM death; OS/disk remain up, not Android or power-loss proof'},null,2)+'\n');
  }
}catch(e){checks.push({name:'crash suite failure',pass:false,error:e.stack})}
finally{if(owned){owned.kill('SIGKILL');await new Promise(r=>owned.once('close',r))}await rm(root,{recursive:true,force:true});await writeFile(E+'/crash'+attempt+'.json',JSON.stringify({status:checks.every(c=>c.pass)?'PASS':'FAIL',checks,ownedPIDs:children,cleanup:[root],scope:'Host JVM real SIGKILL/immutable Java workspace; Android app-private/ART/reboot NOT_CHECKED'},null,2)+'\n');console.log(checks.length,'checks',checks.filter(c=>!c.pass).length,'failed');if(checks.some(c=>!c.pass))process.exitCode=1;}
