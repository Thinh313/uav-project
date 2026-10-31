/** Pure presentation math. No transport, storage, authority or browser side effects. */
export const canonical=x=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?'['+x.map(canonical).join(',')+']':'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';
export function clampTime(t,duration){return Math.max(0,Math.min(Number.isFinite(duration)?duration:0,Number.isFinite(t)?t:0));}
export function clock(t){t=Math.max(0,Number.isFinite(t)?t:0);return`${Math.floor(t/60).toString().padStart(2,'0')}:${Math.floor(t%60).toString().padStart(2,'0')}`;}
export function sampleAt(trace,t){
 if(!trace.length)return{index:-1,sample:null,next:null,unavailable:true};
 let lo=0,hi=trace.length;while(lo<hi){const mid=(lo+hi)>>>1;if(trace[mid].tS<=t)lo=mid+1;else hi=mid;}
 const index=Math.max(0,lo-1),sample=trace[index],next=trace[index+1]??null;
 return{index,sample,next,unavailable:t<sample.tS||!!(next?.breakBefore&&t>sample.tS&&t<next.tS)};
}
export function altitudeRange(trace){let min=0,max=5;for(const p of trace){min=Math.min(min,p.relativeHomeM);max=Math.max(max,p.relativeHomeM);}return{min,max};}
export function fitProjection(points,w,h,padding={left:85,right:20,top:110,bottom:150}){
 if(!points.length||![w,h].every(Number.isFinite)||w<=0||h<=0)return null;
 // Shrink margins on compact canvases; never impose a minimum scale that clips long traces.
 const left=Math.min(padding.left,w*.25),right=Math.min(padding.right,w*.1),top=Math.min(padding.top,h*.3),bottom=Math.min(padding.bottom,h*.35);
 let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
 for(const p of points){if(!Number.isFinite(p.x)||!Number.isFinite(p.y))return null;minX=Math.min(minX,p.x);maxX=Math.max(maxX,p.x);minY=Math.min(minY,p.y);maxY=Math.max(maxY,p.y);}
 const usableW=w-left-right,usableH=h-top-bottom,scale=Math.min(usableW/Math.max(20,maxX-minX),usableH/Math.max(20,maxY-minY));
 if(!(scale>0))return null;
 return{scale,left,right,top,bottom,X:x=>left+usableW/2+(x-(minX+maxX)/2)*scale,Y:y=>top+usableH/2-(y-(minY+maxY)/2)*scale};
}
export async function verifyClientReport(report,cryptoApi=globalThis.crypto){
 if(report?.format!=='aeris-coach01-report'||report.version!==1||report.operational!==false||report.authorityRestorable!==false||report.ai?.controlAuthority!==false||!Array.isArray(report.telemetry?.trace)||!report.telemetry.trace.length||!Number.isFinite(report.telemetry.durationS)||report.telemetry.durationS<0)throw Error('REPORT_SCOPE');
 if(!cryptoApi?.subtle)throw Error('CLIENT_CRYPTO_UNAVAILABLE');
 const{sha256,...body}=report,bytes=new TextEncoder().encode(canonical(body));
 const digest=[...new Uint8Array(await cryptoApi.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
 if(digest!==sha256)throw Error('REPORT_DIGEST');return report;
}
