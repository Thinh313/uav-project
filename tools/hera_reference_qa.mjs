import assert from 'node:assert/strict';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('../',import.meta.url));
const output=path.join(root,'evidence/hera01');await mkdir(output,{recursive:true});
const profile=JSON.parse(await readFile(path.join(root,'hardware/herahub2/profile.json'),'utf8'));
assert.deepEqual(profile.fields.display_resolution_px.claim,[1280,800]);
const {chromium}=await import(pathToFileURL(process.env.AERIS_PLAYWRIGHT_MODULE));
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1280,height:800},hasTouch:true,deviceScaleFactor:1});
const page=await context.newPage(),results=[],errors=[];page.on('pageerror',e=>errors.push(e.message));
async function check(name,fn){try{const detail=await fn();results.push({name,status:'PASS',...(detail?{detail}:{})});console.log('PASS',name);}catch(e){results.push({name,status:'FAIL',error:e.message});throw e;}}
async function visibleBounds(locator,container){const a=await locator.boundingBox(),b=await container.boundingBox();assert.ok(a&&b&&a.y>=b.y&&a.y+a.height<=b.y+b.height&&a.x>=b.x&&a.x+a.width<=b.x+b.width);}
try{
 await page.goto('http://127.0.0.1:8788');await page.evaluate(()=>document.fonts.ready);
 await check('HERA-02 touch reference basic Plan inputs/actions are not clipped',async()=>{
  assert.equal(await page.evaluate(()=>navigator.maxTouchPoints>0),true);
  for(const name of ['width','height','altitude','speed','sideOverlap','frontOverlap'])await visibleBounds(page.locator(`[name=${name}]`),page.locator('.inspector-scroll'));
  for(const selector of ['#mission-summary','.recalculate','#mission-validation','#open-fly'])await visibleBounds(page.locator(selector),page.locator('#workspace-plan'));
  await page.screenshot({path:path.join(output,'hera-plan-reference.png')});
 });
 await check('HERA-02 touch transect/footprint/zoom do not alter mission',async()=>{
  const before=await page.locator('#mission-summary').textContent();await page.locator('#next-transect').tap();assert.match(await page.locator('#selected-transect-label').textContent(),/02/);await page.locator('#toggle-footprint').tap();assert.equal(await page.locator('#toggle-footprint').getAttribute('aria-pressed'),'true');await page.locator('#zoom-in').tap();await page.locator('#fit-map').tap();assert.equal(await page.locator('#mission-summary').textContent(),before);
 });
 await check('HERA-02 file menu and advanced camera operate with touch',async()=>{
  await page.locator('#open-mission-menu').tap();assert.equal(await page.locator('#mission-menu').isVisible(),true);await page.locator('#open-mission-menu').tap();assert.equal(await page.locator('#mission-menu').isVisible(),false);await page.locator('.camera-details summary').tap();await page.locator('[name=minInterval]').scrollIntoViewIfNeeded();await visibleBounds(page.locator('[name=minInterval]'),page.locator('.inspector-scroll'));await page.locator('.camera-details summary').tap();await page.locator('[name=width]').scrollIntoViewIfNeeded();
 });
 await check('HERA-02 dirty mission clears through recalculation',async()=>{
  await page.locator('[name=width]').fill('420');assert.match(await page.locator('#mission-validation').textContent(),/Thông số đã thay đổi/);assert.equal(await page.locator('#open-fly').isEnabled(),false);await page.locator('.recalculate').tap();assert.match(await page.locator('#site-description').textContent(),/420/);assert.match(await page.locator('#mission-validation').textContent(),/Thông số đã kiểm/);assert.equal(await page.locator('#open-fly').isEnabled(),true);
 });
 await check('HERA-02 Fly commands and state are visible in reference window',async()=>{
  await page.locator('#open-fly').tap();for(const selector of ['#flight-mode','#telemetry-values','#command-state','[data-mode=AUTO]','[data-mode=HOLD]','[data-mode=RTL]'])await visibleBounds(page.locator(selector),page.locator('#workspace-fly'));await page.screenshot({path:path.join(output,'hera-fly-reference.png')});
 });
 await check('HERA-02 touch rehearsal maintains ACK/observed distinction',async()=>{
  await page.locator('[data-mode=AUTO]').tap();await page.locator('#open-test-console').tap();await page.locator('#ack-accepted').tap();assert.match(await page.locator('#flight-mode').textContent(),/HOLD/);await page.locator('#observe-mode').tap();assert.match(await page.locator('#flight-mode').textContent(),/AUTO/);await page.locator('#close-test-console').tap();
 });
 await check('HERA-02 all workspaces have no page overflow or runtime exception',async()=>{
  for(const name of ['plan','fly','inspect','review']){await page.locator(`[data-workspace=${name}]`).tap();assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight),name);}assert.deepEqual(errors,[]);
 });
}finally{
 await writeFile(path.join(output,'reference-qa.json'),JSON.stringify({checkedAt:new Date().toISOString(),viewport:{width:1280,height:800},deviceScaleFactor:1,hasTouch:true,results,errors,scope:'Chromium touch reference at nominal panel dimensions; DPR 1 is an assumption. Not Android emulator, dp verification, Hera device, physical RC mapping or flight.'},null,2)+'\n');await browser.close();
}
