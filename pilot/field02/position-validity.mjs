/** Presentation-only geographic usability. Never grants command authority. */
export function cockpitPosition02(state) {
 const f=state?.flight,l=f?.live,p=f?.latestPosition;
 const age=n=>Number.isFinite(n)&&n>=0&&n<=1500;
 const fail=reason=>({usable:false,position:null,reason});
 if(state?.client?.active!==true||l?.transport!=='connected'||l?.failure||!age(l?.heartbeatAgeMs)||!age(f?.positionAgeMs))return fail('LINK_OR_POSITION_STALE');
 const bound=v=>typeof v==='string'&&v.length>0&&v.length<=128;
 if(!p||!bound(f.run)||!f.request||f.request.run!==f.run||!['run','boot','session','modelSha256','planSha256'].every(k=>bound(p[k])&&bound(f.request[k])&&p[k]===f.request[k]))return fail('POSITION_TARGET_MISMATCH');
 if(!Number.isFinite(p.latitudeDeg)||Math.abs(p.latitudeDeg)>90||!Number.isFinite(p.longitudeDeg)||Math.abs(p.longitudeDeg)>180||!Number.isFinite(p.altitudeMslM)||!Number.isFinite(p.relativeHomeM))return fail('POSITION_GEOGRAPHY_INVALID');
 const g=p.gps;
 if(!g||!Number.isSafeInteger(g.fixType)||g.fixType<3||g.fixType>8||g.fixType!==p.gpsFix||!Number.isSafeInteger(g.satellites)||g.satellites<4||g.satellites>=255)return fail('GPS_POSITION_NOT_USABLE');
 if(!age(g.ageMs)||!age(g.ageMs+f.positionAgeMs))return fail('GPS_OBSERVATION_STALE');
 if(!Number.isSafeInteger(p.apTimeBootMs)||p.apTimeBootMs<=0)return fail('AP_POSITION_CLOCK_INVALID');
 return {usable:true,position:p,reason:'SIMULATED_POSITION_REFERENCE_ONLY'};
}

/** Local presentation only: absence never mints or restores a payload token. */
export const retainCockpitToken02=(token,{active,clientActive,positionUsable})=>active&&clientActive&&positionUsable?token:null;
