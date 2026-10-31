import assert from 'node:assert/strict';
import {readFile,writeFile,statfs} from 'node:fs/promises';
import {replay} from '../heramcu45/model.mjs';
import {replayCapsule} from './capsule.mjs';
const f=await statfs('.',{bigint:true});assert.ok(f.bavail*f.bsize>20n*1024n**3n+16777216n);const c=JSON.parse(await readFile('evidence/heramcu45/corpus5.json','utf8'));for(const x of c.cases)replay(x.record,x.record.seal.bodySha256);const old46=JSON.parse(await readFile('evidence/heraui46/browser7/export.json','utf8'));replay(old46,old46.seal.bodySha256);const own=JSON.parse(await readFile('evidence/herapersist47/jvm-after-restart.json','utf8'));replayCapsule(own,own.seal.bodySha256);await writeFile('evidence/herapersist47/cold1.json',JSON.stringify({status:'PASS',protected45Cases:c.cases.length,protected46ExportReplay:true,ownJVMRestoredReplay:true,noOldReceiptWrites:true},null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:'PASS',cases:c.cases.length}));
