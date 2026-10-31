import fs from'node:fs';
import path from'node:path';
import crypto from'node:crypto';
import{fileURLToPath}from'node:url';
const need=(value,reason)=>{if(!value)throw Error(reason);};
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),realRoot=fs.realpathSync(root);
const manifest=JSON.parse(fs.readFileSync(path.join(root,'handoff/SOURCE-MANIFEST.json')));
need(manifest.format==='uav-project-public-source-manifest'&&manifest.version===1&&Array.isArray(manifest.files)&&manifest.files.length>0&&manifest.files.length<=20000,'SOURCE_MANIFEST_SCHEMA');
let checked=0;const seen=new Set(),folded=new Set();
for(const row of manifest.files){
 need(typeof row.path==='string'&&!row.path.includes('\\')&&!row.path.includes('\0')&&!path.isAbsolute(row.path)&&!path.posix.isAbsolute(row.path)&&!/^\w:/.test(row.path)&&row.path.split('/').every(s=>s!==''&&s!=='.'&&s!=='..')&&path.posix.normalize(row.path)===row.path,'SOURCE_CANONICAL_RELATIVE_PATH');
 const fold=row.path.normalize('NFC').toLowerCase();need(!seen.has(row.path)&&!folded.has(fold),'SOURCE_DUPLICATE_PATH');seen.add(row.path);folded.add(fold);
 need(['file','symlink'].includes(row.kind)&&Number.isSafeInteger(row.bytes)&&row.bytes>=0&&/^[a-f0-9]{64}$/.test(row.sha256),'SOURCE_ROW_SCHEMA');
 const p=path.resolve(root,...row.path.split('/'));need(p.startsWith(root+path.sep),'PATH_OUTSIDE_REPO');const st=fs.lstatSync(p);
 need(row.kind==='symlink'?st.isSymbolicLink():st.isFile()&&!st.isSymbolicLink(),'SOURCE_KIND_MISMATCH');
 const resolved=fs.realpathSync(p);need(resolved.startsWith(realRoot+path.sep),'SOURCE_REALPATH_OUTSIDE_REPO');
 const raw=row.kind==='symlink'?Buffer.from(fs.readlinkSync(p)):fs.readFileSync(p);
 need(raw.length===row.bytes&&crypto.createHash('sha256').update(raw).digest('hex')===row.sha256,'SOURCE_SHA256_OR_SIZE_MISMATCH');checked++;
}
console.log(JSON.stringify({status:'PASS_SOURCE_BYTES_ONLY',checked,base:manifest.privateSourceCommit,scope:'Listed source bytes and kinds only; extra files not checked. Not APK, runtime, hardware or flight acceptance'},null,2));
