import assert from'node:assert/strict';import fs from'node:fs';
const mapping={lowerMs:100,upperMs:102,sampledBrowserMs:1000,validUntilBrowserMs:61000,roundtripMs:2},data={frameId:1,requestMs:2000,clock:mapping},context={run:'r',configId:'c'};
const oldShallow={...data,context:{...context}},fixed=structuredClone({...data,context:{...context}});
const encodedBefore=JSON.stringify(fixed);Object.assign(mapping,{lowerMs:101,upperMs:101.5,sampledBrowserMs:31000,validUntilBrowserMs:91000,roundtripMs:.5});context.configId='next';
assert.notEqual(oldShallow.clock.lowerMs,100,'fixture must expose old shallow mutation');assert.equal(JSON.stringify(fixed),encodedBefore);assert.equal(fixed.clock.sampledBrowserMs,1000);assert.equal(fixed.context.configId,'c');
const output={format:'aeris-correction02-clock-copy-design-test',version:1,at:new Date().toISOString(),status:'PASS',checks:4,oldShallowChanged:true,deepSnapshotStable:true,scope:'MOCK_PROPOSAL_ONLY_NOT_PINNED_RUNTIME_OR_ANDROID_ACCEPTANCE'};fs.writeFileSync('planning/betastability02/correction02-clock-copy-tests.json',JSON.stringify(output,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(output));
