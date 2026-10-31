// New evidence qualification; unchanged TAKEOFF command/readback. No command is generated here.
export function takeoffSample(plan,boundHome,m,hb,landed,current,previous,at){
 const takeoff=plan.compiled.items.find(i=>i.command===22),first=plan.compiled.items.find(i=>i.command===16&&i.seq>0);if(!takeoff||!first||!boundHome||!hb||hb.custom_mode!==3||!(hb.base_mode&128)||landed!==2||current<takeoff.seq||current>first.seq||!Number.isFinite(at))return null;
 const p=m.fields;if(m.id!==33||m.system!==42||m.component!==1||![p.lat,p.lon,p.relative_alt,p.alt,p.time_boot_ms].every(Number.isFinite)||p.time_boot_ms<=0)return null;const x=(p.lon/1e7-boundHome.lon)*111319*Math.cos(boundHome.lat*Math.PI/180),y=(p.lat/1e7-boundHome.lat)*111319,height=p.relative_alt/1000;
 if(Math.hypot(x,y)>3||Math.abs(height-takeoff.z)>1||Math.abs(p.alt/1000-boundHome.amsl-height)>.5)return null;
 if(previous&&(p.time_boot_ms<=previous.bootMs||at<=previous.at||at-previous.at>1500))return null;
 return{at,bootMs:p.time_boot_ms,heightM:height,MSLAltitudeM:p.alt/1000,lat:p.lat/1e7,lon:p.lon/1e7,sequence:m.seq,takeoffSeq:takeoff.seq,currentSeq:current,planSha256:plan.sha256};
}
