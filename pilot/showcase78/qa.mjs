import assert from 'node:assert/strict';
import {startShowcase,admitted,PREVIEW_MIN,LIVE_MIN} from './server.mjs';
import {targets} from './sound.mjs';
import {stickKeys,SCRIPT} from './controls.mjs';
let checks=0;function check(x){assert.ok(x);checks++}
check(!admitted(PREVIEW_MIN-1));check(admitted(PREVIEW_MIN));check(!admitted(LIVE_MIN-1,true));check(admitted(LIVE_MIN,true));check(!admitted(NaN));
const low=targets([1000,1000,1000,1000],3),high=targets([5000,5100,4900,5000],3);
check(high.gain>low.gain);check(high.frequencies[0]>low.frequencies[0]);check(targets([0,0,0,0],0).gain===0);check(targets([5000,5000,5000,5000],50).gain<high.gain);
check(stickKeys('left',0,0).length===0);check(stickKeys('right',0,-1).join()==='KeyW');check(stickKeys('left',1,-1).join()==='ArrowRight,ArrowUp');check(stickKeys('right',-.32,.32).length===0);check(SCRIPT.reduce((s,x)=>s+x.ms,0)===12000);check(SCRIPT.at(-1).keys.length===0);
const server=await startShowcase(8838);const base='http://127.0.0.1:8838';
try{
 for(const p of ['/','/showcase.mjs','/showcase.css','/sound.mjs','/scene.mjs','/blend.mjs','/assets/cesium-drone.glb','/assets/replay-index.json','/assets/showcase78-flight.json','/live']){const r=await fetch(base+p);check(r.status===200);await r.arrayBuffer()}
 check((await fetch(base+'/',{method:'POST'})).status===405);
 check((await fetch(base+'/',{headers:{origin:'http://evil.invalid'}})).status===403);
 check((await fetch(base+'/api/flight/input',{method:'POST',headers:{'content-type':'application/json'},body:'{}'})).status===403);
 check((await fetch(base+'/..%2f..%2fAGENTS.md')).status===404);
 const replayList=await(await fetch(base+'/assets/replay-index.json')).json();check(replayList.length===3);check(replayList[0].nonNeutralRenderSamples===122);check(replayList[0].inputAlignment.includes('not AP RC echo'));
 const meta=await(await fetch(base+'/api/presentation')).json();check(meta.actualImages===0&&meta.calibratedHera===false&&meta.liveMinimumGiB===28);
 const catalog=await(await fetch(base+'/api/catalog')).json();check(catalog.length===23);check(catalog.some(c=>c.id==='sim-feedback'&&c.limitations.includes('Lỗi an toàn còn mở')));check((await fetch(base+'/api/report?id=delivery%2FCOMPLETION-KEY74.md')).status===200);
 console.log(JSON.stringify({status:'PASS_SCOPED_HOST_QA',checks,scope:'HTTP/admission/audio math; no AP, browser or acoustic listening acceptance'}));
}finally{await new Promise(r=>server.close(r))}
