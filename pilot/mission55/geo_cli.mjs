import {evaluate} from './geo.mjs';
const chunks=[];let size=0;
for await(const chunk of process.stdin){size+=chunk.length;if(size>1_000_000)throw Error('INPUT_LIMIT');chunks.push(chunk);}
const input=JSON.parse(Buffer.concat(chunks).toString('utf8'));
if(!Array.isArray(input)||input.length>2000)throw Error('CASE_LIMIT');
process.stdout.write(JSON.stringify(input.map(({id,op,args})=>{try{return {id,ok:true,result:evaluate(op,args)};}catch(e){return {id,ok:false,error:e.message};}}))+'\n');
