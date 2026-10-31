// Static preparation checks only. This never compiles, launches Android or touches old receipts.
import {readFile,writeFile,readdir,statfs} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {assets} from './server.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex'), checks=[];
const check=(name,pass,detail)=>checks.push({name,pass,detail});
const derivation=JSON.parse(await readFile('native/cockpit66/derivation.json'));
for(const e of derivation.entries){const original=await readFile(e.source),derived=await readFile(e.destination);let reconstructed=original;for(const [a,b] of e.substitutions){const text=reconstructed.toString();if(!text.includes(a))throw Error('DERIVATION_PATTERN_MISSING');reconstructed=Buffer.from(text.split(a).join(b));}check(e.destination,sha(original)===e.sourceSha256&&sha(derived)===e.derivedSha256&&sha(reconstructed)===sha(derived),'source + derived SHA + explicit substitution replay');}
const listed=JSON.parse(await readFile('native/cockpit66/assets.json')).assets,served=await assets();
const java=await readFile('native/cockpit66/src/vn/rtr/aeris/cockpit66/ShellActivity.java','utf8');
const match=java.match(/ASSETS=new HashSet<>\(Arrays\.asList\((.*?)\)\);/);
const native=match?[...match[1].matchAll(/"([^"\n]+)"/g)].map(m=>m[1]):[];
const equal=(a,b)=>JSON.stringify([...a].sort())===JSON.stringify([...b].sort());
check('static asset whitelist',equal(served,listed)&&equal(native,listed)&&new Set(listed).size===23,{served:served.length,native:native.length,manifest:listed.length});
const xml=await readFile('native/cockpit66/AndroidManifest.xml','utf8');
check('manifest has no permissions',!xml.includes('uses-permission'),'No runtime/network/radio permissions declared');
check('wrapper isolation source', ['setAllowFileAccess(false)','setAllowContentAccess(false)','setBlockNetworkLoads(true)','MIXED_CONTENT_NEVER_ALLOW','shouldInterceptRequest','shouldOverrideUrlLoading'].every(s=>java.includes(s))&&!java.includes('addJavascriptInterface'),'Source strings checked, not Android behavior');
check('wrapper lifecycle source',['onPause()','onWindowFocusChanged(boolean focused)','onDestroy()','window.cockpit66Lifecycle'].every(s=>java.includes(s)),'Static presence only');
const lexical=java.replace(/"(?:\\.|[^"\\])*"/g,'""').replace(/\/\*[^]*?\*\//g,'').replace(/\/\/[^\n]*/g,'');
let stack=[],balanced=true;for(const ch of lexical){if('({['.includes(ch))stack.push(ch);else if(')}]'.includes(ch)&&stack.pop()!=='({['[')}]'.indexOf(ch)])balanced=false;}
check('Java lexical delimiter balance',balanced&&stack.length===0,'Not javac, type checking or ART');
async function modules(dir){let result=[];for(const e of await readdir(dir,{withFileTypes:true})){const p=dir+'/'+e.name;if(e.isDirectory())result.push(...await modules(p));else if(p.endsWith('.mjs'))result.push(p);}return result;}
for(const p of await modules('native/cockpit66')){const r=spawnSync(process.execPath,['--check',p],{encoding:'utf8'});check('syntax '+p,r.status===0,r.stderr||'node --check');}
const s=await statfs('.',{bigint:true}),freeBytes=Number(s.bavail*s.bsize);
check('disk floor',freeBytes>=20*1024**3,{freeBytes,floor:20*1024**3});
const result={schema:'cockpit66-host-static/1',status:checks.every(c=>c.pass)?'PASS_HOST_STATIC':'FAIL',checks,androidCompile:'NOT_CHECKED',androidRuntime:'NOT_CHECKED',freeBytes};
await writeFile(process.argv[2]??'evidence/cockpit66/technical-health01.json',JSON.stringify(result,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:result.status,checks:checks.length,freeGiB:freeBytes/1024**3}));if(result.status==='FAIL')process.exitCode=1;
