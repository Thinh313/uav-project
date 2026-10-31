import {chromium} from '/Users/os/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import {writeFile,readFile} from 'node:fs/promises';
import {createPreview} from './server.mjs';
const dir='evidence/payload21',checks=[],check=(name,ok)=>{checks.push({name,pass:!!ok});if(!ok)throw Error(name);console.log('PASS',name);};
const server=createPreview();await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser;
try{
 const origin=`http://127.0.0.1:${server.address().port}`;
 check('P21-08 no flight/mutation API',(await fetch(origin+'/api/sitl/status')).status===404&&(await fetch(origin+'/',{method:'POST'})).status===405);
 check('P21-08 loopback origin required',(await fetch(origin+'/',{headers:{Origin:'https://example.com'}})).status===403);
 browser=await chromium.launch({headless:true});const context=await browser.newContext({viewport:{width:1280,height:900},acceptDownloads:true}),page=await context.newPage(),errors=[],writes=[],remote=[],assetErrors=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.method()!=='GET')writes.push(r.url());if(!r.url().startsWith(origin))remote.push(r.url());});
 page.on('response',r=>{if(r.status()>=400)assetErrors.push(r.url());});
 await page.goto(origin);await page.waitForSelector('[data-payload=front]');await page.waitForFunction(()=>document.querySelectorAll('#matrix-rows tr').length===12);
 check('P21-06 three heterogeneous synthetic payloads and visible boundary',await page.locator('.payload-choice').count()===3&&(await page.locator('.feed-caption').innerText()).includes('Không có video/ảnh thật'));
 check('P21-03 initial commands disabled',await page.locator('#capture').isDisabled()&&await page.locator('#set-gimbal').isDisabled());
 await page.locator('#acquire').click();await page.locator('#capture').click();await page.waitForFunction(()=>document.querySelector('#command-state').textContent.includes('Đã quan sát phản hồi mô phỏng'));
 check('P21-07 capture produces synthetic receipt only',(await page.locator('#capture-count').innerText()).includes('1 capture receipt tổng hợp · 0 ảnh thật'));
 await page.locator('[data-payload=center]').click();await page.locator('#acquire').click();check('P21-06 unsupported center zoom/focus/gimbal disabled',await page.locator('#set-zoom').isDisabled()&&await page.locator('#focus').isDisabled()&&await page.locator('#nadir').isDisabled());
 await page.locator('[data-payload=front]').click();await page.locator('#stream-select').selectOption('front-ir');check('P21-06 thermal stream retains camera route',(await page.locator('#route-label').innerText()).includes('CAM 100'));
 await page.locator('summary').click();await page.locator('#video-fault').click();check('P21-05 lost feed controls remain independent',await page.locator('#feed-warning').isVisible()&&await page.locator('#capture').isEnabled());
 await page.locator('[data-payload=rear]').click();check('P21-05 other feed remains available',await page.locator('#feed-warning').isHidden());
 await page.locator('[data-payload=front]').click();await page.locator('#gimbal-fault').click();check('P21-05 gimbal fault blocks angles but allows capture',await page.locator('#nadir').isDisabled()&&await page.locator('#capture').isEnabled());
 await page.locator('#gimbal-fault').click();await page.locator('#video-fault').click();
 await page.locator('#reply-mode').selectOption('ack-only');await page.locator('#capture').click();await page.waitForFunction(()=>document.querySelector('#command-state').textContent.includes('ACK chấp nhận'));
 check('P21-04 ACK visibly distinct and no receipt increment',(await page.locator('#capture-count').innerText()).startsWith('1 '));
 await page.waitForFunction(()=>document.querySelector('#command-state').textContent.includes('Hết hạn'));
 check('P21-04 timeout leaves uncertain result without retry',(await page.locator('#capture-count').innerText()).startsWith('1 '));
 await page.locator('#reply-mode').selectOption('none');await page.locator('#payload-loss').click();check('P21-05 disconnect revokes control',await page.locator('#capture').isDisabled());
 await page.locator('#rediscover').click();check('P21-05 rediscovery does not reacquire automatically',await page.locator('#capture').isDisabled()&&await page.locator('#acquire').isEnabled());
 await page.locator('#acquire').click();await page.locator('#mission-authority').click();check('P21-05 mission authority blocks operator',await page.locator('#capture').isDisabled());await page.locator('#acquire').click();
 await page.locator('#set-gimbal').click();await page.waitForFunction(()=>document.querySelector('#command-state').textContent.includes('Đã quan sát phản hồi mô phỏng'));
 check('P21-06 angles update from observation',(await page.locator('#angles').innerText()).includes('-45° / 0°'));
 const downloadPromise=page.waitForEvent('download');await page.locator('#export').click();const download=await downloadPromise,review=JSON.parse(await readFile(await download.path(),'utf8'));
 check('P21-07 exported review has exact synthetic identity/units and no physical media',review.origin==='SIMULATION'&&review.physicalCaptureVerified===false&&review.physicalMedia.length===0&&review.commands.every(c=>c.route.aircraftId==='SIM-HERA'&&c.units.pitchDeg==='degree'));
 await writeFile(dir+'/browser-simulation-review.json',JSON.stringify(review,null,2)+'\n');
 await page.locator('#aircraft-toggle').click();check('P21-05 aircraft loss invalidates all views/control',await page.locator('#capture').isDisabled()&&(await page.locator('#aircraft-mode').innerText()).includes('Mất'));
 await page.locator('#aircraft-toggle').click();check('P21-05 reconnect requires explicit authority and clears historical live conclusion',await page.locator('#capture').isDisabled()&&(await page.locator('#command-state').innerText()).includes('chưa có lệnh'));await page.locator('#acquire').click();
 await page.locator('summary').click();
 for(const width of [1920,1280,1024,800,600,360]){
  await page.setViewportSize({width,height:1000});check(`P21-08 controls fit ${width}px with >=44px targets`,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth&&[...document.querySelectorAll('button,select,input')].filter(e=>e.getClientRects().length).every(e=>{const r=e.getBoundingClientRect();return r.width>=44&&r.height>=44&&r.left>=0&&r.right<=innerWidth;})));
  check(`P21-08 payload selectors aligned ${width}px`,await page.evaluate(()=>{const rows=[...document.querySelectorAll('.payload-choice')].map(b=>b.getBoundingClientRect());return Math.max(...rows.map(r=>r.top))-Math.min(...rows.map(r=>r.top))<1&&Math.max(...rows.map(r=>r.height))-Math.min(...rows.map(r=>r.height))<1;}));
  if(width===1280||width===360)await page.screenshot({path:`${dir}/console-${width}.png`,fullPage:true});
 }
 await page.setViewportSize({width:1280,height:900});await page.locator('#capture').focus();await page.keyboard.press('Tab');check('P21-08 keyboard focus advances to enabled control',await page.evaluate(()=>document.activeElement.tagName==='INPUT'));
 await page.locator('#matrix-tab').click();check('P21-01 matrix has no A/B winner and retains missing gates',(await page.locator('#matrix-view').innerText()).includes('Chưa có phiên A/B')&&await page.locator('#matrix-rows tr').count()===12);await page.screenshot({path:dir+'/matrix.png',fullPage:true});
 check('P21-08 no JS errors, failed assets, external fetch or network command writes',errors.length===0&&writes.length===0&&remote.length===0&&assetErrors.length===0);
 await context.close();
}catch(e){checks.push({name:'browser-error',pass:false,error:e.stack});console.error(e.stack);process.exitCode=1;}finally{await browser?.close();await new Promise(r=>server.close(r));await writeFile(dir+'/browser-qa.json',JSON.stringify({checks,scope:'Actual local browser simulation, not device/native/SITL/video acceptance'},null,2)+'\n');}
