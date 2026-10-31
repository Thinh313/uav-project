/** QA-only proposal, NOT imported by production viewer. No local/dummy frames. */
export function networkBootstrapProposal({decoder,session,isCurrent,outputTimestamp,requestResync}) {
 const identity=['run','boot','configId','feed','profileId','viewerId'];let attempted=false,expected=null,keyTimestamp=null;
 const current=()=>{if(!isCurrent()||decoder.state!=='configured')throw Error('BOOTSTRAP_SESSION_STALE');};
 const same=meta=>identity.every(k=>meta[k]===session[k]);
 return {
  async flushFirstNetworkKey(meta) {
   current();if(attempted)throw Error('BOOTSTRAP_ONCE_PER_CONFIG');
   if(!same(meta)||meta.type!=='key')throw Error('BOOTSTRAP_NETWORK_KEY_IDENTITY');
   attempted=true;keyTimestamp=meta.timestampUs;let timer;
   try {
    await Promise.race([decoder.flush(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('BOOTSTRAP_FLUSH_1500MS_TIMEOUT')),1500);})]);
    current();if(outputTimestamp()!==keyTimestamp)throw Error('BOOTSTRAP_EXACT_NETWORK_KEY_OUTPUT_REQUIRED');
    const reply=await requestResync();current();
    if(!same(reply.session)||!Number.isSafeInteger(reply.recoveryId)||reply.recoveryId<=meta.recoveryId)throw Error('BOOTSTRAP_RESYNC_IDENTITY');
    expected=reply.recoveryId;return {expectedRecoveryId:expected,retainSameConfiguredDecoder:true};
   } finally {clearTimeout(timer);}
  },
  consumeWarmKey(meta) {
   current();if(expected===null)throw Error('BOOTSTRAP_NOT_WAITING_KEY');
   if(!same(meta)||meta.recoveryId!==expected||meta.timestampUs<=keyTimestamp)throw Error('BOOTSTRAP_POST_FLUSH_KEY_IDENTITY');
   if(meta.type!=='key')return false;
   expected=null;return true;
  },
  get attempted(){return attempted;}
 };
}
