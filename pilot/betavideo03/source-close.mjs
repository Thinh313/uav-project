/** Receipts observe the owned child's exit; elapsed time alone is never closure. */
export async function closeOwnedSource(child,exitPromise,{graceMs=2500,termMs=750,killMs=750}={}){
 if(!child)return{pid:null,code:null,signal:null,notStarted:true,terminationSignals:[]};
 const signals=[];child.stdin.end();
 const observed=async deadline=>{let timer;return Promise.race([exitPromise,new Promise(r=>{timer=setTimeout(()=>r(null),deadline);})]).finally(()=>clearTimeout(timer));};
 let result=await observed(graceMs);if(!result){signals.push('SIGTERM');child.kill('SIGTERM');result=await observed(termMs);if(!result){signals.push('SIGKILL');child.kill('SIGKILL');result=await observed(killMs);}}
 if(!result)throw Error('NATIVE_OWNED_EXIT_UNOBSERVED');return{...result,terminationSignals:signals};
}
export async function drainSourcePrefix(client){try{return{prefix:client?await client.traceBarrier():null,prefixFailure:null};}catch(e){return{prefix:null,prefixFailure:String(e.message).slice(0,240)};}}
