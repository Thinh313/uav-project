import {readFile,writeFile} from 'node:fs/promises';import {replay as original} from '../../pilot/cyber65/replay.mjs';import {replay as portable} from './portable/cyber65/replay.mjs';
const c=JSON.parse(await readFile('pilot/cyber65/corpus.json','utf8')),rows=[];
for(const s of c.body.cases){const a=await original(c,s),b=await portable(c,s);rows.push({id:s.id,originalPass:a.pass,portablePass:b.pass,exactReview:a.review.sha256===b.review.sha256,sha256:b.review.sha256});}
const out={status:rows.every(x=>x.originalPass&&x.portablePass&&x.exactReview)?'PASS_PORTABLE_PARITY':'FAIL',scenarios:rows.length,corpusSha256:c.sha256,rows,scope:'Node execution of portable/browser source vs original Node core; Android runtime NOT_CHECKED'};
await writeFile('evidence/cockpit66/portable-parity01.json',JSON.stringify(out,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:out.status,scenarios:rows.length}));if(out.status!=='PASS_PORTABLE_PARITY')process.exitCode=1;
