import assert from 'node:assert/strict';
import {chromium} from '/Users/os/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {mkdir,writeFile,readdir,copyFile,rm} from 'node:fs/promises';
import {preview,journal} from './server.mjs';
import {validateCapsule44} from './capsule.mjs';

const dir='evidence/native44/checkbox-fault1',store='.local/native44/checkbox-qa',results=[];
await mkdir(dir);const server=preview({store});let browser,context;
const check=(name,pass)=>{assert.ok(pass,name);results.push({name,pass:true});console.log(name+' PASS');};
const idle=p=>p.waitForFunction(()=>!document.querySelector('#reload').disabled);
const read=async()=>{const r=await journal('load',store);return validateCapsule44(Buffer.from(r.bodyBase64,'base64').toString());};
try{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const url='http://127.0.0.1:'+server.address().port;
 browser=await chromium.launch({headless:true});context=await browser.newContext({viewport:{width:1280,height:800}});const p=await context.newPage(),errors=[],external=[];
 p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(!r.url().startsWith(url))external.push(r.url());});
 await p.goto(url);await idle(p);await p.click('#compile');await idle(p);await p.click('#inspect');await idle(p);
 const beforeHome=await read();let release,entered;const held=new Promise(r=>release=r),atWriter=new Promise(r=>entered=r);
 await p.route('**/workspace/save',async r=>{entered();await held;await r.continue();},{times:1});
 await p.locator('#home').focus();await p.keyboard.press('Space');await atWriter;await p.waitForTimeout(650);
 check('keyboard Home remains pending over periodic render',await p.locator('#home').isChecked()&&await p.locator('#home').getAttribute('aria-busy')==='true');
 check('pending Home has no durable confirmation or start',(await read()).journey.current.events.length===beforeHome.journey.current.events.length&&await p.locator('#start').isDisabled());
 release();await idle(p);check('Home exactly committed once',(await read()).journey.current.events.filter(e=>e.body.kind==='HOME_CONFIRMED').length===1);
 const before=await read();let releaseFault,enteredFault,calls=0;const holdFault=new Promise(r=>releaseFault=r),atFault=new Promise(r=>enteredFault=r);
 await p.route('**/workspace/save',async r=>{calls++;enteredFault();await holdFault;await r.abort('failed');},{times:1});
 await p.locator('#datum').check();await atFault;await p.waitForTimeout(650);
 check('pending datum stays checked and all confirmations/start disabled',await p.locator('#datum').isChecked()&&await p.locator('#home').isDisabled()&&await p.locator('#datum').isDisabled()&&await p.locator('#start').isDisabled());
 releaseFault();await idle(p);
 check('failed save rolls back both confirmations and clears pending',!(await p.locator('#home').isChecked())&&!(await p.locator('#datum').isChecked())&&await p.locator('#datum').getAttribute('aria-busy')==='false');
 check('failed save visibly blocks storage and start',await p.locator('#phase').innerText()==='STORAGE_UNCONFIRMED'&&await p.locator('#start').isDisabled()&&await p.locator('#inspect').isDisabled());
 check('failed save retains exact committed capsule without retry',JSON.stringify(await read())===JSON.stringify(before)&&calls===1);
 await p.screenshot({path:dir+'/storage-failure-1280.png',fullPage:true});
 await p.click('#reload');await idle(p);
 check('explicit reload restores evidence without source/confirmations',await p.locator('#pf-state').innerText()==='Chưa có nguồn'&&await p.locator('#start').isDisabled()&&!(await p.locator('#home').isChecked())&&!(await p.locator('#datum').isChecked()));
 check('no external requests or browser exceptions',!errors.length&&!external.length);
 await writeFile(dir+'/receipt.json',JSON.stringify({status:'PASS',checks:results.length,results,errors,external,scope:'ActualChromium/hostJVM mock only; noAndroid/Hera'},null,2)+'\n',{flag:'wx'});
}catch(e){await writeFile(dir+'/failure.json',JSON.stringify({status:'FAIL',error:e.stack,passed:results},null,2)+'\n',{flag:'wx'});throw e;}
finally{await context?.close();await browser?.close();if(server.listening)await new Promise(r=>server.close(r));await mkdir(dir+'/retained-store');try{for(const f of await readdir(store))await copyFile(store+'/'+f,dir+'/retained-store/'+f);}catch{}await rm(store,{recursive:true,force:true});await writeFile(dir+'/cleanup.json',JSON.stringify({removed:[store],browserClosed:true,serverClosed:true},null,2)+'\n',{flag:'wx'});}
