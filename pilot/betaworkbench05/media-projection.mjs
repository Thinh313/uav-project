import fs from'node:fs';import path from'node:path';import{fileURLToPath,pathToFileURL}from'node:url';import{createHash}from'node:crypto';
const R=fileURLToPath(new URL('../../',import.meta.url)),name='pilot/beta06g5/media/server.mjs',P=path.join(R,name),hash=s=>createHash('sha256').update(s).digest('hex');
export async function createBetaMedia(options){
 const pins=JSON.parse(fs.readFileSync(path.join(R,'evidence/beta06/generation17/flight-pins01.json')));const original=fs.readFileSync(P,'utf8');if(pins.files[name]!==hash(original))throw Error('FROZEN_MEDIA_SOURCE_DRIFT');
 let s=original;const a="'evidence/beta06/generation05/'",b="'evidence/betaworkbench05/'";if(s.split(a).length!==2)throw Error('MEDIA_SCOPE_EXACT_COUNT');s=s.replace(a,b);
 if(s.split('fileURLToPath(import.meta.url)').length!==3)throw Error('MEDIA_META_COUNT');s=s.replaceAll('fileURLToPath(import.meta.url)',JSON.stringify(P));
 s=s.replace(/from\s*(['"])(\.[^'"]+)\1/g,(_,q,p)=>'from '+JSON.stringify(new URL(p,pathToFileURL(P)).href));
 s=s.replace('20n * 1024n ** 3n + 128n * 1024n ** 2n','10n * 1024n ** 3n + 256n * 1024n ** 2n').replace('lifetimeMs: 1800000','lifetimeMs: 2700000');
 s=s.replace("return send(200, await fs.readFile(file), filename.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/javascript');","return send(200, filename === 'viewer.mjs' ? await fs.readFile(path.join(REPO,'pilot/betaworkbench05/viewer.mjs')) : await fs.readFile(file), filename.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/javascript');");
 const mod=await import('data:text/javascript;base64,'+Buffer.from(s).toString('base64'));const media=await mod.createMediaServer(options);
 return{...media,projection:{path:name,originalSha256:hash(original),effectiveSha256:hash(s),namespaceOnly:false,policyProjection:"USER_20_10_AND_MATCHED_45MIN_TEST_LIFETIME"}};
}
