import {readFile,writeFile} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {runFence,replayCorpus} from './scenarios.mjs';
import {Decoder,unhex} from './wire.mjs';
const c=JSON.parse(await readFile('evidence/mavflight37/corpus4.json','utf8'));const replay=await replayCorpus(c);if(replay.status!=='MOCK_PASS')throw Error('accepted replay required');
const frames=[];function add(id,kind,rawHex){const f=new Decoder().push(unhex(rawHex))[0];frames.push({caseId:id,kind,rawHex,expected:f?{id:f.id,fields:f.fields,system:f.system,component:f.component,sequence:f.seq}:null})}
for(const s of c.cases){if(s.kind==='FENCE'){for(const step of s.input.steps)if(step.op==='rx')add(s.id,'MOCK_RX',step.rawHex);const r=await runFence(s.input);for(const p of r.outputs)add(s.id,'MOCK_BUFFER_TX_ONLY',p.rawHex)}else for(const f of s.input.frames)add(s.id,'MOCK_RX',f.rawHex)}
let n=1;while(existsSync(`evidence/mavflight37/dialogue-vectors${n}.json`))n++;await writeFile(`evidence/mavflight37/dialogue-vectors${n}.json`,JSON.stringify({origin:'MOCK_CORPUS_ONLY',corpusSha256:replay.corpusSha256,frames,networkSent:false},null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({frames:frames.length,receipt:`dialogue-vectors${n}.json`,networkSent:false}));
