/** Selected Node ESM boundary: one manifest alias map, same held final paths as
 * Python discover(). No unheld fallback, preloads, third-party or network code. */
import{registerHooks}from'node:module';import fs from'node:fs';import path from'node:path';import{fileURLToPath,pathToFileURL}from'node:url';import{createHash}from'node:crypto';
export const canonical=v=>v===null||typeof v!=='object'?JSON.stringify(v):Array.isArray(v)?'['+v.map(canonical).join(',')+']':'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
const hash=b=>createHash('sha256').update(b).digest('hex'),fail=n=>{throw Error('PRODUCT_LOADER_H9_'+n);},own=(o,k)=>Object.hasOwn(o,k),record=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
export function createBoundary(manifest,repo){
 repo=path.resolve(repo);const pins=manifest.productSourceSHA256,closure=manifest.productInputClosure;
 if(!record(pins)||Object.keys(pins).length<3||Object.keys(pins).length>1024||!record(closure)||closure.format!=='aeris-betasim-product-readonly-closure'||closure.version!==1||canonical(closure.pins)!==canonical(pins)||!record(closure.aliases)||closure.dynamicDataModulesAllowed!==false)fail('SOURCE_CLOSURE');
 const aliases=closure.aliases,modules=closure.moduleInputs;
 if(!Array.isArray(modules)||modules.length>1024||new Set(modules).size!==modules.length||Object.keys(aliases).length>32)fail('FINITE_MODULE_ALIAS_SET');
 function relative(n){if(typeof n!=='string'||!n||Buffer.byteLength(n)>512||n.includes('\\')||n.includes('\0')||n.includes('?')||n.includes('#')||path.posix.normalize(n)!==n||n.split('/').some(x=>!x||x==='.'||x==='..')||path.isAbsolute(n)||!n.endsWith('.mjs')&&!n.endsWith('.js'))fail('CANONICAL_MODULE_PATH');return n;}
 function local(filename){filename=path.resolve(filename);const rel=path.relative(repo,filename);relative(rel);if(filename!==path.join(repo,rel))fail('OUTSIDE_REPOSITORY');return rel;}
 function verifyFile(filename){const rel=local(filename);if(!own(pins,rel)||typeof pins[rel]!=='string'||!/^[a-f0-9]{64}$/.test(pins[rel]))fail('MODULE_OUTSIDE_HELD_GRAPH:'+rel);let current=filename;while(current!==path.dirname(current)){if(fs.lstatSync(current).isSymbolicLink())fail('MODULE_SYMLINK');current=path.dirname(current);}const st=fs.statSync(filename);if(!st.isFile()||st.size>2**20)fail('MODULE_FILE_BOUND');const bytes=fs.readFileSync(filename);if(hash(bytes)!==pins[rel])fail('MODULE_SOURCE_DRIFT:'+rel);return bytes;}
 for(const[k,v]of Object.entries(aliases)){relative(k);relative(v);if(k===v||own(aliases,v)||own(pins,k)||!own(pins,v))fail('ALIAS_UNHELD_CHAIN_OR_OLD_FALLBACK');verifyFile(path.join(repo,v));}
 function resolveSpecifier(specifier,parentURL){
  if(typeof specifier!=='string')fail('SPECIFIER_TYPE');if(specifier.startsWith('node:'))return specifier;
  let url;if(specifier.startsWith('file:'))url=new URL(specifier);else if(path.isAbsolute(specifier))url=pathToFileURL(specifier);else if(specifier.startsWith('./')||specifier.startsWith('../')){if(typeof parentURL!=='string'||!parentURL.startsWith('file:'))fail('RELATIVE_PARENT');url=new URL(specifier,parentURL);}else fail('DYNAMIC_OR_BARE_SPECIFIER');
  if(url.protocol!=='file:'||url.search||url.hash||url.host)fail('LOCAL_FILE_URL_ONLY');const original=fileURLToPath(url),rel=local(original),selected=own(aliases,rel)?aliases[rel]:rel,filename=path.join(repo,selected);verifyFile(filename);return pathToFileURL(filename).href;
 }
 return Object.freeze({resolveSpecifier,verifyFile,aliases:Object.freeze({...aliases}),pins:Object.freeze({...pins}),repo});
}
const arg=n=>{const indices=process.argv.flatMap((v,i)=>v===n?[i]:[]);if(indices.length!==1||indices[0]+1>=process.argv.length)fail('ARG:'+n);return process.argv[indices[0]+1];};
if((process.env.NODE_OPTIONS??'').trim()||(process.env.NODE_PATH??'').trim())fail('UNCONTROLLED_NODE_ENV');
const manifestFile=path.resolve(arg('--manifest')),expected=arg('--candidate-sha'),repo=path.resolve(fileURLToPath(new URL('../../..',import.meta.url))),raw=fs.readFileSync(manifestFile),manifest=JSON.parse(raw);
if(!/^[a-f0-9]{64}$/.test(expected)||hash(canonical(manifest))!==expected||raw.toString()!==canonical(manifest)+'\n'||manifest.native?.productKind!=='BETASIM_INTEGRATED'||manifest.simulationOnly!==true)fail('MANIFEST');
export const selectedBoundary=createBoundary(manifest,repo);selectedBoundary.verifyFile(fileURLToPath(import.meta.url));
registerHooks({resolve(specifier,context,nextResolve){if(specifier.startsWith('node:'))return nextResolve(specifier,context);return{url:selectedBoundary.resolveSpecifier(specifier,context.parentURL),shortCircuit:true};},load(url,context,nextLoad){if(url.startsWith('node:'))return nextLoad(url,context);const selected=selectedBoundary.resolveSpecifier(url);if(selected!==url)fail('LOAD_BYPASSED_RESOLVE');selectedBoundary.verifyFile(fileURLToPath(url));return nextLoad(url,context);}});
