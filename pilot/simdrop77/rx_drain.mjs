// Track admitted RX work through intentional closure; retain errors and bounds.
export class RxDrain {
 constructor(){this.pending=new Set();this.closing=false;this.failure=null;}
 track(job){if(this.closing)throw Error('RX_AFTER_CUTOFF');if(this.pending.size>=64)throw Error('RX_DRAIN_BOUND');this.pending.add(job);job.then(()=>this.pending.delete(job),e=>{this.failure??=e;this.pending.delete(job);});return job;}
 async drain(){this.closing=true;const results=await Promise.allSettled([...this.pending]);const rejected=results.find(r=>r.status==='rejected');if(rejected)this.failure??=rejected.reason;if(this.failure)throw this.failure;if(this.pending.size)throw Error('RX_NOT_DRAINED');}
}
