import assert from 'node:assert/strict';import {writeFile} from 'node:fs/promises';import {existsSync} from 'node:fs';
import {corpus43,replayCorpus43,executeFixture} from './corpus.mjs';
const c=corpus43(),r=replayCorpus43(c);let n=1;while(existsSync(`evidence/preflight43/mock${n}.json`))n++;
await writeFile(`evidence/preflight43/corpus${n}.json`,JSON.stringify(c,null,2)+'\n',{flag:'wx'});await writeFile(`evidence/preflight43/mock${n}.json`,JSON.stringify({status:r.every(x=>x.pass)?'PASS':'FAIL',total:r.length,passed:r.filter(x=>x.pass).length,results:r},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({total:r.length,passed:r.filter(x=>x.pass).length,failures:r.filter(x=>!x.pass).map(x=>({name:x.name,expected:x.expected,actual:x.actual,error:x.error}))}));assert.ok(r.every(x=>x.pass));
