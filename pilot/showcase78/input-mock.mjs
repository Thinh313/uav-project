const world=document.getElementById('world'),log=document.getElementById('log');let events=[];
const q={source:'ACTUAL_AP_REFERENCE_PHYSICS',owned:true,lease:true,localSnapshotAgeMs:0}; // deliberately synthetic positive fixture, not a provenance claim
function set(){world.dataset.qa=JSON.stringify(q)}set();
for(const type of ['keydown','keyup'])world.addEventListener(type,e=>{events.push({type,code:e.code});log.textContent=JSON.stringify(events);});
document.getElementById('lost').onclick=()=>{q.lease=false;set()};document.getElementById('restore').onclick=()=>{q.lease=true;set()};
await import('/controls.mjs');
