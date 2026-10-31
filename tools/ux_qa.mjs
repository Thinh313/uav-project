import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('../',import.meta.url));
const output=path.join(root,'evidence/ux01');
const {chromium}=await import(pathToFileURL(process.env.AERIS_PLAYWRIGHT_MODULE));
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1440,height:900}});
const results=[],errors=[];page.on('pageerror',e=>errors.push(e.message));
async function test(name,fn){try{const detail=await fn();results.push({name,status:'PASS',...(detail?{detail}:{})});console.log('PASS',name);}catch(e){results.push({name,status:'FAIL',error:e.message});throw e;}}
async function inViewport(ids){for(const id of ids){const rect=await page.locator('#'+id).boundingBox();assert.ok(rect&&rect.y>=0&&rect.y+rect.height<=await page.evaluate(()=>innerHeight),id+' outside viewport');}}
const luminance=hex=>{const rgb=hex.match(/[a-f\d]{2}/gi).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722;};
const ratio=(a,b)=>{const l=[luminance(a),luminance(b)].sort((a,b)=>b-a);return(l[0]+.05)/(l[1]+.05);};
try{
 await page.goto('http://127.0.0.1:8788');await page.evaluate(()=>document.fonts.ready);
 await test('UX-01 local font and white/black/yellow working tokens',async()=>{assert.equal(await page.evaluate(()=>document.fonts.check('14px Plex')),true);const tokens=await page.evaluate(()=>{const s=getComputedStyle(document.documentElement);return {carbon:s.getPropertyValue('--carbon').trim(),paper:s.getPropertyValue('--paper').trim(),yellow:s.getPropertyValue('--yellow').trim()};});assert.deepEqual(tokens,{carbon:'#050505',paper:'#fff',yellow:'#f2ca30'});return tokens;});
 await test('UX-02 critical Plan/Fly UI stays visible at desktop and landscape tablet',async()=>{
  for(const [width,height] of [[1440,900],[1024,768],[1280,720]]){await page.setViewportSize({width,height});await page.locator('[data-workspace=plan]').click();await inViewport(['mission-summary','mission-validation','open-fly']);const calculate=await page.locator('.recalculate').boundingBox();assert.ok(calculate.y+calculate.height<=height);const scroll=await page.locator('.inspector-scroll').boundingBox();for(const name of ['width','height','altitude','speed','sideOverlap','frontOverlap']){const b=await page.locator(`[name=${name}]`).boundingBox();assert.ok(b.y>=scroll.y&&b.y+b.height<=scroll.y+scroll.height,name+' clipped by inspector');}
   if(height===720){const origin=await page.locator('#mission-map svg text').filter({hasText:'(0, 0)'}).boundingBox();const dock=await page.locator('.transect-dock').boundingBox();assert.ok(origin.y+origin.height<dock.y,'Origin label obscured by transect dock');}
   await page.screenshot({path:path.join(output,`plan-${width}.png`)});
   await page.locator('[data-workspace=fly]').click();await inViewport(['flight-mode','telemetry-values','command-state']);for(const b of await page.locator('[data-mode]').all()){const r=await b.boundingBox();assert.ok(r.y+r.height<=height);}
  }
  await page.setViewportSize({width:1440,height:900});await page.locator('[data-workspace=plan]').click();
 });
 await test('UX-03 selected normal text and control token contrasts',async()=>{
  const pairs=[['101010','ffffff',4.5],['666666','ffffff',4.5],['b8b8bc','101012',4.5],['101010','f2ca30',4.5],['b42318','ffffff',4.5],['888888','fafafa',3],['77777c','101012',3],['a5a5ad','19191c',3],['806700','ffffff',3]];
  const readings=pairs.map(([a,b,min])=>({foreground:a,background:b,ratio:+ratio(a,b).toFixed(2),required:min}));for(const r of readings)assert.ok(r.ratio>=r.required,JSON.stringify(r));return readings;
 });
 await test('UX-03 active controls meet 44px project floor',async()=>{
  const sizes=await page.locator('button:visible,input:visible,summary:visible').evaluateAll(els=>els.filter(el=>!el.disabled).map(el=>({id:el.id||el.getAttribute('name')||el.textContent.trim(),width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height})));
  for(const r of sizes)assert.ok(r.width>=43.9&&r.height>=43.9,JSON.stringify(r));return {controls:sizes.length};
 });
 await test('UX-04 select route, inspect computed footprint, and zoom with keyboard',async()=>{
  await page.locator('#next-transect').click();assert.match(await page.locator('#selected-transect-label').textContent(),/02/);
  await page.locator('#toggle-footprint').click();assert.equal(await page.locator('#toggle-footprint').getAttribute('aria-pressed'),'true');
  const footprint=await page.locator('#mission-map svg rect[fill-opacity]').getAttribute('width');assert.ok(Math.abs(Number(footprint)-90)<1e-8);
  const before=await page.locator('#mission-summary').textContent();await page.locator('#mission-map').focus();await page.keyboard.press('+');assert.match(await page.locator('#map-scale').textContent(),/1.25/);await page.keyboard.press('ArrowRight');assert.match(await page.locator('#selected-transect-label').textContent(),/03/);await page.keyboard.press('0');assert.match(await page.locator('#map-scale').textContent(),/1.00/);assert.equal(await page.locator('#mission-summary').textContent(),before);
 });
 await test('UX-04 pointer selection and fit preserve actual settings',async()=>{
  // SVG line has a zero-width geometry box, but a 22px stroked hit region.
  const point=await page.locator('#mission-map [data-transect="5"] .route-hit').evaluate(el=>{const p=el.getPointAtLength(el.getTotalLength()/2).matrixTransform(el.getScreenCTM());return{x:p.x,y:p.y};});
  await page.mouse.click(point.x,point.y);assert.match(await page.locator('#selected-transect-label').textContent(),/06/);await page.locator('#fit-map').click();assert.equal(await page.locator('[name=width]').inputValue(),'360');
 });
 await test('UX-05 mission file menu closes with Escape and restores focus',async()=>{await page.locator('#open-mission-menu').click();assert.equal(await page.locator('#mission-menu').isVisible(),true);await page.keyboard.press('Escape');assert.equal(await page.locator('#mission-menu').isVisible(),false);assert.equal(await page.evaluate(()=>document.activeElement.id),'open-mission-menu');});
 await test('UX-05 stale values show unavailable glyph plus text, not live-looking numbers',async()=>{
  await page.locator('[data-workspace=fly]').click();await page.locator('#open-test-console').click();await page.locator('#pause-telemetry').click();await page.waitForFunction(()=>document.getElementById('link-label').textContent==='Telemetry đã cũ');const values=await page.locator('#telemetry-values .metric strong').allTextContents();assert.deepEqual(values.slice(0,3),['—','—','—']);assert.match(await page.locator('#command-availability').textContent(),/Dữ liệu đã cũ/);await page.screenshot({path:path.join(output,'fly-stale.png')});await page.locator('#pause-telemetry').click();
 });
 await test('UX-06 session reset cancellation preserves session/events',async()=>{
  await page.locator('#reset-rehearsal').click();assert.equal(await page.locator('#new-session-dialog').isVisible(),true);await page.locator('#new-session-dialog button[value=cancel]').click();assert.equal(await page.locator('#new-session-dialog').isVisible(),false);await page.locator('#close-test-console').click();await page.locator('[data-workspace=review]').click();assert.ok(await page.locator('#event-rows tr').count()>1);
 });
 await test('UX-06 mobile parameter sheet traps focus, scrolls advanced inputs and restores context',async()=>{
  await page.setViewportSize({width:390,height:844});await page.locator('[data-workspace=plan]').click();await page.locator('#open-plan-settings').click();assert.equal(await page.locator('#plan-inspector').getAttribute('aria-modal'),'true');await page.locator('#open-fly').focus();await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),'close-plan-settings');await page.locator('.camera-details summary').click();await page.locator('[name=minInterval]').focus();await page.keyboard.press('Tab');const focused=await page.evaluate(()=>{const r=document.activeElement.getBoundingClientRect();return {id:document.activeElement.id||document.activeElement.name,y:r.y,bottom:r.bottom,h:innerHeight};});assert.ok(focused.y>=0&&focused.bottom<=focused.h,JSON.stringify(focused));await page.screenshot({path:path.join(output,'plan-mobile-sheet.png')});await page.keyboard.press('Escape');assert.equal(await page.evaluate(()=>document.activeElement.id),'open-plan-settings');assert.equal(await page.locator('#plan-inspector').isVisible(),false);await page.screenshot({path:path.join(output,'plan-mobile-canvas.png')});
 });
 await test('UX-06 mobile active targets and focus do not shrink',async()=>{
  const bad=await page.locator('button:visible').evaluateAll(els=>els.filter(el=>!el.disabled).map(el=>({id:el.id||el.textContent.trim(),r:el.getBoundingClientRect().toJSON()})).filter(o=>o.r.width<43.9||o.r.height<43.9));assert.deepEqual(bad,[]);
 });
 await test('UX-06 mobile test drawer closes on Escape before command actions',async()=>{await page.locator('[data-workspace=fly]').click();await page.locator('#open-test-console').click();assert.equal(await page.locator('#test-console').getAttribute('aria-modal'),'true');await page.keyboard.press('Escape');assert.equal(await page.locator('#test-console').isVisible(),false);assert.equal(await page.evaluate(()=>document.activeElement.id),'open-test-console');});
 await test('UX-08 rendering has no page overflow or runtime exception',async()=>{for(const [width,height]of[[390,844],[768,1024],[1024,768],[1440,900]]){await page.setViewportSize({width,height});for(const name of ['plan','fly','inspect','review']){await page.locator(`[data-workspace=${name}]`).click();assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&document.documentElement.scrollHeight<=innerHeight),`${width} ${name}`);}}assert.deepEqual(errors,[]);});
}finally{
 await writeFile(path.join(output,'ux-qa.json'),JSON.stringify({checkedAt:new Date().toISOString(),results,errors,scope:'Selected UI criteria on Chromium, not full WCAG conformity, pilot usability or aesthetic acceptance'},null,2)+'\n');await browser.close();
}
