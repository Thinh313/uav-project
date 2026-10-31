import {writeFile,statfs} from 'node:fs/promises';
import {loadCorpus,replay} from './replay.mjs';
import {sha} from './contracts.mjs';
const label=process.argv[2];if(!/^attempt[0-9]{2}$/.test(label))throw Error('NEW_ATTEMPT_LABEL_REQUIRED');
const fs=await statfs('.');if(fs.bavail*fs.bsize<20*2**30+16*2**20)throw Error('DISK_FLOOR_ADMISSION');
const c=await loadCorpus(),results=[];
for(const s of c.body.cases){try{results.push(await replay(c,s));}catch(e){results.push({scenarioId:s.id,pass:false,fatal:e.stack});}}
const failures=results.filter(x=>!x.pass).map(r=>({scenario:r.scenarioId,fatal:r.fatal??null,assertions:r.assertions?.filter(x=>!x.pass)??[],steps:r.outcomes?.filter(x=>!x.pass)??[]}));
const body={status:failures.length?'FAIL_MOCK_REPLAY':'PASS_SCOPED_MOCK_REPLAY',corpusSha256:c.sha256,scenarioCount:results.length,passed:results.filter(x=>x.pass).length,failed:failures.length,assertionCount:results.reduce((n,r)=>n+(r.assertions?.length??0),0),failures,results,scope:'In-memory mock only; no hardware/Phase One SDK/two physical operators or flight'};
await writeFile(new URL('../../evidence/cyber65/'+label+'-replay.json',import.meta.url),JSON.stringify({body,sha256:sha(body)},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:body.status,scenarios:body.scenarioCount,passed:body.passed,assertions:body.assertionCount,failures}));process.exitCode=failures.length?1:0;
