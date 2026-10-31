export const ADJUSTMENTS=Object.freeze({altitude:{step:1,min:10,max:30,unit:'m'},speed:{step:0.1,min:.5,max:2,unit:'m/s'}});
export function steppedValue(field,value,direction){
 const p=ADJUSTMENTS[field];
 if(!p||typeof value!=='number'||!Number.isFinite(value)||value<p.min||value>p.max||![-1,1].includes(direction))throw Error('INVALID_EXPLICIT_STEP');
 return Math.max(p.min,Math.min(p.max,Math.round((value+direction*p.step)*10)/10));
}
export function themePresentation(theme){
 if(!['day','night'].includes(theme))throw Error('UNKNOWN_THEME');
 return theme==='day'?{symbol:'#i-sun',label:'Giao diện ngày. Chuyển sang giao diện đêm',pressed:false}:{symbol:'#i-moon',label:'Giao diện đêm. Chuyển sang giao diện ngày',pressed:true};
}
export function tickPresentationKey(s){
 return JSON.stringify([s.phase,s.ready,s.storageBlocked,s.revision,s.cursor,s.grant,s.missionSha256,s.snapshotCount,s.source?.allowed,s.source?.assessment?.state,s.source?.assessment?.reasons?.map(x=>x.code),s.source?.binding?.reasons?.map(x=>x.code)]);
}

export function reviewPresentation(phase,loaded){
 if(!loaded)return {symbol:'#i-clock',state:'loading'};
 if(phase==='COMPLETED_MOCK')return {symbol:'#i-check',state:'completed-mock'};
 if(phase?.startsWith('INTERRUPTED'))return {symbol:'#i-interrupted',state:'interrupted'};
 if(['RUNNING_MOCK','AWAITING_MOCK_LANDING'].includes(phase))return {symbol:'#i-clock',state:'in-progress'};
 return {symbol:'#i-review',state:'empty'};
}
