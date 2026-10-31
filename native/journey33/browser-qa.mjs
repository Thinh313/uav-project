import {chromium} from '/Users/os/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {readFile,writeFile,rm,mkdir,readdir,copyFile} from 'node:fs/promises';import path from 'node:path';
import {preview,journal} from './server.mjs';import {validateWorkspace} from './journey.mjs';
import {createHash} from 'node:crypto';
const E=path.resolve('evidence/native33');let attempt=1;for(;;attempt++){try{await readFile(E+'/browser'+attempt+'.json')}catch{try{await readFile(E+'/browser'+attempt+'/running-before-restart.json');}catch{break}}}
const folder=E+'/browser'+attempt;await mkdir(folder);const store=path.resolve('native/journey33/.qa-store-'+attempt);
const sourceHashes={};for(const name of ['index.html','shell.css','shell.mjs','journey.mjs','editor.mjs','pins.mjs','vendor/survey.mjs','vendor/compiler.mjs','server.mjs','browser-qa.mjs'])sourceHashes[name]=createHash('sha256').update(await readFile('native/journey33/'+name)).digest('hex');
const checks=[],errors=[],external=[],writes=[];let browser,server=preview({store});
const check=(name,v)=>{checks.push({name,pass:!!v});console.log(name,v?'PASS':'FAIL');if(!v)throw Error(name)};
await new Promise(r=>server.listen(0,'127.0.0.1',r));let url='http://127.0.0.1:'+server.address().port;
const opened=[];
async function pageIn(ctx){const p=await ctx.newPage();opened.push(p);p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(!r.url().startsWith(url)&&!r.url().startsWith('blob:'))external.push(r.url());if(r.method()!=='GET')writes.push(r.url());});await p.goto(url);await idle(p);return p;}
async function idle(p){await p.waitForFunction(()=>!document.querySelector('#reload').disabled&&document.querySelector('#phase').textContent!=='STORAGE_UNCONFIRMED');}
async function click(p,id){await p.click('#'+id);await p.waitForFunction(()=>!document.querySelector('#reload').disabled);}
async function nav(p,stage){await p.locator('[data-view='+stage+']').click();}
async function read(){const d=await journal('load',store);return {d,w:await validateWorkspace(Buffer.from(d.bodyBase64,'base64').toString())};}
async function start(p){await nav(p,'Plan');await click(p,'compile');await click(p,'inspect');await click(p,'home');await click(p,'datum');await click(p,'start');}
try{
  browser=await chromium.launch({headless:true});let ctx=await browser.newContext({viewport:{width:1280,height:800},acceptDownloads:true});let p=await pageIn(ctx);
  check('initial default without authority',await p.locator('#phase').innerText()==='DRAFT');
  await p.fill('#name','Khảo sát Native33');await p.fill('#altitude','72');await click(p,'save');
  check('explicit save binds edited draft', (await read()).w.draft.form.altitude==='72');
  await p.reload();await idle(p);check('page restart restores draft without mission gates',await p.locator('#altitude').inputValue()==='72'&&await p.locator('#phase').innerText()==='DRAFT');
  await p.fill('#speed','0');await click(p,'save');await p.reload();await idle(p);await click(p,'compile');
  check('invalid draft survives restart and cannot compile',await p.locator('#speed').inputValue()==='0'&&await p.locator('#phase').innerText()==='DRAFT');
  await p.fill('#speed','4');await click(p,'compile');await nav(p,'Fly');await click(p,'start');check('start without confirmations refused',await p.locator('#phase').innerText()==='COMPILED_DRAFT');
  await nav(p,'Preflight');await click(p,'inspect');await click(p,'home');await click(p,'datum');await click(p,'start');
  check('four-stage path starts only with current confirmed gates',await p.locator('#phase').innerText()==='RUNNING_MOCK');
  check('active run locks editor',await p.locator('#altitude').isDisabled());
  await click(p,'ack');check('ACK checkpoint does not advance route',(await read()).w.current.cursor===0);
  await click(p,'land');check('early landing refused',await p.locator('#phase').innerText()==='RUNNING_MOCK');
  await click(p,'step');const prefix=(await read()).w.current;
  await writeFile(folder+'/running-before-restart.json',JSON.stringify(prefix,null,2));await p.screenshot({path:folder+'/fly-1280.png',fullPage:true});
  // Browser context destruction and new server process boundary; host Java commits survive.
  await ctx.close();await new Promise(r=>server.close(r));server=preview({store});await new Promise(r=>server.listen(0,'127.0.0.1',r));url='http://127.0.0.1:'+server.address().port;
  ctx=await browser.newContext({viewport:{width:1280,height:800},acceptDownloads:true});p=await pageIn(ctx);
  const interrupted=(await read()).w.current;
  check('new runtime interrupts prior run with exact saved prefix',interrupted.phase==='INTERRUPTED_RESTART'&&interrupted.cursor===1&&JSON.stringify(interrupted.events.slice(0,-1))===JSON.stringify(prefix.events));
  check('restart cannot resume/restore authority',await p.locator('#phase').innerText()==='DRAFT'&&await p.locator('#altitude').inputValue()==='72');
  await nav(p,'Review');check('review reports interruption and zero real media',(await p.locator('#review-summary').innerText()).includes('gián đoạn')&&interrupted.media.length===0&&!interrupted.flightExecutionProven);
  await start(p);const count=JSON.parse((await read()).w.current.compiledRaw).items; // route length from screen, not command ACK
  let iterations=0;while(await p.locator('#phase').innerText()==='RUNNING_MOCK'&&iterations++<200)await click(p,'step');
  check('full route still requires explicit landing',await p.locator('#phase').innerText()==='AWAITING_MOCK_LANDING');
  await click(p,'land');const done=(await read()).w;
  check('completed mock auto-checkpointed with historical interrupted run',done.current.phase==='COMPLETED_MOCK'&&done.history.length===1&&done.history[0].session===prefix.session);
  check('review has exact mission provenance and no physical media',done.draft.missionSha256===done.current.missionSha256&&!done.current.authorityRestorable&&!done.current.physicalMediaVerified&&done.current.media.length===0);
  await p.screenshot({path:folder+'/review-1280.png',fullPage:true});await writeFile(folder+'/completed-workspace.json',JSON.stringify(done,null,2));
  const stable=JSON.stringify(done);await p.reload();await idle(p);check('completed review survives restart byte-exact without authority',JSON.stringify((await read()).w)===stable&&await p.locator('#phase').innerText()==='DRAFT');
  await nav(p,'Plan');const downloadEvent=p.waitForEvent('download');await click(p,'export');const download=await downloadEvent;await download.saveAs(folder+'/export.json');
  check('export re-import verifier exact committed workspace',JSON.stringify(await validateWorkspace(await readFile(folder+'/export.json','utf8')))===stable);
  await p.fill('#name','Nhiệm vụ thứ ba');await click(p,'compile');await click(p,'inspect');await click(p,'home');await click(p,'datum');await click(p,'start');await click(p,'loss');
  check('link interruption saved and never called completed',(await read()).w.current.phase==='INTERRUPTED_LINK');
  await nav(p,'Plan');await p.fill('#vertices','10.854,106.807\n10.855,106.807\n10.854,106.808');await click(p,'compile');
  check('arbitrary triangle uses pinned compiler', (await read()).w.current.missionForm.vertices.split('\n').length===3);
  await p.reload();await idle(p);
  const other=await pageIn(ctx);await p.bringToFront();await nav(p,'Plan');await p.fill('#name','Writer A');await click(p,'save');await other.bringToFront();await other.fill('#name','Writer B stale');await click(other,'save');
  check('stale UI writer blocked without overwriting new draft',await other.locator('#phase').innerText()==='STORAGE_UNCONFIRMED'&&(await read()).w.draft.form.name==='Writer A');await other.close();await p.bringToFront();
  await click(p,'reload');await nav(p,'Plan');
  for(const width of [1920,1280,1024,800,600,360]){
    await p.setViewportSize({width,height:800});const geometry=await p.evaluate(()=>{const nav=[...document.querySelectorAll('nav button')].map(x=>x.getBoundingClientRect());return {overflow:document.documentElement.scrollWidth>innerWidth,aligned:nav.every(x=>x.height>=48&&Math.abs(x.height-nav[0].height)<1),inputs:[...document.querySelectorAll('input:not([type=file]),textarea')].every(x=>x.getBoundingClientRect().height>=48)}});
    check('aligned accessible host controls/no overflow '+width,!geometry.overflow&&geometry.aligned&&geometry.inputs);
  }
  await p.screenshot({path:folder+'/plan-360.png',fullPage:true});await p.setViewportSize({width:1280,height:800});await p.screenshot({path:folder+'/plan-1280.png',fullPage:true});
  const tampered=structuredClone(done);tampered.sourceId='foreign';await p.setInputFiles('#import',{name:'tampered.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(tampered))});await p.waitForFunction(()=>!document.querySelector('#reload').disabled);
  check('tampered import refused without changing authority',(await p.locator('#status').innerText()).includes('scope/version')&&await p.locator('#phase').innerText()==='DRAFT');
  check('no flight API',(await fetch(url+'/api/sitl/command',{method:'POST'})).status===405);
  check('cross-origin write refused',(await fetch(url+'/workspace/save',{method:'POST',headers:{Origin:'https://foreign.invalid','Content-Type':'application/json'},body:'{}'})).status===403);
  check('zero console errors/external requests/non-workspace writes',errors.length===0&&external.length===0&&writes.every(u=>u.endsWith('/workspace/save')));
}catch(e){checks.push({name:'browser failure',pass:false,error:e.stack});console.error(e.stack);for(const [i,p]of opened.entries())if(!p.isClosed()){await writeFile(folder+'/failure-page-'+i+'.json',JSON.stringify(await p.evaluate(()=>({phase:document.querySelector('#phase')?.textContent,status:document.querySelector('#status')?.textContent,storage:document.querySelector('#storage')?.textContent})),null,2));await p.screenshot({path:folder+'/failure-page-'+i+'.png',fullPage:true});}try{await mkdir(folder+'/failure-store');for(const name of await readdir(store))await copyFile(path.join(store,name),path.join(folder,'failure-store',name));}catch{}}
finally{await browser?.close();await new Promise(r=>server.close(r));await rm(store,{recursive:true,force:true});await writeFile(E+'/browser'+attempt+'.json',JSON.stringify({status:checks.every(c=>c.pass)?'PASS':'FAIL',checks,errors,external,sourceHashes,scope:'Host Chromium + real Java journal, not Android/WebView/app-private/reboot acceptance',cleanup:[store],androidRuntime:'NOT_CHECKED'},null,2)+'\n');console.log(checks.length,'checks',checks.filter(c=>!c.pass).length,'failed');if(checks.some(c=>!c.pass))process.exitCode=1;}
