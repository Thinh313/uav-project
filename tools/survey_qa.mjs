import assert from 'node:assert/strict';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
const ROOT=fileURLToPath(new URL('../',import.meta.url)),OUT=path.join(ROOT,process.env.AERIS_EVIDENCE_DIR||'evidence/survey01');await mkdir(OUT,{recursive:true});
const {chromium}=await import(pathToFileURL(process.env.AERIS_PLAYWRIGHT_MODULE));
const browser=await chromium.launch({headless:true}),context=await browser.newContext({viewport:{width:1280,height:800},hasTouch:true,acceptDownloads:true});
const page=await context.newPage(),checks=[],errors=[],requests=[];
page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});page.on('request',r=>requests.push(r.url()));
page.on('dialog',d=>d.accept());
async function check(name,fn){try{await fn();checks.push({name,status:'PASS'});console.log('PASS',name);}catch(e){checks.push({name,status:'FAIL',error:e.message});throw e;}}
const summary=()=>page.locator('#mission-summary').textContent();
async function fileAction(id){if(await page.locator('#mission-menu').isHidden())await page.locator('#open-mission-menu').tap();await page.locator('#'+id).tap();}
async function set(name,value){const l=page.locator(`[name="${name}"]`);await l.scrollIntoViewIfNeeded();await l.fill(String(value));}
async function recalc(){await page.locator('.recalculate').tap();}
async function bounds(selector,parent){const a=await page.locator(selector).boundingBox(),b=await page.locator(parent).boundingBox();assert.ok(a&&b&&a.x>=b.x-.5&&a.y>=b.y-.5&&a.x+a.width<=b.x+b.width+.5&&a.y+a.height<=b.y+b.height+.5,selector+' clipped');}
try{
 await page.goto(process.env.AERIS_QA_URL||'http://127.0.0.1:8788');await page.evaluate(()=>document.fonts.ready);
 await check('U1 WGS84 reference Plan and primary actions fit HeraHub review viewport',async()=>{
  assert.match(await summary(),/7,88/);assert.match(await summary(),/337/);assert.match(await page.locator('.map-context').textContent(),/WGS84/);assert.equal(await page.evaluate(()=>navigator.maxTouchPoints>0),true);
  for(const sel of ['#mission-summary','.recalculate','#mission-validation','#open-fly','#draw-area','#edit-coordinates'])await bounds(sel,'#workspace-plan');
  await page.screenshot({path:path.join(OUT,'plan-herahub.png')});
 });
 await check('U1 select, footprint and zoom leave stored survey geometry unchanged',async()=>{
  const before=await summary();await page.locator('#next-transect').tap();assert.match(await page.locator('#selected-transect-label').textContent(),/02/);await page.locator('#toggle-footprint').tap();assert.equal(await page.locator('#toggle-footprint').getAttribute('aria-pressed'),'true');await page.locator('#zoom-in').tap();await page.locator('#fit-map').tap();assert.equal(await summary(),before);
 });
 await check('U1 dirty heading clears figures and blocks stale export/upload',async()=>{
  await set('heading',30);assert.equal(await page.locator('#export-mission').isDisabled(),true);assert.equal(await page.locator('#open-fly').isDisabled(),true);assert.ok(!(await summary()).includes('337'));await recalc();assert.equal(await page.locator('#mission-validation').getAttribute('data-state'),'valid');assert.match(await page.locator('#site-description').textContent(),/7,88/);
 });
 await check('U1 GSD target recalculates visible altitude and optical result',async()=>{
  await set('heading',0);await set('targetGsdCm',1);await recalc();assert.equal(Number(await page.locator('[name=altitude]').inputValue()),36.48);assert.match(await page.locator('#optics-summary').textContent(),/1 cm\/px/);await set('targetGsdCm','');await set('altitude',60);await recalc();
 });
 await check('U1 incomplete terrain preserves draft save but never shows invented photos or permits upload',async()=>{
  await page.locator('[name=altitudeFrame]').selectOption('terrain');await recalc();assert.match(await page.locator('#mission-validation').textContent(),/Thiếu DEM/);assert.equal(await page.locator('#open-fly').isDisabled(),true);assert.equal(await page.locator('#save-mission').isDisabled(),false);assert.match(await summary(),/Ảnh dự kiến—/);await page.locator('[name=altitudeFrame]').selectOption('flat-reference');await recalc();
 });
 await check('U1 custom camera rate failure and missing camera are visible honest readiness states',async()=>{
  await page.locator('.camera-details summary').tap();await set('minInterval',10);await recalc();assert.match(await page.locator('#mission-validation').textContent(),/không theo kịp/);assert.equal(await page.locator('#open-fly').isDisabled(),true);await set('minInterval',1);await page.locator('[name=cameraProfile]').selectOption('none');await recalc();assert.match(await page.locator('#mission-validation').textContent(),/Chưa có footprint/);assert.match(await summary(),/Ảnh dự kiến—/);await page.locator('[name=cameraProfile]').selectOption('demo');await recalc();await page.locator('.camera-details summary').tap();
 });
 await check('U1 vertex drag changes polygon and recalculates route after release',async()=>{
  const before=await summary(),v=await page.locator('[data-vertex="2"] circle').last().boundingBox();await page.mouse.move(v.x+v.width/2,v.y+v.height/2);await page.mouse.down();await page.mouse.move(v.x+v.width/2-30,v.y+v.height/2+20,{steps:5});await page.mouse.up();assert.notEqual(await summary(),before);assert.equal(await page.locator('#mission-validation').getAttribute('data-state'),'valid');
 });
 await check('U1 coordinate editor rejects invalid polygon without replacing valid plan',async()=>{
  const before=await summary();await page.locator('#edit-coordinates').tap();const coords=await page.locator('#coordinates-input').inputValue();await page.locator('#coordinates-input').fill('10.854, 106.807\n10.854,106.807\n10.855,106.808');await page.locator('#apply-coordinates').tap();assert.match(await page.locator('#coordinates-error').textContent(),/trùng/);assert.equal(await summary(),before);await page.locator('#coordinates-input').fill(coords);await page.locator('#apply-coordinates').tap();assert.equal(await page.locator('#coordinates-dialog').isVisible(),false);
 });
 await check('U1 local named library restores geometry and recomputes result',async()=>{
  await set('name','Hera · site A');await recalc();const expected=await summary();await fileAction('save-mission');await set('heading',50);await recalc();await fileAction('load-mission');await page.locator('#mission-library-list button').first().tap();assert.equal(await page.locator('[name=heading]').inputValue(),'0');assert.equal(await summary(),expected);
 });
 let downloaded;
 await check('U1 v2 export/import round-trip retains polygon, camera, frame and result',async()=>{
  const expected=await summary(),promise=page.waitForEvent('download');await fileAction('export-mission');downloaded=await promise;const file=await downloaded.path(),pkg=JSON.parse(await readFile(file,'utf8'));assert.equal(pkg.format,'aeris-survey');assert.equal(pkg.version,2);assert.equal(pkg.operational,false);assert.equal(pkg.settings.polygon.length,4);await set('speed',7);await recalc();await page.locator('#mission-file').setInputFiles(file);await page.waitForFunction(()=>document.querySelector('[name=speed]').value==='6');assert.equal(await summary(),expected);assert.equal(await page.locator('[name=speed]').inputValue(),'6');
 });
 await check('I1 upload ACK cannot start mission until matching readback',async()=>{
  await page.locator('#open-fly').tap();assert.match(await page.locator('#mission-session-state').textContent(),/ACK/);assert.equal(await page.locator('#mission-start').isDisabled(),true);await page.locator('#mission-ack').tap();assert.match(await page.locator('#mission-session-state').textContent(),/readback/);assert.equal(await page.locator('#mission-start').isDisabled(),true);await page.locator('#mission-readback').tap();assert.match(await page.locator('#mission-session-state').textContent(),/đã khớp/);assert.equal(await page.locator('#mission-start').isDisabled(),false);
 });
 await check('I1 mission start/pause/resume observes progress without advancing resume',async()=>{
  await page.locator('#mission-start').tap();await page.locator('#mission-advance').tap();assert.match(await page.locator('#mission-session-detail').textContent(),/1\//);await page.locator('#mission-pause').tap();assert.match(await page.locator('#mission-session-state').textContent(),/tạm dừng/);await page.locator('#mission-start').tap();assert.match(await page.locator('#mission-session-detail').textContent(),/1\//);await page.locator('#mission-pause').tap();await page.locator('#close-test-console').tap();await page.screenshot({path:path.join(OUT,'fly-herahub.png')});
 });
 await check('I1 planner edits do not mutate mission on simulated vehicle',async()=>{
  const old=await page.locator('#onboard-name').textContent();await page.locator('[data-workspace=plan]').tap();await set('name','Bản nháp khác');await set('heading',15);await recalc();await page.locator('[data-workspace=fly]').tap();assert.equal(await page.locator('#onboard-name').textContent(),old);assert.match(await page.locator('#mission-session-detail').textContent(),/Bản nháp khác/);
 });
 await check('I1 mode ACK still needs fresh observed telemetry and video loss is independent',async()=>{
  await page.locator('[data-mode=AUTO]').tap();await page.locator('#open-test-console').tap();await page.locator('#ack-accepted').tap();assert.match(await page.locator('#command-state').textContent(),/chưa xác nhận/);assert.match(await page.locator('#flight-mode').textContent(),/HOLD/);await page.locator('#observe-mode').tap();assert.match(await page.locator('#flight-mode').textContent(),/AUTO/);await page.locator('#toggle-video').tap();assert.match(await page.locator('#fly-checks').textContent(),/Telemetry: mới/);await page.locator('#pause-telemetry').tap();await page.waitForFunction(()=>document.getElementById('flight-mode').textContent.includes('dữ liệu cũ'),null,{timeout:5000});assert.match(await page.locator('#telemetry-values').textContent(),/—/);assert.equal(await page.locator('[data-mode=HOLD]').isDisabled(),true);
 });
 await check('I1 reload restores digest-checked plan without claiming execution',async()=>{
  await page.reload();await page.locator('#mission-summary .metric').first().waitFor();await page.locator('[data-workspace=fly]').tap();assert.match(await page.locator('#mission-session-state').textContent(),/Readback đã khớp/);assert.match(await page.locator('#mission-session-detail').textContent(),/1\//);assert.equal(await page.locator('#onboard-name').textContent(),'Hera · site A');
 });
 await check('U1 touch polygon drawing and close action recompute a new mission',async()=>{
  await page.locator('[data-workspace=plan]').tap();await page.locator('#draw-area').tap();const b=await page.locator('#mission-map').boundingBox();for(const [x,y]of [[.35,.35],[.7,.35],[.7,.65],[.35,.65]])await page.touchscreen.tap(b.x+b.width*x,b.y+b.height*y);await page.locator('#complete-area').tap();assert.match(await page.locator('#area-description').textContent(),/4 đỉnh/);assert.equal(await page.locator('#complete-area').isVisible(),false);assert.equal(await page.locator('#mission-validation').getAttribute('data-state'),'valid');
 });
 await check('U1 critical content remains in viewport at 1440×900 and 1280×720',async()=>{
  for(const [width,height]of [[1440,900],[1280,720]]){await page.setViewportSize({width,height});for(const sel of ['#mission-summary','.recalculate','#mission-validation','#open-fly','#edit-coordinates'])await bounds(sel,'#workspace-plan');assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await page.screenshot({path:path.join(OUT,`plan-${width}x${height}.png`)});}
 });
 await check('U1 mobile sheet, focus and close preserve accessible workflow',async()=>{
  await page.setViewportSize({width:390,height:844});await page.locator('#open-plan-settings').tap();assert.equal(await page.locator('#plan-inspector').getAttribute('aria-modal'),'true');await set('heading',20);await recalc();await page.locator('#close-plan-settings').tap();assert.equal(await page.locator('#plan-inspector').isVisible(),false);await page.screenshot({path:path.join(OUT,'plan-mobile.png')});await page.locator('[data-workspace=fly]').tap();for(const sel of ['#mission-session-state','#mission-start','#mission-pause'])await bounds(sel,'#workspace-fly');await page.screenshot({path:path.join(OUT,'fly-mobile.png')});
 });
 await check('V1 no runtime errors, external asset requests or served private BOM',async()=>{
  assert.deepEqual(errors,[]);assert.ok(requests.every(u=>u.startsWith('http://127.0.0.1:8788/')||u.startsWith('data:')||u.startsWith('blob:')));assert.equal((await fetch('http://127.0.0.1:8788/sot/source_canonical/0.BOM26.xlsx')).status,404);
 });
}finally{await writeFile(path.join(OUT,'browser-qa.json'),JSON.stringify({checks,errors,externalRequests:requests.filter(u=>!u.startsWith('http://127.0.0.1:8788/')&&!u.startsWith('data:')&&!u.startsWith('blob:')),scope:'Chromium reference/touch simulation, not Android/Hera/SITL or operator acceptance'},null,2)+'\n');await browser.close();}
