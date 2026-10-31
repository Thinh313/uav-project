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
 return{connect:ok&&!f?.run&&consent,preflight:owned&&live?.stage==='DISARMED'&&live?.armed===false,grant:owned&&f?.preflight?.ready===true,upload:owned&&!!f?.authority&&f?.preflight?.ready===true,arm:owned&&live?.stage==='DISARMED'&&f?.preflight?.ready===true&&!!f?.authority&&!!live?.readback63&&live?.armed===false,auto:owned&&!!f?.authority&&live?.stage==='ARMED_HOME_REVIEW'&&live?.postArmHomeReviewFresh===true,close:owned&&f?.completion?.complete===true};
}
