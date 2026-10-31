/** Exact allowlisted source/mock revision; original G5 files remain immutable. */
import fs from'node:fs';import path from'node:path';import{fileURLToPath,pathToFileURL}from'node:url';import{createHash}from'node:crypto';import{registerHooks}from'node:module';
export const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),E='evidence/beta06/generation05-mockcompat01/';
const sha=b=>createHash('sha256').update(b).digest('hex');
export const RECIPES=Object.freeze({
 'pilot/beta06g5/app.mjs':[{from:"'evidence/beta06/generation05/'",to:"'"+E+"'",count:2},{from:"'evidence/beta06/generation05/flight'",to:"'"+E+"flight'",count:1},
 {from:'archiveCompletedClose,reviewHistory,persistCloseOutcome}',to:'archiveCompletedClose,reviewHistory,persistCloseOutcome,notePostEffectFailure,assertWorkspaceOutcomes,noteCommandResponse}',count:1},
 {from:'let responseActionId=null,postEffectResult=null;',to:'let responseActionId=null,responseFlightAction=null,postEffectResult=null;',count:1},
 {from:'responseActionId=uiActionId;delete q.uiActionId;',to:"responseActionId=uiActionId;responseFlightAction=route==='flight'?q.action:null;delete q.uiActionId;",count:1},
 {from:'res.end(b);};',to:"res.end(b);if(type==='application/json'&&v?.result?.closeIndex?.status==='CLOSED_REVIEW_INDEXED')noteCommandResponse(flight.evidenceRoot,v.result.closeIndex,{route:req.url,action:responseFlightAction,uiActionId:responseActionId});};",count:1},
 {from:'async function state(){client.tick();',to:"async function state(){try{assertWorkspaceOutcomes(flight.evidenceRoot,workspaceRoot,store.records(),flight.state().run);}catch(e){campaignFailure={status:'MOCK_CLOSE_OUTCOME_UNKNOWN_BLOCKED',error:String(e.message).slice(0,160),automaticRetry:false,campaignContinuationAllowed:false};throw e;}client.tick();",count:1},
 {from:'async function action(route,q){',to:"async function action(route,q){try{assertWorkspaceOutcomes(flight.evidenceRoot,workspaceRoot,store.records(),flight.state().run);}catch(e){campaignFailure={status:'MOCK_CLOSE_OUTCOME_UNKNOWN_BLOCKED',error:String(e.message).slice(0,160),automaticRetry:false,campaignContinuationAllowed:false};}",count:1},
 {from:"error:'OUTCOME_PERSISTENCE:'+String(e.message).slice(0,120)};",to:"error:'OUTCOME_PERSISTENCE:'+String(e.message).slice(0,120)};notePostEffectFailure(flight.evidenceRoot,archived.closeIndex);",count:1},
 {from:"error:'POST_EFFECT_RESPONSE_OR_JOURNAL:'+String(e.message).slice(0,100)};",to:"error:'POST_EFFECT_RESPONSE_OR_JOURNAL:'+String(e.message).slice(0,100)};notePostEffectFailure(flight.evidenceRoot,campaignFailure);",count:1}],
 'pilot/beta06g5/flight/base.mjs':[{from:"'evidence/beta06/generation05/flight'",to:"'"+E+"flight'",count:2}],
 'pilot/beta06g5/media/server.mjs':[{from:"'evidence/beta06/generation05/'",to:"'"+E+"'",count:1}]
});
export function transform(name,source){for(const r of RECIPES[name]??[]){const parts=source.split(r.from);if(parts.length-1!==r.count)throw Error('OVERLAY_EXACT_REPLACEMENT_COUNT:'+name+':'+r.from);source=parts.join(r.to);}return source;}
export const NEW_FILES=Object.freeze(['entry.mjs','overlay.mjs','flight-overlay.mjs','mode-index.mjs','mock-review.mjs'].map(n=>'pilot/beta06g5r1/'+n));
export function boundedFile(p,max=1024*1024){
 const absolute=path.resolve(p);let current=path.parse(absolute).root;
 for(const part of absolute.slice(current.length).split('/').filter(Boolean).slice(0,-1)){current=path.join(current,part);const s=fs.lstatSync(current);if(!s.isDirectory()||s.isSymbolicLink())throw Error('REGULAR_PARENT_REQUIRED');}
 const fd=fs.openSync(absolute,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW);try{const s=fs.fstatSync(fd);if(!s.isFile()||s.size<0||s.size>max)throw Error('REGULAR_FILE_BOUND');const bytes=fs.readFileSync(fd);if(bytes.length!==s.size||fs.fstatSync(fd).size!==s.size)throw Error('FILE_CHANGED');return bytes;}finally{fs.closeSync(fd);}
}
const sameKeys=(v,keys)=>v&&typeof v==='object'&&!Array.isArray(v)&&JSON.stringify(Object.keys(v).sort())===JSON.stringify([...keys].sort());
export function verifyOverlay(manifestPath){
 if(typeof manifestPath!=='string'||!path.isAbsolute(manifestPath)||path.resolve(manifestPath)!==manifestPath||!manifestPath.startsWith(path.join(ROOT,E)))throw Error('EXPLICIT_OWNED_OVERLAY_MANIFEST_REQUIRED');
 const m=JSON.parse(boundedFile(manifestPath,256*1024));if(m.format!=='aeris-g5-mockcompat-overlay-pins'||m.scope!=='SOURCE_MOCK_REPLAY_ONLY_NO_LISTEN_NO_AP')throw Error('OVERLAY_MANIFEST_SCOPE');
 const oldPath=path.join(ROOT,'evidence/beta06/generation05/flight-pins.json'),oldBytes=boundedFile(oldPath),old=JSON.parse(oldBytes);if(sha(oldBytes)!==m.originalManifestSha256||Object.keys(old.files).length!==700)throw Error('EXACT_ORIGINAL_700_PINS_REQUIRED');
 if(!sameKeys(m.files,NEW_FILES))throw Error('EXACT_NEW_OWNED_SOURCE_SET_REQUIRED');
 for(const files of [old.files,m.files])for(const[p,h]of Object.entries(files)){if(!/^[a-f0-9]{64}$/.test(h)||path.isAbsolute(p)||p.split('/').some(x=>!x||x==='.'||x==='..'))throw Error('SAFE_PIN_PATH_SHA_REQUIRED');if(sha(boundedFile(path.join(ROOT,p),32*1024*1024))!==h)throw Error('OVERLAY_SOURCE_PIN_DRIFT:'+p);}
 if(JSON.stringify(m.recipe)!==JSON.stringify(RECIPES)||!sameKeys(m.compiled,Object.keys(RECIPES)))throw Error('EXACT_OVERLAY_RECIPE_REQUIRED');
 for(const[p,row]of Object.entries(m.compiled)){const b=boundedFile(path.join(ROOT,p));if(row.artifact!==E+path.basename(manifestPath,'.json')+'-'+p.split('/').slice(2).join('-')||sha(boundedFile(path.join(ROOT,row.artifact)))!==row.compiledSha256||sha(b)!==row.originalSha256||sha(transform(p,b.toString()))!==row.compiledSha256)throw Error('OVERLAY_COMPILED_SOURCE_SHA:'+p);}
 return m;
}
export function installOverlay(manifestPath){const m=verifyOverlay(manifestPath),loaded=new Set(),urls=new Map(Object.keys(RECIPES).map(p=>[pathToFileURL(path.join(ROOT,p)).href,p]));if(globalThis[Symbol.for('aeris.g5.mockcompat.overlay')])throw Error('OVERLAY_SINGLE_INSTALL_REQUIRED');globalThis[Symbol.for('aeris.g5.mockcompat.overlay')]=true;
 const appURL=pathToFileURL(path.join(ROOT,'pilot/beta06g5/app.mjs')).href,adapterURL=pathToFileURL(path.join(ROOT,'pilot/beta06g5/flight/adapter.mjs')).href,closeURL=pathToFileURL(path.join(ROOT,'pilot/beta06g5/close-index.mjs')).href;
 registerHooks({resolve(specifier,context,next){if(context.parentURL===appURL){const target=new URL(specifier,context.parentURL).href;if(target===adapterURL)return next(pathToFileURL(path.join(ROOT,'pilot/beta06g5r1/flight-overlay.mjs')).href,context);if(target===closeURL)return next(pathToFileURL(path.join(ROOT,'pilot/beta06g5r1/mode-index.mjs')).href,context);}return next(specifier,context);},load(url,context,next){const result=next(url,context),name=urls.get(url);if(!name)return result;if(loaded.has(url))throw Error('OVERLAY_MODULE_DUPLICATE_LOAD');const source=typeof result.source==='string'?result.source:Buffer.from(result.source).toString(),row=m.compiled[name];if(!row||sha(source)!==row.originalSha256)throw Error('OVERLAY_LOADED_ORIGINAL_SHA');const compiled=transform(name,source);if(sha(compiled)!==row.compiledSha256)throw Error('OVERLAY_EFFECTIVE_COMPILED_SHA');loaded.add(url);return{...result,source:compiled};}});
 return{assertFreshLoaded(){if(loaded.size!==urls.size)throw Error('OVERLAY_PRELOADED_MODULE_OR_CACHE_AMBIGUITY');},manifest:m};
}
