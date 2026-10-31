import {readFile,writeFile} from 'node:fs/promises';
import {DEFAULT_SURVEY,DEMO_CAMERA,localFrame} from '../app/core/survey.mjs';
import {SITL_WORLD} from '../app/core/compiler.mjs';
import {prepareQgcForSitl,makeQgcRequest} from '../app/core/qgc.mjs';
import {PROFILE_REF} from '../app/core/vehicle-profile.mjs';
import {digest} from '../app/core/execution-record.mjs';
import {sha256} from '../app/core/geodata.mjs';
import {caseExpectation,validateBenchmarkSuite} from '../app/core/benchmark.mjs';
const frame=localFrame({lat:SITL_WORLD.home.lat,lon:SITL_WORLD.home.lon});
const survey=(name,points,heading=0)=>({format:'aeris-survey',version:2,operational:false,model:'wgs84-enu-polygon-flat-v2',coordinateSystem:'WGS84',settings:{...structuredClone(DEFAULT_SURVEY),name,polygon:points.map(([x,y])=>frame.reverse({x,y})),altitude:15,speed:6,heading,sideOverlap:30,frontOverlap:30,targetGsdCm:null,camera:structuredClone(DEMO_CAMERA)}});
const synthetic={kind:'synthetic',source:'BENCH06 generated local ENU polygon; not QGC export or physical site',originalSha256:null,derivation:null};
const narrow=survey('Dải hẹp · một tuyến',[[15,15],[25,15],[25,51],[15,51]]);
const rotated=survey('Khảo sát tuyến xoay 35°',[[15,15],[53,15],[53,39],[15,39]],35);
const source='app/fixtures/qgc/roundtrip03/simple-relative-qgc-saved.plan',raw=await readFile(source,'utf8'),options={confirmHome:true,confirmSnapshot:false,altitudePolicy:'preserve-relative',cameraPolicy:'preserve'},derived=await prepareQgcForSitl(raw,options);
const cases=[
 {id:'narrow',title:'Dải hẹp / một tuyến',provenance:synthetic,request:narrow,accept:true},
 {id:'rotated',title:'Tuyến xoay 35°',provenance:synthetic,request:rotated,accept:true},
 {id:'qgc-relative',title:'QGC / độ cao tương đối',provenance:{kind:'qgc-derived',source,originalSha256:await sha256(raw),derivation:derived.receipt},request:makeQgcRequest(derived.raw),accept:true},
 {id:'concave-connector',title:'Vùng lõm / đoạn nối ngoài ranh',provenance:synthetic,request:survey('U-shaped negative',[[15,15],[57,15],[57,57],[43,57],[43,29],[29,29],[29,57],[15,57]],90),accept:false},
 {id:'unresolved-datum',title:'Chưa có tham chiếu độ cao',provenance:synthetic,request:{...narrow,settings:{...narrow.settings,altitudeFrame:'relative-launch'}},accept:false},
 {id:'outside-world',title:'Vượt vùng thử 500 m',provenance:synthetic,request:survey('Outside simulator',[[550,15],[560,15],[560,51],[550,51]]),accept:false},
 {id:'camera-rate',title:'Chu kỳ chụp không đáp ứng',provenance:synthetic,request:{...narrow,settings:{...narrow.settings,speed:20,frontOverlap:95}},accept:false}
];
for(const c of cases){const expectation=await caseExpectation(c.request);if(expectation.accepted!==c.accept)throw Error(`Unexpected acceptance: ${c.id}`);c.expected=expectation;delete c.accept;}
const body={format:'aeris-benchmark-suite',version:1,id:'survey-matrix06',simulation:true,world:SITL_WORLD,profile:PROFILE_REF,cases};
const suite={...body,sha256:await digest(body)};await validateBenchmarkSuite(suite);await writeFile('app/fixtures/bench06/suite.json',JSON.stringify(suite,null,2)+'\n');console.log(JSON.stringify({sha256:suite.sha256,cases:cases.map(c=>({id:c.id,...c.expected}))},null,2));
