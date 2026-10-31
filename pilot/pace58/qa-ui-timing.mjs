import assert from'node:assert/strict';import fs from'node:fs';import{UITiming}from'./ui-timing.mjs';
const world={dataset:{}},t=new UITiming();let now=0;
for(let i=0;i<1600;i++){now+=i===1500?120:1000/60;t.drawn(now,{run:'a',owned:true,controllerActive:true,physics:{frame:i*20,serverAgeMs:{high:10}}},world)}
assert.equal(t.rows.length,1600);assert.equal(t.summary().intervalMaxMs,120);assert(t.summary().measuredHz<60);assert(t.summary().notFrozenSceneStartupBuffer);
now+=2000;t.drawn(now,{controllerActive:false},world);const saved=JSON.parse(world.dataset.uiFrames);assert.equal(saved.rows.length,1600);assert.equal(saved.run,'a');
t.drawn(now+1000,{run:'b',owned:true,controllerActive:true,physics:{frame:0}},world);assert.equal(t.rows.length,1);assert.equal(world.dataset.uiFrames,undefined);
for(let i=0;i<12001;i++)t.drawn(now+2000+i,{run:'b',owned:true,controllerActive:true,physics:{frame:i}},world);
assert.equal(t.rows.length,12000);assert.equal(t.overflow,true);
fs.writeFileSync('evidence/pace58/qa-ui-timing.json',JSON.stringify({status:'PASS',checks:5,lateFrameSpikeAfterStartupDetected:true,runReset:true,explicitOverflow:true,realBrowser:false},null,2)+'\n',{flag:'wx'});console.log('UI timing5 checks PASS');
