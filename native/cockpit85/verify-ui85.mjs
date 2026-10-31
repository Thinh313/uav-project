import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {verifyReview84} from './assets/fly-model84.mjs';
import {validateCapsule44,decode} from './assets/workflow/capsule.mjs';
import {journal82} from '../cockpit82/server.mjs';
const E='evidence/cockpit85',read=n=>JSON.parse(fs.readFileSync(path.join(E,n),'utf8')),sha=b=>createHash('sha256').update(b).digest('hex');
const pins=read('ui-admission-pins02.json');for(const[n,h]of Object.entries(pins.files))assert.equal(sha(fs.readFileSync(n)),h,n);
const checks=[];function check(name,ok){assert(ok,name);checks.push({name,pass:true});}
const names=fs.readdirSync(E),groups=[['release-main-',32],['accept-popup-',144],['accept-panel-',32],['accept-return-',8],['release-alert-',56],['release-history-',24],['release-background-',6]];
const selected=[];
for(const[prefix,count]of groups){const files=names.filter(n=>n.startsWith(prefix)&&n.endsWith('.json')&&!n.endsWith('-text.json'));check(prefix+' exact coverage '+count,files.length===count);for(const f of files){const d=read(f);check(f+' geometry',d.failures.length===0);if(d.delta!==null)check(f+' aligned within 1px',d.delta<=1);if(d.themeIcon)check(f+' theme glyph',d.themeIcon===(d.theme==='day'?'#i-sun':'#i-moon'));const txt=f.replace('.json','-text.json');if(fs.existsSync(path.join(E,txt)))check(txt,read(txt).failures.length===0);selected.push(f);}}
for(const f of ['release-journey-fly.json','release-journey-review.json','release-journey-after-reload.json','release-sitl-disconnected.json']){check(f,read(f).failures.length===0);selected.push(f);}
const before=read('before-fly-1280x720.json');check('before 76px mismatch retained',before.alignmentDelta===76);
check('alignment negative control bites',read('bite-alignment.json').failures.includes('BRAND_METRIC_ALIGNMENT'));
check('overflow negative control bites',read('bite-overflow.json').failures.includes('PANEL_BOUNDS:#task-pane'));
check('video recovery map visible',read('video-recovery.json').mapRecovered&&read('video-recovery.json').videoWarningHidden);
check('panel closes and returns focus',Object.values(read('coordination.json')).every(x=>x===true));
check('reduced material tested',read('reduced-material.json').material==='reduced');
const oldPins=read('ui-admission-pins.json');const changed=Object.keys(oldPins.files).filter(n=>oldPins.files[n]!==pins.files[n]);check('only final video recovery CSS changed after popup matrix',JSON.stringify(changed)===JSON.stringify(['native/cockpit85/assets/layout85.css']));
const fixture=read('history-fixture.json');check('archived source SHA',sha(fs.readFileSync(fixture.source))===fixture.sourceSHA256);let archived=0;
for(const r of Object.values(fixture.records)){const raw=Buffer.from(r.bodyBase64,'base64').toString('utf8');check('archive body SHA '+r.token,sha(raw)===r.sha256);await verifyReview84(JSON.parse(raw),async s=>sha(s));archived++;}check('all five archive records semantic verified',archived===5);
const loaded=await journal82('load',path.resolve('.local/cockpit85/journal'));assert(loaded.ok);const capsule=await validateCapsule44(decode(loaded.bodyBase64));const reviews=capsule.journey.reviews??capsule.journey.workspace?.reviews;
// Capsule validation already checks event replay; retain exact current body and its metadata.
fs.writeFileSync(path.join(E,'host-workspace-verification.json'),JSON.stringify({status:'PASS',scope:'HOST_JAVA_JOURNAL_MOCK_NOT_ANDROID',token:loaded.token,sha256:loaded.sha256,operational:capsule.operational??false,reviewCount:reviews?.length??null,journeyKeys:Object.keys(capsule.journey)},null,2)+'\n');
for(const f of ['controls-regression.json','model-regression.json','workflow-qa-r01.json']){const d=read(f);check(f,d.fail===0||d.status==='PASS');}
check('no console errors in final browser session',read('console-final.json').length===0);
const receipts=selected.map(n=>({file:n,sha256:sha(fs.readFileSync(path.join(E,n)))}));
const result={at:new Date().toISOString(),status:'PASS_BROWSER_UI_SCOPED',sourceManifest:'ui-admission-pins02.json',sourceManifestSHA256:sha(fs.readFileSync(path.join(E,'ui-admission-pins02.json'))),sourceCount:Object.keys(pins.files).length,scenarioReceipts:receipts.length,checks,receipts,scopedReuse:'Popup/panel/return matrix predates final CSS loss-only correction. Exact diff checked; latest full main/alert/history and actual map recovery cover that correction.',notChecked:['Android APK85/emulator','HeraHub physical touch/HID/video','Android SAF/IME/system dialogs','Portrait/below 1024px','OS reduced-motion preference switching','GPU/compositor cost','New SITL flight'],scope:'Browser UI + host JVM mock replay. No flight, APK or production signature; no DJI/Apple certification.'};
fs.writeFileSync(path.join(E,'verification-ui.json'),JSON.stringify(result,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:result.status,checks:checks.length,scenarios:receipts.length,archiveRecords:archived}));
