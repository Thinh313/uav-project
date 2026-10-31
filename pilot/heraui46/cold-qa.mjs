import assert from 'node:assert/strict';
import {readFile,writeFile,statfs} from 'node:fs/promises';
import {replay} from '../heramcu45/model.mjs';
import {MockFramer45,encodeMockAction} from '../heramcu45/framer.mjs';
import {HeraMCU45} from '../heramcu45/model.mjs';
import {stable} from '../heramcu45/schema.mjs';
const f=await statfs('.',{bigint:true});assert.ok(f.bavail*f.bsize>20n*1024n**3n+16777216n);const corpus=JSON.parse(await readFile('evidence/heramcu45/corpus5.json','utf8'));let rows=0;
for(const c of corpus.cases){assert.ok(c.pass);replay(c.record,c.record.seal.bodySha256);rows+=c.record.events.length;}
const selected=corpus.cases.find(c=>c.name==='nine calibration results +save+readback').record,framer=new MockFramer45(),model=new HeraMCU45(selected.context),stream=Buffer.concat(selected.events.map(e=>encodeMockAction(e.body.input)));for(let pos=0;pos<stream.length;pos+=13)for(const action of framer.push(stream.subarray(pos,pos+13)))model.process(action);framer.close();assert.equal(stable(model.export()),stable(selected));
await writeFile('evidence/heraui46/cold1.json',JSON.stringify({status:'PASS',corpusCases:corpus.cases.length,eventsReplayed:rows,stream:{chunkBytes:13,frames:framer.frames,bytes:stream.length,exactRecord:true},scope:'Protected45 coldreplay/read-only imports, no oldreceiptwrites'},null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({status:'PASS',corpusCases:corpus.cases.length,events:rows}));
