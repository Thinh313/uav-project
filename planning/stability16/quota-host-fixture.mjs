/** Actual frozen G15 handler, explicit mock roots/physical-admission fixture/disabled flight transport.
 * No G15 entry/guarded listen, no actual campaign, no authentication or journal substitutions.
 */
import fs from 'node:fs';import path from 'node:path';import{registerHooks}from'node:module';import{pathToFileURL}from'node:url';import{createHash}from'node:crypto';
const ROOT=path.resolve('.'),E='evidence/stability16/',url=p=>pathToFileURL(path.join(ROOT,p)).href,sources=new Map();let seq=0;
registerHooks({resolve(u,c,next){if(sources.has(u))return{url:u,shortCircuit:true};return next(u,c);},load(u,c,next){if(sources.has(u))return{format:'module',source:sources.get(u),shortCircuit:true};return next(u,c);}});
function replace(s,a,b){if(s.split(a).length!==2)throw Error('EXACT_QUOTA_HOST_FIXTURE:'+a);return s.replace(a,b);}
function absolute(s,base,overrides={}){return s.replace(/(from\s*|import\()(['"])(\.[^'"]+)\2/g,(m,p,q,n)=>p+q+(overrides[n]??new URL(n,url(base)).href)+q);}
export async function createHostFixture({out}){
 out=path.resolve(out);if(!out.startsWith(path.join(ROOT,E,'builder-quota-')))throw Error('OWNED_STABILITY16_MOCK_ROOT');const id=++seq,appURL=url('planning/stability16/quota-effective-app.mjs')+'?'+id,mediaURL=url('planning/stability16/media/quota-server.mjs')+'?'+id;
 const original=fs.readFileSync('evidence/beta06/generation15/compiled-app.mjs','utf8');let s=original;
 s=replace(s,'FlightBeta06G15 as Flight01','FlightFixture as Flight01');
 s=replace(s,"evidenceRoot:path.join(R,'evidence/beta06/generation15/flight')","evidenceRoot:path.join(out,'fixture-flight')");
 s=s.split('evidence/beta06/generation15/').join(E);
 s=replace(s,"const admission=fs.statfsSync(R);if(admission.bavail*admission.bsize<29*2**30)throw Error('ADMISSION_BELOW_29GIB');","const admission={fixtureOnly:true}; /* physical admission NOT exercised: source/mock fixture only */");
 let media=fs.readFileSync('evidence/beta06/generation15/compiled-media-server.mjs','utf8').split('evidence/beta06/generation15/').join(E);media=absolute(media,'pilot/beta06g5/media/server.mjs');sources.set(mediaURL,media);
 s=absolute(s,'pilot/beta06g5/app.mjs',{'./close-index.mjs':url('pilot/beta06g5r1/mode-index.mjs'),'./workspace-lineage.mjs':url('pilot/beta06g15/workspace-lineage.mjs'),'./flight/adapter.mjs':url('pilot/heartbeat13fix/flight-fixture.mjs'),'./media/server.mjs':mediaURL,'./flight/handoff.mjs':url('pilot/beta06g15/flight/handoff.mjs')});sources.set(appURL,s);
 try{const app=await(await import(appURL)).createBeta06G5({out});return{...app,fixture:{originalSHA256:createHash('sha256').update(original).digest('hex'),effectiveSHA256:createHash('sha256').update(s).digest('hex'),seam:'Mock roots + physical constructor admission excluded + rejecting FlightFixture; real G15 handler/client/session/payload/strict Store/journal/fsync unchanged. No app.listen.'},async close(){try{await app.close();}finally{sources.delete(appURL);sources.delete(mediaURL);}}};}catch(error){sources.delete(appURL);sources.delete(mediaURL);throw error;}
}
