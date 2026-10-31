/** Exclusive G4 integration pins. No guest, listener or app process is started. */
import'../field02/flight/isolated-loader.mjs';
import fs from'node:fs';import path from'node:path';import{createHash}from'node:crypto';
const{stable}=await import('../auto63/compiler.mjs');
const E='evidence/beta06/generation05/',target=E+'flight-pins.json',previous='evidence/beta06/generation04/flight-pins.json',hash=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
if(fs.existsSync(target))throw Error('EXCLUSIVE_G5_PINS_EXISTS');
const old=JSON.parse(fs.readFileSync(previous)),files={...old.files,[previous]:hash(previous)};
for(const[p,h]of Object.entries(old.files))if(hash(p)!==h)throw Error('IMMUTABLE_G4_PIN_DRIFT:'+p);
function add(dir){for(const n of fs.readdirSync(dir).sort()){const p=path.join(dir,n),s=fs.lstatSync(p);if(s.isSymbolicLink())throw Error('SOURCE_SYMLINK');if(s.isDirectory())add(p);else if(s.isFile())files[p]=hash(p);}}
add('pilot/beta06g5');for(const p of ['pilot/beta06g4r2/sealed-flight-close.mjs','planning/beta06g4r2/complete_nominal_policy.py'])files[p]=hash(p);
for(const p of ['planning/beta06g5/TIP-INTEGRATED-CLOSE05.md','planning/beta06g5/ADR-CLOSE-INTEGRATION05.md',E+'workspace-copy01.json',E+'qa-preservation-before05.json',E+'qa-workspace-copy05.json'])files[p]=hash(p);
const binary='.local/beta06g3/arducopter',binarySHA='1d3479f1fd2b9c6d85c95f38eeb8c105e6735ea1dc372736ddc07efd5162fc41',s=fs.lstatSync(binary);
if(!s.isFile()||s.isSymbolicLink()||(s.mode&0o777)!==0o755||s.size!==7172336||hash(binary)!==binarySHA)throw Error('EXACT_PREPARED_EXECUTABLE_REQUIRED');files[binary]=hash(binary);
const g4Request='evidence/beta06/generation04/flight/runs/sfae933b8b0fe4d6192c5/request.json';files[g4Request]=hash(g4Request);const priorGeneration04=[{run:'sfae933b8b0fe4d6192c5',requestSha256:hash(g4Request),outcome:'HISTORICAL_RAW_PASS_CAMPAIGN_FAILED_CLOSE_INDEX_NOT_POOLED'}];
if(old.priorSITLRequests?.length!==11||old.priorBetaSITLRequests?.length!==1||old.priorGeneration02SITLRequests?.length!==1||old.priorGeneration03SITLRequests?.length!==1)throw Error('EXACT_FOURTEEN_PRIOR_BEFORE_G4');
const helperFile=process.argv[2];if(!helperFile?.startsWith(E)||!helperFile.endsWith('.json'))throw Error('EXPLICIT_CURRENT_HELPER_FREEZE_REQUIRED');
const helper=JSON.parse(fs.readFileSync(helperFile));if(!helper.files||!Object.keys(helper.files).length)throw Error('HELPER_FREEZE_SHAPE');files[helperFile]=hash(helperFile);
for(const[p,v]of Object.entries(helper.files)){const h=typeof v==='string'?v:v.sha256;if(!(p.startsWith('planning/beta06g5/')||p==='planning/beta06g4r2/complete_nominal_policy.py')||hash(p)!==h||v.bytes!==undefined&&fs.statSync(p).size!==v.bytes)throw Error('HELPER_FREEZE_DRIFT:'+p);files[p]=h;}
const budget={...old.budget,priorGeneration04SITLRequests:1,historicalSITLRequests:15,maxNewSITLRequests:4,refuseNewOrdinal:5,totalBetaMaximum:8,totalHistoricalPlusBetaMaximum:19,generationHostWindows:1,totalBetaHostWindows:5,generationHostProcesses:2,totalBetaHostProcesses:7,managedRestarts:1,generationColdboots:2,totalBetaColdboots:9,hostDeadlineSeconds:2700,APDeadlineSeconds:540,noAutomaticRetry:true};
const manifest={format:'aeris-beta06g5-flight-pins',version:1,previousManifestSha256:hash(previous),qualifiedProfile:{...old.qualifiedProfile,id:'beta06g5-native-arm64-exec-4.7.1',binaryPath:binary,binaryMode:'0755',binaryBytes:7172336},aliases:old.aliases,budget,priorSITLRequests:old.priorSITLRequests,priorBetaSITLRequests:old.priorBetaSITLRequests,priorGeneration02SITLRequests:old.priorGeneration02SITLRequests,priorGeneration03SITLRequests:old.priorGeneration03SITLRequests,priorGeneration04SITLRequests:priorGeneration04,helperFreeze:{path:helperFile,sha256:hash(helperFile)},files};
const bytes=Buffer.from(stable(manifest)+'\n');function put(p,b,mode=0o444){const fd=fs.openSync(p,'wx',mode);try{fs.writeFileSync(fd,b);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}const dir=fs.openSync(path.dirname(p),'r');try{fs.fsyncSync(dir);}finally{fs.closeSync(dir);}}
put(target,bytes);const receipt={status:'PASS_SOURCE_ONLY',manifest:target,sha256:hash(target),bytes:bytes.length,files:Object.keys(files).length,historicalRequests:15,newMaximum:4,budget,actualNewRunsLaunched:0};put(E+'builder-pins-receipt01.json',Buffer.from(JSON.stringify(receipt,null,2)+'\n'),0o600);console.log(JSON.stringify(receipt));
