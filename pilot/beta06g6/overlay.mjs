/** Runtime sibling: exact G5 transforms, independently pinned original/effective bytes. */
import{stable}from'../mapping51/common.mjs';import fs from'node:fs';import path from'node:path';import{fileURLToPath,pathToFileURL}from'node:url';import{registerHooks}from'node:module';import{createHash}from'node:crypto';
import{RECIPES as R1,boundedFile,verifyOverlay as verifyR1}from'../beta06g5r1/overlay.mjs';
export{boundedFile};export const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),E='evidence/beta06/generation06/',R1E='evidence/beta06/generation05-mockcompat01/';
export const NEW_FILES=Object.freeze(['entry.mjs','overlay.mjs','flight/adapter.mjs','flight/runtime.py','flight/handoff.mjs','flight/receive-flight.mjs','flight/qualified/profile.mjs','flight/qualified/link.mjs','flight/qualified/mock.mjs','flight/qualified/verify-profile.mjs','workspace-lineage.mjs','pins.mjs','freeze.mjs'].map(n=>'pilot/beta06g6/'+n));
export const RECIPES=Object.freeze({...Object.fromEntries(Object.entries(R1).map(([p,rows])=>[p,rows.map(r=>({...r,to:r.to.split(R1E).join(E)}))])),
 'pilot/beta06g5/app.mjs':[...R1['pilot/beta06g5/app.mjs'].map(r=>({...r,to:r.to.split(R1E).join(E)})),{from:'FlightBeta06G5 as Flight01',to:'FlightBeta06G6 as Flight01',count:1},{from:'BETA06G5_HOST_SOURCE_ANDROID_RECEIVER',to:'BETA06G6_HOST_SOURCE_ANDROID_RECEIVER',count:1}],
 'pilot/beta06g5/flight/base.mjs':[...R1['pilot/beta06g5/flight/base.mjs'].map(r=>({...r,to:r.to.split(R1E).join(E)})),{from:'beta06g5',to:'beta06g6',count:3}],
 'pilot/beta06g5/evidence/delivery-set.mjs':[{from:"'evidence/beta06/generation05'",to:"'evidence/beta06/generation06'",count:1}]
});
export const sha=b=>createHash('sha256').update(b).digest('hex');
export function transform(p,source){for(const r of RECIPES[p]??[]){const a=source.split(r.from);if(a.length-1!==r.count)throw Error('EXACT_G6_REPLACEMENT_COUNT:'+p);source=a.join(r.to);}return source;}
const sameKeys=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&JSON.stringify(Object.keys(v).sort())===JSON.stringify([...keys].sort());
export function verifyOverlay(manifestPath=path.join(ROOT,E,'flight-pins.json')){
 if(!path.isAbsolute(manifestPath)||path.resolve(manifestPath)!==manifestPath||manifestPath!==path.join(ROOT,E,'flight-pins.json'))throw Error('EXACT_G6_MANIFEST_PATH');
 const m=JSON.parse(boundedFile(manifestPath,256*1024)),oldBytes=boundedFile(path.join(ROOT,'evidence/beta06/generation05/flight-pins.json')),old=JSON.parse(oldBytes);
 if(m.format!=='aeris-beta06g6-flight-pins'||m.previousManifestSha256!==sha(oldBytes)||Object.keys(old.files).length!==700||m.budget?.maxNewSITLRequests!==4||m.budget.hostDeadlineSeconds!==2700||m.budget.APDeadlineSeconds!==540||m.priorGeneration05SITLRequests?.length!==0)throw Error('G6_MANIFEST_SCHEMA');
 const r1=verifyR1(path.join(ROOT,R1E,'overlay-pins08.json'));for(const[p,h]of Object.entries(r1.files))if(m.files?.[p]!==h)throw Error('R1_LOADED_SOURCE_PIN_REQUIRED:'+p);
 if(m.mockCompatibility?.manifestSha256!==sha(boundedFile(path.join(ROOT,R1E,'overlay-pins08.json'))))throw Error('FROZEN_R1_OVERLAY08_REQUIRED');
 if(stable(m.overlay?.recipe)!==stable(RECIPES)||!sameKeys(m.overlay.compiled,Object.keys(RECIPES)))throw Error('EXACT_G6_RECIPE_SET');
 for(const[p,h]of Object.entries(old.files))if(m.files?.[p]!==h||sha(boundedFile(path.join(ROOT,p),32*1024*1024))!==h)throw Error('ORIGINAL700_PIN_DRIFT:'+p);
 for(const p of NEW_FILES)if(!m.files?.[p])throw Error('MISSING_G6_MODULE_PIN:'+p);
 for(const[p,h]of Object.entries(m.files??{})){if(path.isAbsolute(p)||p.split('/').some(x=>!x||x==='.'||x==='..')||!/^[a-f0-9]{64}$/.test(h)||sha(boundedFile(path.join(ROOT,p),32*1024*1024))!==h)throw Error('G6_SOURCE_PIN_DRIFT:'+p);}
 for(const[p,row]of Object.entries(m.overlay.compiled)){const artifact=E+'compiled-'+p.split('/').slice(2).join('-');if(row.artifact!==artifact||m.files[artifact]!==row.compiledSha256||sha(boundedFile(path.join(ROOT,p)))!==row.originalSha256||sha(transform(p,boundedFile(path.join(ROOT,p)).toString()))!==row.compiledSha256)throw Error('G6_COMPILED_SOURCE_SHA:'+p);}
 return m;
}
export function installOverlay(manifestPath){const m=verifyOverlay(manifestPath),loaded=new Set(),urls=new Map(Object.keys(RECIPES).map(p=>[pathToFileURL(path.join(ROOT,p)).href,p]));if(globalThis[Symbol.for('aeris.g6.overlay')])throw Error('G6_SINGLE_INSTALL_REQUIRED');globalThis[Symbol.for('aeris.g6.overlay')]=true;
 const app=pathToFileURL(path.join(ROOT,'pilot/beta06g5/app.mjs')).href,redirects=new Map([['pilot/beta06g5/flight/adapter.mjs','pilot/beta06g6/flight/adapter.mjs'],['pilot/beta06g5/close-index.mjs','pilot/beta06g5r1/mode-index.mjs'],['pilot/beta06g5/workspace-lineage.mjs','pilot/beta06g6/workspace-lineage.mjs'],['pilot/beta06g5/flight/handoff.mjs','pilot/beta06g6/flight/handoff.mjs']].map(([a,b])=>[pathToFileURL(path.join(ROOT,a)).href,pathToFileURL(path.join(ROOT,b)).href]));
 registerHooks({resolve(specifier,context,next){if(context.parentURL===app){const target=new URL(specifier,context.parentURL).href;if(redirects.has(target))return next(redirects.get(target),context);}return next(specifier,context);},load(url,context,next){const result=next(url,context),p=urls.get(url);if(!p)return result;if(loaded.has(url))throw Error('G6_DUPLICATE_MODULE_LOAD');const source=typeof result.source==='string'?result.source:Buffer.from(result.source).toString(),row=m.overlay.compiled[p];if(sha(source)!==row.originalSha256)throw Error('G6_LOADED_ORIGINAL_SHA');const effective=transform(p,source);if(sha(effective)!==row.compiledSha256)throw Error('G6_EFFECTIVE_SOURCE_SHA');loaded.add(url);return{...result,source:effective};}});
 return{assertFreshLoaded(){// delivery-set is a lazy import; its preloaded form is checked before export below.
 const required=[...urls].filter(([,p])=>!p.endsWith('/delivery-set.mjs'));if(required.some(([u])=>!loaded.has(u)))throw Error('G6_PRELOADED_MODULE_OR_CACHE_AMBIGUITY');},assertDeliveryLoaded(){const u=pathToFileURL(path.join(ROOT,'pilot/beta06g5/evidence/delivery-set.mjs')).href;if(!loaded.has(u))throw Error('G6_DELIVERY_MODULE_CACHE_AMBIGUITY');}};
}
