/** Exclusive G4 integration pins. No guest, listener or app process is started. */
import'../field02/flight/isolated-loader.mjs';
import fs from'node:fs';import path from'node:path';import{createHash}from'node:crypto';
const{stable}=await import('../auto63/compiler.mjs');
const E='evidence/beta06/generation04/',target=E+'flight-pins.json',previous='evidence/beta06/generation03/flight-pins.json',hash=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
if(fs.existsSync(target))throw Error('EXCLUSIVE_G4_PINS_EXISTS');
const old=JSON.parse(fs.readFileSync(previous)),files={...old.files,[previous]:hash(previous)};
for(const[p,h]of Object.entries(old.files))if(hash(p)!==h)throw Error('IMMUTABLE_G3_PIN_DRIFT:'+p);
function add(dir){for(const n of fs.readdirSync(dir).sort()){const p=path.join(dir,n),s=fs.lstatSync(p);if(s.isSymbolicLink())throw Error('SOURCE_SYMLINK');if(s.isDirectory())add(p);else if(s.isFile())files[p]=hash(p);}}
add('pilot/beta06g4');add('evidence/beta06/generation03');
for(const p of ['planning/beta06g4/TIP-INTEGRATED-RUNTIME04.md','planning/beta06g4/ADR-INTEGRATION04.md','planning/beta06g4/DECISION-OBSERVATION-CADENCE04.md','planning/beta06g3/TIP-READINESS-CORRECTION04.md',E+'workspace-copy02.json',E+'builder-pre-integration-baseline01.json',E+'builder-readiness-correction02.json',E+'qa-correction-final03.json'])files[p]=hash(p);
const baseline=JSON.parse(fs.readFileSync(E+'builder-pre-integration-baseline01.json'));
for(const[p,row]of Object.entries(baseline.files))if(hash(p)!==row.sha256||fs.statSync(p).size!==row.bytes)throw Error('PRE_INTEGRATION_BASELINE_DRIFT:'+p);
const binary='.local/beta06g3/arducopter',binarySHA='1d3479f1fd2b9c6d85c95f38eeb8c105e6735ea1dc372736ddc07efd5162fc41',s=fs.lstatSync(binary);
if(!s.isFile()||s.isSymbolicLink()||(s.mode&0o777)!==0o755||s.size!==7172336||hash(binary)!==binarySHA)throw Error('EXACT_PREPARED_EXECUTABLE_REQUIRED');files[binary]=hash(binary);
const priorGeneration03=[{run:'se15994472d0e479cbaa8',requestSha256:hash('evidence/beta06/generation03/flight/runs/se15994472d0e479cbaa8/request.json'),outcome:'HISTORICAL_FAILED_PREPARATION_CLOSED_NOT_POOLED'}];
if(old.priorSITLRequests?.length!==11||old.priorBetaSITLRequests?.length!==1||old.priorGeneration02SITLRequests?.length!==1)throw Error('EXACT_THIRTEEN_PRIOR_BEFORE_G3');
const helperFile=process.argv[2];if(!helperFile?.startsWith(E)||!helperFile.endsWith('.json'))throw Error('EXPLICIT_CURRENT_HELPER_FREEZE_REQUIRED');
const helper=JSON.parse(fs.readFileSync(helperFile));if(!helper.files||!Object.keys(helper.files).length)throw Error('HELPER_FREEZE_SHAPE');files[helperFile]=hash(helperFile);
for(const[p,v]of Object.entries(helper.files)){const h=typeof v==='string'?v:v.sha256;if(!(p.startsWith('planning/beta06g4/')||p==='pilot/beta06g4/bootstrap.js')||hash(p)!==h||v.bytes!==undefined&&fs.statSync(p).size!==v.bytes)throw Error('HELPER_FREEZE_DRIFT:'+p);files[p]=h;}
const budget={...old.budget,priorGeneration03SITLRequests:1,historicalSITLRequests:14,maxNewSITLRequests:4,refuseNewOrdinal:5,totalBetaMaximum:7,totalHistoricalPlusBetaMaximum:18,generationHostWindows:1,totalBetaHostWindows:4,generationHostProcesses:2,totalBetaHostProcesses:5,managedRestarts:1,generationColdboots:2,totalBetaColdboots:7,hostDeadlineSeconds:2700,APDeadlineSeconds:540,noAutomaticRetry:true};
const manifest={format:'aeris-beta06g4-flight-pins',version:1,previousManifestSha256:hash(previous),qualifiedProfile:{...old.qualifiedProfile,id:'beta06g4-native-arm64-exec-4.7.1',binaryPath:binary,binaryMode:'0755',binaryBytes:7172336},aliases:old.aliases,budget,priorSITLRequests:old.priorSITLRequests,priorBetaSITLRequests:old.priorBetaSITLRequests,priorGeneration02SITLRequests:old.priorGeneration02SITLRequests,priorGeneration03SITLRequests:priorGeneration03,helperFreeze:{path:helperFile,sha256:hash(helperFile)},files};
const bytes=Buffer.from(stable(manifest)+'\n');function put(p,b,mode=0o444){const fd=fs.openSync(p,'wx',mode);try{fs.writeFileSync(fd,b);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}const dir=fs.openSync(path.dirname(p),'r');try{fs.fsyncSync(dir);}finally{fs.closeSync(dir);}}
put(target,bytes);const receipt={status:'PASS_SOURCE_ONLY',manifest:target,sha256:hash(target),bytes:bytes.length,files:Object.keys(files).length,historicalRequests:14,newMaximum:4,budget,actualNewRunsLaunched:0};put(E+'builder-pins-receipt01.json',Buffer.from(JSON.stringify(receipt,null,2)+'\n'),0o600);console.log(JSON.stringify(receipt));
