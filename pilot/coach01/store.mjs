import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {randomUUID} from 'node:crypto';
import {analyzePackage,receiveReport,verifyReport,hash,stable,POLICY} from './core.mjs';

const ROOT=fileURLToPath(new URL('../../',import.meta.url));
const need=(v,m)=>{if(!v)throw Error(m);};
export function storageBudget(free,used=0,requested=0,admission=false){need([free,used,requested].every(x=>Number.isSafeInteger(x)&&x>=0),'STORAGE_NUMBERS');need(free>=(admission?20*2**30:10*2**30+256*2**20),'DISK_GATE_20_10_GIB');need(used+requested<=256*2**20,'STORE_QUOTA');return true;}
export function diskGuard(admission=false){const s=fs.statfsSync(ROOT),free=s.bavail*s.bsize;storageBudget(free,0,0,admission);return free;}
export class ReportStore{
 constructor(root){
  this.root=path.resolve(root);const allowed=path.join(ROOT,'evidence/coach01');need(this.root.startsWith(allowed+path.sep),'COACH_ISOLATED_STORE');diskGuard();
  fs.mkdirSync(this.root,{recursive:true});need(!fs.lstatSync(this.root).isSymbolicLink(),'STORE_SYMLINK');this.busy=false;
 }
 regular(name,max=34*2**20){need(/^(?:[a-f0-9]{64}\.(?:source|report|receipt)\.json)$/.test(name),'STORE_NAME');const p=path.join(this.root,name),s=fs.lstatSync(p);need(s.isFile()&&!s.isSymbolicLink()&&s.size<=max,'STORE_REGULAR_BOUND');return fs.readFileSync(p);}
 usage(){let total=0;for(const n of fs.readdirSync(this.root)){const p=path.join(this.root,n),s=fs.lstatSync(p);need(s.isFile()&&!s.isSymbolicLink(),'STORE_FOREIGN_MEMBER');total+=s.size;}need(total<=256*2**20,'STORE_QUOTA');return total;}
 write(name,bytes){const free=diskGuard();storageBudget(free,this.usage(),bytes.length);const p=path.join(this.root,name);if(fs.existsSync(p)){need(this.regular(name).equals(bytes),'STORE_COLLISION');return;}
  const temp=path.join(this.root,'.pending-'+randomUUID());const fd=fs.openSync(temp,'wx',0o600);try{fs.writeFileSync(fd,bytes);fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  // link publishes without replacing a pre-existing path. Pending files are retained on failure.
  fs.linkSync(temp,p);fs.unlinkSync(temp);const dir=fs.openSync(this.root,'r');try{fs.fsyncSync(dir);}finally{fs.closeSync(dir);}
 }
 async ingest(bytes){need(!this.busy,'ANALYSIS_BUSY');this.busy=true;try{diskGuard();const report=await analyzePackage(bytes);const source=hash(bytes),id=report.sha256;this.write(source+'.source.json',bytes);this.write(id+'.report.json',Buffer.from(stable(report)));const receipt={format:'coach01-local-receipt',id,sourcePackageSha256:source,run:report.run,policy:report.policy.id,authorityRestorable:false};this.write(id+'.receipt.json',Buffer.from(stable(receipt)));return report;}finally{this.busy=false;}}
 list(){const reports=[],issues=[];for(const n of fs.readdirSync(this.root).filter(n=>n.endsWith('.receipt.json'))){try{const id=n.slice(0,-13);need(/^[a-f0-9]{64}$/.test(id),'RECEIPT_NAME');const receipt=JSON.parse(this.regular(n,4096));need(receipt.id===id&&receipt.authorityRestorable===false,'RECEIPT_SCOPE');const report=JSON.parse(this.regular(id+'.report.json'));need(verifyReport(report)===id&&report.sourcePackageSha256===receipt.sourcePackageSha256&&report.run===receipt.run,'RECEIPT_REPORT');need(report.policy.id===POLICY.id,'OLD_POLICY_REQUIRES_REANALYSIS');const source=this.regular(receipt.sourcePackageSha256+'.source.json');need(hash(source)===receipt.sourcePackageSha256,'STORED_SOURCE_HASH');reports.push({id,run:report.run,name:report.plan.name,source:report.source,accepted:report.sourceAccepted});}catch(e){issues.push({receipt:n,error:e.message});}}
  return{reports,issues,bytes:this.usage(),authorityRestorable:false};
 }
 async get(id){need(/^[a-f0-9]{64}$/.test(id),'REPORT_ID');const receipt=JSON.parse(this.regular(id+'.receipt.json',4096));need(receipt.id===id&&receipt.authorityRestorable===false,'RECEIPT_SCOPE');const bytes=this.regular(id+'.report.json'),r=JSON.parse(bytes);need(r.sha256===id&&r.sourcePackageSha256===receipt.sourcePackageSha256&&r.run===receipt.run,'RECEIPT_REPORT');await receiveReport(bytes,this.regular(receipt.sourcePackageSha256+'.source.json'));return r;}
 image(report,file){need(report.inspection.captures.some(c=>c.file===file),'CAPTURE_ALLOWLIST');const source=JSON.parse(this.regular(report.sourcePackageSha256+'.source.json'));const f=source.files[file],bytes=Buffer.from(f.base64,'base64');need(bytes.length===f.bytes&&hash(bytes)===f.sha256&&bytes.length<=4*2**20,'IMAGE_HASH_BOUND');return bytes;}
}
