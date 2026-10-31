/** Once per source configuration: flush the first validated network key. No dummy frames. */
export function networkBootstrap({decoder,session,isCurrent,outputTimestamp,requestResync,onEvent=()=>{}}) {
 const identity=['run','boot','configId','feed','profileId'];let attempted=false,expected=null,keyTimestamp=null;
 const current=()=>{if(!isCurrent()||decoder.state!=='configured')throw Error('BOOTSTRAP_SESSION_STALE');};
 const same=meta=>identity.every(k=>meta[k]===session[k]);
 return {
  async flushFirstNetworkKey(meta) {
   current();if(attempted)throw Error('BOOTSTRAP_ONCE_PER_CONFIG');
   if(!same(meta)||meta.type!=='key')throw Error('BOOTSTRAP_NETWORK_KEY_IDENTITY');
   attempted=true;keyTimestamp=meta.timestampUs;let timer;
   try {
    const flushStarted=performance.now();await Promise.race([decoder.flush(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('BOOTSTRAP_FLUSH_1500MS_TIMEOUT')),1500);})]);
    current();onEvent('FIRST_NETWORK_KEY_FLUSH_RESOLVED',{flushMs:performance.now()-flushStarted,timestampUs:keyTimestamp});if(outputTimestamp()!==keyTimestamp)throw Error('BOOTSTRAP_EXACT_NETWORK_KEY_OUTPUT_REQUIRED');
    const resyncStarted=performance.now();onEvent('POST_FLUSH_RELAY_KEY_REQUEST');const reply=await requestResync();current();onEvent('POST_FLUSH_RELAY_KEY_REPLY',{roundtripMs:performance.now()-resyncStarted});
    if(!same(reply.session)||reply.session.viewerId!==session.viewerId||!Number.isSafeInteger(reply.recoveryId)||reply.recoveryId<=meta.recoveryId)throw Error('BOOTSTRAP_RESYNC_IDENTITY');
    expected=reply.recoveryId;return {expectedRecoveryId:expected,retainSameConfiguredDecoder:true};
   } finally {clearTimeout(timer);}
  },
  consumeWarmKey(meta) {
   current();if(expected===null)throw Error('BOOTSTRAP_NOT_WAITING_KEY');
   if(!same(meta)||meta.recoveryId!==expected||meta.timestampUs<=keyTimestamp)throw Error('BOOTSTRAP_POST_FLUSH_KEY_IDENTITY');
   if(meta.type!=='key')return false;
   expected=null;return true;
  },
  get attempted(){return attempted;},
  get expectedRecoveryId(){return expected;}
 };
}
