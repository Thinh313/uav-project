export const TTL84={heartbeat:1500,position:1500,attitude:1500,gps:1500,health:1500,home:3000};
export function stable84(v){const sort=x=>Array.isArray(x)?x.map(sort):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,sort(x[k])])):x;return JSON.stringify(sort(v));}
// Exact pre-canonical schema order, retained solely to read earlier immutable records.
export function legacyOrder84(g){const h=g.home;const b={format:g.format,version:g.version,run:g.run,instance:g.instance,session:g.session,boot:g.boot,planSha256:g.planSha256,missionSha256:g.missionSha256,datum:g.datum,timeBasis:g.timeBasis,home:h?{lat:h.lat,lon:h.lon,amsl:h.amsl}:null,route:g.route.map(p=>({seq:p.seq,lat:p.lat,lon:p.lon}))};if(g.qualificationPolicy!==undefined)b.qualificationPolicy=g.qualificationPolicy;b.points=g.points.map(p=>{const q={at:p.at,lat:p.lat,lon:p.lon,height:p.height,amsl:p.amsl,speed:p.speed};if(p.qualified84!==undefined)q.qualified84=p.qualified84;return q;});b.fullWithinBound=g.fullWithinBound;b.pointBound=g.pointBound;return b;}
export const coordinate84=p=>!!p&&Number.isFinite(p.lat)&&Number.isFinite(p.lon)&&Math.abs(p.lat)<=80&&Math.abs(p.lon)<=180;
export function local84(home,p){if(!coordinate84(home)||!coordinate84(p))throw Error('GEOGRAPHY_COORDINATE');let d=p.lon-home.lon;d=(d+540)%360-180;return{x:d*Math.PI/180*6378137*Math.cos(home.lat*Math.PI/180),y:(p.lat-home.lat)*Math.PI/180*6378137};}
export function heading84(yaw){return Number.isFinite(yaw)?(yaw*180/Math.PI%360+360)%360:null;}
export function route84(plan){return(plan?.compiled?.items??[]).filter(i=>[16,22].includes(i.command)&&i.seq!==0).map(i=>({seq:i.seq,lat:i.x/1e7,lon:i.y/1e7})).filter(coordinate84);}
export function segments84(points){const result=[];let part=[];for(const p of points){if(p.qualified84!==true||!coordinate84(p)){if(part.length)result.push(part);part=[];continue;}if(part.length&&p.at-part.at(-1).at>1500){result.push(part);part=[];}part.push(p);}if(part.length)result.push(part);return result;}
export class Fly84 {
 constructor(){this.last=null;this.received=-Infinity;this.seen=new Set();this.deadlines={};this.blocked='CHƯA KẾT NỐI';}
 clear(reason){this.blocked=reason;this.deadlines={};}
 ingest(s,now){const e=s?.presentation84;if(!s?.ok||!e||e.format!=='aeris-fly84-envelope'||e.instance!==s.instance||!Number.isSafeInteger(e.sequence)||e.sequence<1||!Number.isFinite(now)){this.clear('NGUỒN KHÔNG HỢP LỆ');return false;}
  if(s.live&&(s.source!=='OWNED_INTERNAL_QUAD_SITL'||(s.live.vehicle?(s.live.vehicle.system!==42||s.live.vehicle.component!==1):s.live.connected===true)||!s.live.sessionId||!s.live.boot||!s.run)){this.clear('KHÔNG ĐÚNG NGUỒN / PHIÊN SITL');return false;}
  const prev=this.last?.presentation84;
  if(prev?.instance===e.instance&&e.sequence<=prev.sequence)return false;
  if(prev&&prev.instance!==e.instance){this.seen.add(prev.instance);if(this.seen.has(e.instance)){this.clear('PHIÊN CŨ BỊ TỪ CHỐI');return false;}}
  const delay=e.androidDeliveryAgeMs??0;if(!Number.isFinite(delay)||delay<0||delay>60000){this.clear('NHẬN DỮ LIỆU QUÁ HẠN');return false;}
  const identity=x=>[x?.instance,x?.run,x?.live?.sessionId,x?.live?.boot].join('/'),same=identity(s)===identity(this.last);
  const deadlines={};for(const[k,ttl]of Object.entries(TTL84)){const age=e.ageMs?.[k],stamp=e.sampleStamp?.[k];if(!Number.isFinite(age)||age<0||!Number.isFinite(stamp)){deadlines[k]=-Infinity;continue;}let until=now+ttl-age-delay;if(same&&prev?.sampleStamp?.[k]===stamp)until=Math.min(until,this.deadlines[k]??until);deadlines[k]=until;}
  this.deadlines=deadlines;this.last=s;this.received=now;this.blocked=null;return true;
 }
 view(now){const s=this.last,l=s?.live,fresh=k=>!this.blocked&&Number.isFinite(now)&&now>=this.received&&now-this.received<=1500&&now<=this.deadlines[k];
  const alive=!!l&&!l.failure&&l.connected&&fresh('heartbeat');const located=alive&&fresh('gps')&&l.gps?.fix>=3;const p=located&&fresh('position')&&coordinate84(l.position)&&[l.position.relativeAltitude,l.position.amsl,l.position.groundSpeed].every(Number.isFinite)?l.position:null;
  const home=located&&fresh('home')&&coordinate84(l.home)?l.home:null;
  return{state:this.blocked??(!l?'CHƯA KẾT NỐI':l.failure?'MẤT PHIÊN':alive&&!located?'CHỜ ĐỊNH VỊ 3D':!alive||!p?'DỮ LIỆU QUÁ HẠN':'LIVE SITL'),live:!!(alive&&p),mode:alive?l.mode:null,armed:alive?l.armed:null,position:p,home,
   heading:alive&&fresh('attitude')?heading84(l.attitude?.yaw):null,gps:alive&&fresh('gps')?l.gps:null,health:alive&&fresh('health')?l.health:null,
   distance:p&&home?Math.hypot(...Object.values(local84(home,p))):null,sourceAgeMs:s?.presentation84?.ageMs?.position??null,receiptAgeMs:Number.isFinite(this.received)?Math.max(0,now-this.received):null,
   run:s?.run,session:l?.sessionId,boot:l?.boot,route:route84(s?.plan),track:l?.trace??[],grant:s?.grant===true&&alive,complete:l?.completion?.complete===true};
 }
}
export async function verifyReview84(record,digest){
 if(!record||!/^aeris-native(83|84)-sitl-review$/.test(record.format)||record.authorityRestorable!==false||record.actualImages!==0||typeof record.accepted!=='boolean'||typeof record.aborted!=='boolean')throw Error('REVIEW_SCOPE');
 if(record.accepted&&(record.aborted||record.failure||!record.execution?.complete||!record.readback?.matches))throw Error('REVIEW_ACCEPTANCE_CONTRADICTION');
 const geo=record.geography84;if(!geo){if(record.format==='aeris-native84-sitl-review'&&!(record.trackOverflow===true&&!record.accepted))throw Error('REVIEW_GEOGRAPHY_MISSING');return{historical:true,geography:null,legacy:record.format==='aeris-native83-sitl-review',overflow:record.trackOverflow===true};}
 const{sha256,...body}=geo;
 let boundHash=false;if(body.hashScheme==='CANONICAL_KEYS_V1')boundHash=sha256===await digest(stable84(body));else if(body.hashScheme===undefined){const legacy=legacyOrder84(body);boundHash=stable84(legacy)===stable84(body)&&sha256===await digest(JSON.stringify(legacy));}
 if(!boundHash||geo.run!==record.run||geo.instance!==record.instance||geo.planSha256!==record.planSha256||geo.missionSha256!==record.missionSha256||!geo.session||!geo.boot||geo.pointBound!==1200||!Array.isArray(geo.points)||geo.points.length>1200||!Array.isArray(geo.route)||geo.route.length>32)throw Error('REVIEW_GEOGRAPHY_INTEGRITY');
 if(geo.trackOverflow===true){const ref=geo.rawReference,n=record.native95,raw=n?.raw;if(geo.hashScheme!=='CANONICAL_KEYS_V1'||geo.format!=='aeris-geography84'||geo.version!==1||geo.fullWithinBound!==false||record.trackOverflow!==true||geo.points.length!==0||!Number.isSafeInteger(geo.pointCount)||geo.pointCount<=1200||geo.pointCount>10000||geo.reason!=='WORKSPACE_TRACK_BOUND_RAW_REFERENCE'||ref?.format!=='aeris-sealed-native-raw-reference'||ref.version!==1||ref.run!==record.run||!/^s[a-f0-9]{20}$/.test(ref.run)||ref.head!==record.rawHead||!/^[a-f0-9]{64}$/.test(ref.head)||ref.records!==record.rawRecords||!Number.isSafeInteger(ref.records)||ref.records<1||!Number.isSafeInteger(ref.bytes)||ref.bytes<ref.records||ref.bytes>32*1024*1024||ref.closed!==true||ref.failed!==false||n?.ok!==true||n.open!==false||n.run!==record.run||n.authorityRestorable!==false||n.closureStorageError!==null||raw?.closed!==true||raw.failed!==false||raw.head!==ref.head||raw.records!==ref.records||raw.bytes!==ref.bytes||record.accepted&&n.safeComplete!==true)throw Error('REVIEW_COMPACT_RAW_INTEGRITY');if(geo.home&&!coordinate84(geo.home))throw Error('REVIEW_HOME');if(!geo.route.every(coordinate84))throw Error('REVIEW_ROUTE');return{historical:true,geography:null,compactGeography:geo,legacy:false,overflow:true};}
 if(geo.fullWithinBound!==true||record.trackOverflow===true)throw Error('REVIEW_GEOGRAPHY_INTEGRITY');
 if(geo.home&&!coordinate84(geo.home))throw Error('REVIEW_HOME');let at=-Infinity;for(const p of geo.points){if(!coordinate84(p)||![p.height,p.amsl,p.speed,p.at].every(Number.isFinite)||p.at<at)throw Error('REVIEW_TRACK');at=p.at;}if(!geo.route.every(coordinate84))throw Error('REVIEW_ROUTE');
 if(geo.qualificationPolicy==='GPS3D_FRESH_SELECTED_SOURCE_V1'&&geo.points.some(p=>typeof p.qualified84!=='boolean'))throw Error('REVIEW_QUALIFICATION');return{historical:true,geography:geo,legacy:false,legacyQuality:geo.qualificationPolicy!=='GPS3D_FRESH_SELECTED_SOURCE_V1'};
}
