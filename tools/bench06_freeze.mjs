import {readdir,readFile,writeFile,mkdir} from 'node:fs/promises';
import {createHash,randomUUID} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {validateBenchmarkSuite,validateBenchmarkFreeze,sealBenchmark,EXPECTED_SITL_ARGV} from '../app/core/benchmark.mjs';
import {digest,BUILD} from '../app/core/execution-record.mjs';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
export async function sourceFiles(){const files={};async function walk(dir){for(const e of (await readdir(dir,{withFileTypes:true})).sort((a,b)=>a.name.localeCompare(b.name))){const path=dir+'/'+e.name;if(e.isDirectory())await walk(path);else if(e.isFile())files[path]=hash(await readFile(path));}}await walk('app');await walk('services');for(const p of ['package.json','tools/bench06_sitl_qa.mjs','tools/bench06_freeze.mjs','tools/build_bench06_suite.mjs','tools/recovery07_sitl_qa.mjs','tools/journal08_sitl_qa.mjs','tools/journal08_worker.mjs','tools/journal08_qa.mjs','tools/handoff09_sitl_qa.mjs','tools/handoff09_fault_qa.mjs','tools/handoff09_worker.mjs'])files[p]=hash(await readFile(p));return files;}
export async function makeFreeze(){
 const suite=await validateBenchmarkSuite(await readFile('app/fixtures/bench06/suite.json','utf8'));
 const container=JSON.parse(execFileSync('docker',['inspect','aeris-sitl'],{encoding:'utf8'}))[0];
 const port=container.HostConfig.PortBindings?.['5760/tcp'];
 if(!container.State.Running||JSON.stringify(container.Config.Cmd)!==JSON.stringify(EXPECTED_SITL_ARGV)||port?.length!==1||port[0].HostIp!=='127.0.0.1'||port[0].HostPort!=='5760')throw Error('Dedicated normal loopback SITL configuration required; refusing to reconfigure an existing container.');
 const files=await sourceFiles(),build={version:JSON.parse(await readFile('package.json','utf8')).version,label:BUILD,files,sha256:await digest(files)};
 const runtime={kind:'dedicated-loopback-sitl',firmware:'4.7.1',binarySha256:hash(await readFile('runtime/sitl/arducopter')),defaults:Object.fromEntries(await Promise.all(['copter.parm','aeris.parm'].map(async p=>[p,hash(await readFile('runtime/sitl/'+p))]))),imageId:container.Image,argv:container.Config.Cmd,model:'quad',speedup:5,world:suite.world,profile:suite.profile,resetPolicy:'observed-disarmed-restart-before-each-trial'};
 const freeze=await sealBenchmark({format:'aeris-benchmark-freeze',version:1,id:randomUUID(),createdAt:new Date().toISOString(),suiteSha256:suite.sha256,build,runtime});await validateBenchmarkFreeze(freeze,suite);return {suite,freeze};
}
export async function assertCurrentFreeze(freeze){const files=await sourceFiles();if(await digest(files)!==freeze.build.sha256)throw Error('Source bytes changed after pre-run freeze.');const c=JSON.parse(execFileSync('docker',['inspect','aeris-sitl'],{encoding:'utf8'}))[0];if(c.Image!==freeze.runtime.imageId||JSON.stringify(c.Config.Cmd)!==JSON.stringify(freeze.runtime.argv))throw Error('Runtime image/command changed after freeze.');for(const p of Object.keys(freeze.runtime.defaults))if(hash(await readFile('runtime/sitl/'+p))!==freeze.runtime.defaults[p])throw Error('Simulator defaults changed.');if(hash(await readFile('runtime/sitl/arducopter'))!==freeze.runtime.binarySha256)throw Error('Simulator binary changed.');}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){const {freeze}=await makeFreeze(),dir=process.env.AERIS_EVIDENCE_DIR||'evidence/bench06';await mkdir(dir,{recursive:true});await writeFile(dir+'/freeze.json',JSON.stringify(freeze,null,2)+'\n');console.log(JSON.stringify({id:freeze.id,sha256:freeze.sha256,buildSha256:freeze.build.sha256,files:Object.keys(freeze.build.files).length}));}
