import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('../',import.meta.url));
const imported=await import(pathToFileURL(process.env.AERIS_PNG_MODULE));
const PNG=imported.PNG||imported.default.PNG;
const results=[];
for(const file of ['plan-1440.png','plan-1024.png','plan-1280.png','plan-mobile-canvas.png']){
 const decoded=PNG.sync.read(await readFile(path.join(root,'evidence/ux01',file)));
 let yellow=0,neutral=0,total=0;
 for(let i=0;i<decoded.data.length;i+=4){const [r,g,b,a]=decoded.data.subarray(i,i+4);if(a<128)continue;total++;
  if(r>150&&g>110&&b<130&&r>b*1.35&&g>b*1.35)yellow++;
  if(Math.max(r,g,b)-Math.min(r,g,b)<=18)neutral++;
 }
 const result={file,width:decoded.width,height:decoded.height,yellowPercent:+(100*yellow/total).toFixed(3),neutralPercent:+(100*neutral/total).toFixed(3),yellowBudgetPercent:5};
 assert.ok(result.yellowPercent<=5,`${file} exceeds project's small-accent budget`);results.push(result);
}
await writeFile(path.join(root,'evidence/ux01/palette-measurement.json'),JSON.stringify({results,method:'Counts opaque pixels in rendered screenshots using an explicit yellow RGB heuristic; selected states only, not brand certification'},null,2)+'\n');
console.log(JSON.stringify(results));
