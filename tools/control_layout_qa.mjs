import {mkdir, writeFile} from 'node:fs/promises';
import {createAppServer} from './server.mjs';

const modulePath = process.env.AERIS_PLAYWRIGHT_MODULE || '/Users/os/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
const {chromium} = await import(modulePath);
const directory = process.env.AERIS_EVIDENCE_DIR || 'evidence/bench06/controls';
await mkdir(directory, {recursive: true});
const checks = [], measurements = [];
const check = (name, pass, detail) => {checks.push({name, pass, ...(detail ? {detail} : {})});};
// Isolated static server: no simulator connection, archive writes or flight commands.
const server = createAppServer({enableSitl: false});
await new Promise((resolve, reject) => {server.once('error', reject); server.listen(0, '127.0.0.1', resolve);});
const origin = `http://127.0.0.1:${server.address().port}`;
let browser;
const posts = [], errors = [];
async function geometry(page) {
  return page.locator('.control-toolbar, .control-group').evaluateAll(groups => groups.filter(g => g.getClientRects().length).map(g => {
    const parent = g.getBoundingClientRect();
    const controls = [...g.children].filter(e => e.getClientRects().length).map(e => {
      const r = e.getBoundingClientRect(), style = getComputedStyle(e), range = document.createRange();
      range.selectNodeContents(e);
      const text = [...range.getClientRects()].filter(r => r.width && r.height);
      return {id: e.id || e.textContent.trim(), x: r.x, y: r.y, width: r.width, height: r.height,
        margin: [style.marginTop, style.marginRight, style.marginBottom, style.marginLeft], radius: style.borderRadius,
        textContained: text.every(t => t.left >= r.left - 1 && t.right <= r.right + 1 && t.top >= r.top - 1 && t.bottom <= r.bottom + 1)};
    });
    return {toolbar: g.classList.contains('control-toolbar'), width: parent.width, x: parent.x, controls};
  }));
}
function violations(groups) {
  const failures = [];
  for (const group of groups) {
    const rows = [];
    for (const control of group.controls) {
      if (control.width < 43.9 || control.height < 43.9) failures.push(`${control.id}: touch area`);
      if (control.x < group.x - .5 || control.x + control.width > group.x + group.width + .5) failures.push(`${control.id}: group overflow`);
      if (!control.textContained) failures.push(`${control.id}: clipped content`);
      if (control.margin.some(m => Math.abs(parseFloat(m)) > .1)) failures.push(`${control.id}: inherited margin`);
      const row = rows.find(r => Math.abs(r[0].y - control.y) <= .5);
      if (row) row.push(control); else rows.push([control]);
      if (group.toolbar && Math.abs(control.height - 44) > .5) failures.push(`${control.id}: toolbar height`);
      if (['zoom-in','zoom-out'].includes(control.id) && Math.abs(control.width - control.height) > .5) failures.push(`${control.id}: icon not square`);
    }
    for (const row of rows) {
      if (Math.max(...row.map(c => c.height)) - Math.min(...row.map(c => c.height)) > .5) failures.push('row: unequal bottom edges');
      if (!group.toolbar && row.length > 1 && Math.max(...row.map(c => c.width)) - Math.min(...row.map(c => c.width)) > .5) failures.push('row: unequal columns');
    }
    // At these widths the toolbar fits on one row. Detect split baselines directly.
    if (group.toolbar && group.width >= 352 && rows.length !== 1) failures.push('toolbar: uneven top edges');
    if (group.toolbar && new Set(group.controls.map(c => c.radius)).size !== 1) failures.push('toolbar: mixed corners');
  }
  return failures;
}
try {
  browser = await chromium.launch({headless: true});
  const page = await browser.newPage({deviceScaleFactor: 2});
  page.on('request', r => {if (r.method() === 'POST') posts.push(r.url());});
  page.on('pageerror', e => errors.push(e.message));
  const viewports = [{width:1440,height:900},{width:1280,height:720},{width:1024,height:768},{width:800,height:480},{width:640,height:360},{width:390,height:844},{width:320,height:640}];
  for (const route of ['/?view=plan','/?view=fly','/qgc.html','/review.html','/native.html','/benchmark.html']) {
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.goto(`${origin}${route}`);
      await page.evaluate(async () => {await document.fonts.ready; document.querySelectorAll('details').forEach(d => d.open = true);});
      await page.waitForTimeout(100);
      const groups = await geometry(page), failures = violations(groups);
      measurements.push({route, viewport, groups});
      check(`shared-control-coverage ${route} ${viewport.width}x${viewport.height}`, await page.locator('.row, .actions, .map-tools, .commands').evaluateAll(es => es.every(e => e.classList.contains('control-group') || e.classList.contains('control-toolbar'))));
      check(`control-geometry ${route} ${viewport.width}x${viewport.height}`, groups.length > 0 && failures.length === 0, failures.join('; '));
      if (route === '/?view=fly' && [1280,390,320].includes(viewport.width)) await page.screenshot({path:`${directory}/fly-${viewport.width}.png`, fullPage:true});
    }
  }
  await page.setViewportSize({width:1280,height:720});
  await page.goto(`${origin}/?view=fly`); await page.evaluate(() => document.fonts.ready);
  await page.locator('.map-tools').screenshot({path:`${directory}/after-toolbar-default.png`});
  const initialDraw = await page.locator('#draw').boundingBox();
  await page.locator('#draw').click();
  const activeDraw = await page.locator('#draw').boundingBox();
  check('drawing label keeps the same control box', initialDraw.width === activeDraw.width && violations(await geometry(page)).length === 0);
  await page.locator('#draw').click();
  await page.locator('.toolbar-toggle > span').click();
  check('DSM label activates checkbox', await page.locator('#dsm-layer').isChecked());
  await page.locator('#dsm-layer').focus();
  check('DSM keyboard focus visible around whole control', await page.locator('.toolbar-toggle').evaluate(e => getComputedStyle(e).outlineStyle !== 'none'));
  check('checkbox centered in control', await page.locator('.toolbar-toggle').evaluate(e => {const a=e.getBoundingClientRect(),b=e.firstElementChild.getBoundingClientRect();return Math.abs((a.top+a.bottom-b.top-b.bottom)/2)<.5;}));
  await page.locator('.map-tools').screenshot({path:`${directory}/after-toolbar.png`});
  // Adversarial checks: reproduce the reported cascade bug and another width regression.
  await page.locator('.toolbar-toggle').evaluate(e => e.style.marginBottom = '13px');
  const marginFailures = violations(await geometry(page));
  check('gate detects original form-label margin regression', marginFailures.some(v => v.includes('inherited margin') || v.includes('uneven top edges')), marginFailures.join('; '));
  await page.locator('.toolbar-toggle').evaluate(e => e.style.removeProperty('margin-bottom'));
  await page.locator('#zoom-in').evaluate(e => {e.style.width = '36px'; e.style.minWidth = '36px';});
  const iconFailures = violations(await geometry(page));
  check('gate detects icon touch-area regression', iconFailures.some(v => v.includes('icon not square') || v.includes('touch area')), iconFailures.join('; '));
  await page.locator('#zoom-in').evaluate(e => {e.style.removeProperty('width'); e.style.removeProperty('min-width');});
  check('restored geometry passes after regression injections', violations(await geometry(page)).length === 0);
  await page.goto(`${origin}/?view=plan`);
  await page.locator('#offline-details > summary').click();
  await page.locator('#install-offline').click();
  await page.waitForFunction(() => !!navigator.serviceWorker.controller);
  check('shared stylesheet included in offline package', await page.evaluate(async () => !!await caches.match('/controls.css')));
  await page.context().setOffline(true);
  for (const route of ['/?view=fly','/qgc.html','/review.html','/native.html','/benchmark.html']) {
    await page.goto(`${origin}${route}`); await page.evaluate(() => document.fonts.ready);
    check(`offline control geometry ${route}`, violations(await geometry(page)).length === 0);
  }
  await page.context().setOffline(false);
  check('no JavaScript errors', errors.length === 0, errors.join('; '));
  check('no POST requests or flight mutations', posts.length === 0, posts.join('; '));
} catch (error) {check('runner completed', false, error.stack);}
finally {
  await browser?.close();
  await new Promise(resolve => server.close(resolve));
  const report = {scope:'Chromium CSS geometry and local interactions; simulator disabled, no HeraHub hardware', checks, measurements};
  await writeFile(`${directory}/controls-qa.json`, JSON.stringify(report,null,2)+'\n');
}
const failed = checks.filter(c => !c.pass);
console.log(JSON.stringify({pass:checks.length-failed.length, fail:failed.length, failures:failed},null,2));
if (failed.length) process.exitCode = 1;
