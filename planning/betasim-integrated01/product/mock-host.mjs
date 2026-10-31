/** Integrated UI/protocol preview. Deliberately incapable of starting SITL.
 * Source selection is explicit; old sources and all their evidence are read-only.
 * Actual product deployment uses Root's admitted writer/transport adapters.
 */
import fs from'node:fs';import path from'node:path';import{fileURLToPath,pathToFileURL}from'node:url';import{createHash}from'node:crypto';
import'../../../pilot/field02/flight/isolated-loader.mjs';
const REPO=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const evidence='evidence/betasim-integrated01/product/preview/';
const hash=s=>createHash('sha256').update(s).digest('hex');
const records=[];
function project(name,edits=[]){
 const file=path.join(REPO,name),original=fs.readFileSync(file,'utf8');let code=original;
 for(const[a,b]of edits){if(!code.includes(a))throw Error('PRODUCT_PROJECTION_ANCHOR:'+name+':'+a.slice(0,50));code=code.replaceAll(a,b);}
 code=code.replace(/(?:from\s*|import\s*)(['"])(\.[^'"]+)\1/g,(m,q,p)=>m.replace(q+p+q,JSON.stringify(new URL(p,pathToFileURL(file)).href)));
 code=code.replace(/import\((['"])(\.[^'"]+)\1\)/g,(_,q,p)=>'import('+JSON.stringify(new URL(p,pathToFileURL(file)).href)+')');
 code=code.replaceAll('import.meta.url',JSON.stringify(pathToFileURL(file).href));
 records.push({path:name,originalSHA256:hash(original),effectiveSHA256:hash(code),changes:edits.map(([before,after])=>({before,after})),scope:'MOCK_PROTOCOL_PREVIEW_NOT_ACTUAL_RELEASE_ACCEPTANCE'});
 return 'data:text/javascript;base64,'+Buffer.from(code).toString('base64');
}
const pureKml=pathToFileURL(path.join(REPO,'native/native94/assets/offline94/kml.mjs')).href;
const sessionURL=project('pilot/betaworkbench05/session.mjs',[
 ["'evidence/betaworkbench05/'",JSON.stringify(evidence)],
 ["import{parseKml}from'../workbench01/kml.mjs';",`import{parseKml94 as parseKml}from ${JSON.stringify(pureKml)};`],
 ["const{connectOwnedSitl}=await import('./actual-transport.mjs');","const connectOwnedSitl=()=>{throw Error('PREVIEW_ACTUAL_TRANSPORT_FORBIDDEN');};"],
 ["diskFloor();const allowed=", "if(allowSitl)throw Error('PREVIEW_SITL_FORBIDDEN');diskFloor();const allowed="]
]);
const mediaURL=pathToFileURL(path.join(REPO,'planning/betasim-integrated01/product/preview-media.mjs')).href;
const serverURL=project('pilot/betaworkbench05/server.mjs',[
 ["'./session.mjs'",JSON.stringify(sessionURL)],
 ["'./media-projection.mjs'",JSON.stringify(mediaURL)],
 ["'evidence/betaworkbench05/'",JSON.stringify(evidence)],
 ["import{parseKml}from'../workbench01/kml.mjs';",`import{parseKml94 as parseKml}from ${JSON.stringify(pureKml)};`],
 ["if(wb[req.url]){","if(req.url==='/native-bridge.mjs')return send(200,fs.readFileSync("+JSON.stringify(path.join(REPO,'planning/betasim-integrated01/product/native-channel.mjs'))+"),'text/javascript');if(wb[req.url]){"],
 ['native/crew02/assets/fonts/','native/betasim-integrated01/assets/fonts/']
]);
export async function createPreview({out}={}){
 const parent=path.resolve(REPO,evidence);if(!fs.existsSync(parent))fs.mkdirSync(parent,{recursive:true});
 out=path.resolve(out??path.join(parent,'preview-'+Date.now()));if(!out.startsWith(parent+path.sep))throw Error('PRODUCT_PREVIEW_NAMESPACE');
 const {createHost}=await import(serverURL);const host=await createHost({out,allowSitl:false});
 return {...host,projection:structuredClone(records),out,scope:'MOCK_PROTOCOL_PREVIEW_NO_AP_NO_ANDROID_ACCEPTANCE'};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 if(!process.argv.includes('--allow-mock-preview'))throw Error('EXPLICIT_MOCK_PREVIEW_FLAG_REQUIRED');
 const host=await createPreview();console.log(JSON.stringify({...await host.listen(),out:host.out,scope:host.scope}));
 let closing=false;for(const signal of['SIGINT','SIGTERM'])process.once(signal,()=>{if(closing)return;closing=true;host.close().catch(e=>{console.error(e.message);process.exitCode=1;});});
}
