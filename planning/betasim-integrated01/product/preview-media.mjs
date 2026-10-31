/** Explicit mock-only namespace selection for the retained synthetic media source. */
import fs from'node:fs';import path from'node:path';import{fileURLToPath,pathToFileURL}from'node:url';import{createHash}from'node:crypto';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..'),file=path.join(ROOT,'pilot/beta06g5/media/server.mjs'),hash=b=>createHash('sha256').update(b).digest('hex');
export function projectMediaSource(original){
 let source=original;const before="'evidence/beta06/generation05/'",after="'evidence/betasim-integrated01/product/preview/'";
 if(source.split(before).length!==2)throw Error('PRODUCT_MEDIA_NAMESPACE_ANCHOR');source=source.replace(before,after);
 source=source.replace(/from\s*(['"])(\.[^'"]+)\1/g,(_,q,p)=>'from '+JSON.stringify(new URL(p,pathToFileURL(file)).href));
 source=source.replaceAll('fileURLToPath(import.meta.url)',JSON.stringify(file));
 if(source.split('20n * 1024n ** 3n + 128n * 1024n ** 2n').length!==3)throw Error('PRODUCT_MEDIA_BOTH_GUARD_ANCHORS');
 source=source.replaceAll('20n * 1024n ** 3n + 128n * 1024n ** 2n','10n * 1024n ** 3n + 256n * 1024n ** 2n');
 return{source,projection:{path:'pilot/beta06g5/media/server.mjs',originalSHA256:hash(original),effectiveSHA256:hash(source),scope:'SYNTHETIC_MEDIA_PREVIEW_NOT_ACTUAL_BETA_ACCEPTANCE'}};
}
export async function createBetaMedia(options){
 const original=fs.readFileSync(file,'utf8'),pins=JSON.parse(fs.readFileSync(path.join(ROOT,'evidence/beta06/generation17/flight-pins01.json')));
 if(pins.files['pilot/beta06g5/media/server.mjs']!==hash(original))throw Error('PRODUCT_MEDIA_INPUT_DRIFT');
 const{source,projection}=projectMediaSource(original);
 const mod=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));const media=await mod.createMediaServer(options);return{...media,projection};
}
