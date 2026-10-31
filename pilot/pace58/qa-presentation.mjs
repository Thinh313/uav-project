import assert from'node:assert/strict';import fs from'node:fs';import{timingLabel,pendingStatus}from'./ui-timing.mjs';
const raw=JSON.parse(fs.readFileSync('evidence/pace58/p58B2-ui-frames.json')),timing=JSON.parse(fs.readFileSync('evidence/pace58/p58B2-ui-closed.json'));
const hz=(raw.rows.length-1)*1000/(raw.rows.at(-1)[0]-raw.rows[0][0]);assert(Math.abs(hz-timing.measuredHz)<1e-9);assert(timingLabel(timing).includes(hz.toFixed(0)+'fps'));assert(!timingLabel(timing).includes('60fps'));assert(timingLabel(timing).includes('lượt vừa đo'));
assert(timingLabel(null).includes('chưa có phép đo'));assert(pendingStatus(null,{pendingStart:true,busy:true}).includes('Đang mở'));
assert(pendingStatus({pendingStart:true},{pendingStart:false,controllerActive:true}).includes('đã mở'));assert(pendingStatus(null,{pendingStart:true,busy:false}).includes('Không retry'));
fs.writeFileSync('evidence/pace58/qa-presentation.json',JSON.stringify({status:'PASS',checks:5,meanFpsComparedToActualDrawTimestamps:true,recordedDraws:raw.rows.length,actualHz:hz,displayOnly:true,SITLRechecked:false},null,2)+'\n',{flag:'wx'});console.log('Presentation5 checks PASS');
