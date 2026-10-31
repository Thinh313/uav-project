/** Local asynchronous-result fence only. Never supplies control authority. */
export class ClientFence{
 constructor(){this.generation=0;}
 next(){return ++this.generation;}
 invalidate(){this.generation++;}
 current(ticket){return ticket===this.generation;}
}
export function deadlineElapsed(start,end,maximum){if(!Number.isFinite(start)||!Number.isFinite(end)||end<start||end-start>maximum)throw Error('CLIENT_RESPONSE_DEADLINE_UNKNOWN_NO_RETRY');}
export function flightControls(s,{active=false,busy=false,consent=false}={}){
 const f=s?.flight,live=f?.live,ok=active&&!busy,owned=ok&&!!f?.run&&!live?.failure;
 return{connect:ok&&!f?.run&&consent,preflight:owned&&live?.stage==='DISARMED'&&live?.armed===false,grant:owned&&(f?.preflight?.ready===true||f?.regrantReady===true),upload:owned&&!!f?.authority&&f?.preflight?.ready===true,arm:owned&&live?.stage==='DISARMED'&&f?.preflight?.ready===true&&!!f?.authority&&!!live?.readback63&&live?.armed===false,auto:owned&&!!f?.authority&&live?.stage==='ARMED_HOME_REVIEW'&&live?.postArmHomeReviewFresh===true,close:owned&&f?.completion?.complete===true};
}

/** UI uses current observed leases, never a previous invalidation receipt. No authority is granted here. */
export function payloadLabel(s){const p=s?.payloadAuthority,f=s?.flight,leases=p?.snapshot?.leases;if(!p||p.failedClosed||!Array.isArray(leases))return'Chưa xác định';const current=leases.filter(l=>l.flightRun===f?.run&&l.flightBoot===f?.request?.boot);if(!current.length)return'Chưa cấp';const own=current.filter(l=>l.clientId===s.client?.id&&l.clientEpoch===s.client?.epoch&&l.clientInstance===s.client?.instance);return own.length?'Đang giữ · '+own.length:'Phiên khác · '+current.length;}

export const flightStageLabel=stage=>({DISARMED:'Trên đất',ARM_GROUND:'Đang arm',ARMED_HOME_REVIEW:'Kiểm Home',AUTO:'AUTO'}[stage]??(stage?'Chưa xác định':'Chờ kết nối'));
