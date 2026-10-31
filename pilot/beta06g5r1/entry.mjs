/** Verified in-process entry only. No live runtime or listener admission is provided. */
import path from'node:path';import{bindMockWorkspace}from'./mode-index.mjs';import{pathToFileURL}from'node:url';import{ROOT,E,installOverlay,verifyOverlay}from'./overlay.mjs';
let factory=null,manifestUsed=null;
export async function createMockCompatibleG5({manifestPath,...options}={}){
 verifyOverlay(manifestPath);
 if(options.allowSITL===true)throw Error('MOCKCOMPAT_NO_SITL_ADMISSION');
 if(!factory){const overlay=installOverlay(manifestPath);globalThis[Symbol.for('aeris.g5.mockcompat.manifest')]=manifestPath;const old=await import(pathToFileURL(path.join(ROOT,'pilot/beta06g5/app.mjs')).href);overlay.assertFreshLoaded();factory=old.createBeta06G5;manifestUsed=manifestPath;}else if(manifestPath!==manifestUsed)throw Error('ONE_VERIFIED_OVERLAY_MANIFEST_PER_PROCESS');
 const app=await factory({...options,allowSITL:false});const connect=app.flight.connect.bind(app.flight);app.flight.connect=async d=>{await app.state();const result=await connect(d);bindMockWorkspace(app.flight.evidenceRoot,path.resolve(options.workspaceRoot??path.join(options.out,'workspace')),result.run);return result;};try{await app.state();}catch{/* Original G5 state latches history uncertainty before exposing controls. */}const refuse=()=>{throw Error('MOCKCOMPAT_SOURCE_REPLAY_ONLY_NO_LISTENER');};app.listen=refuse;app.server.listen=refuse;app.media.listen=refuse;app.media.server.listen=refuse;return app;
}
