/** Fixed 30Hz raw-source phase. A late callback captures once, never catches up. */
export function createSourceCadence30(anchorBrowserMs) {
  const periodMs=1000/30;
  if(!Number.isFinite(anchorBrowserMs)||anchorBrowserMs<0)throw Error('SOURCE_SCHEDULE_ANCHOR_INVALID');
  let nextSlot=0,lastObserved=anchorBrowserMs,failure=null;
  function poll(nowBrowserMs){
    if(failure)return{eligible:false,error:failure};
    if(!Number.isFinite(nowBrowserMs)||nowBrowserMs<lastObserved){failure='SOURCE_SCHEDULE_MONOTONIC_CLOCK_INVALID';return{eligible:false,error:failure};}
    lastObserved=nowBrowserMs;
    const nextDeadline=anchorBrowserMs+nextSlot*1000/30;
    if(nowBrowserMs<nextDeadline)return{eligible:false};
    let latestSlot=Math.floor((nowBrowserMs-anchorBrowserMs)*30/1000);
    // Correct only floating point boundary rounding, without iterating elapsed slots.
    if(anchorBrowserMs+(latestSlot+1)*1000/30<=nowBrowserMs)latestSlot++;
    if(anchorBrowserMs+latestSlot*1000/30>nowBrowserMs)latestSlot--;
    latestSlot=Math.max(nextSlot,latestSlot);
    if(!Number.isSafeInteger(latestSlot)||!Number.isFinite(anchorBrowserMs+(latestSlot+1)*1000/30)){failure='SOURCE_SCHEDULE_SLOT_BOUND';return{eligible:false,error:failure};}
    const missedSlots=latestSlot-nextSlot,scheduledBrowserMs=anchorBrowserMs+latestSlot*1000/30;
    nextSlot=latestSlot+1;
    return{eligible:true,slot:latestSlot,elapsedSlots:missedSlots+1,missedSlots,scheduledBrowserMs,latenessMs:nowBrowserMs-scheduledBrowserMs};
  }
  return{poll,periodMs};
}
