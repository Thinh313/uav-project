/** Mode-2 two-pointer projection. Pure requested input; no timers, sockets or arming. */
export class Touch06{
 constructor(){this.reset();}
 reset(){this.pointers={left:null,right:null};this.axes={x:0,y:0,z:500,r:0};this.seq=0;this.started=false;}
 down(slot,id){if(!['left','right'].includes(slot)||!Number.isInteger(id)||id<0||id>65535||this.pointers[slot]!==null||Object.values(this.pointers).includes(id))throw Error('POINTER_OWNERSHIP');this.pointers[slot]=id;}
 move(slot,id,dx,dy){if(this.pointers[slot]!==id||!Number.isFinite(dx)||!Number.isFinite(dy))throw Error('POINTER_CONTEXT');const x=Math.round(Math.max(-1,Math.min(1,dx))*1000),y=Math.round(Math.max(-1,Math.min(1,dy))*1000);if(slot==='left'){this.axes.r=x;this.axes.z=Math.round((1000-y)/2);}else{this.axes.y=x;this.axes.x=-y;}return{...this.axes};}
 snapshot(at){if(!Number.isSafeInteger(at)||at<0||Object.values(this.pointers).every(x=>x===null))throw Error('NEW_POINTER_SNAPSHOT_REQUIRED');const axes=this.started?{...this.axes}:{x:0,y:0,z:500,r:0};this.started=true;return{seq:++this.seq,sampleAtMs:at,leftPointer:this.pointers.left??-1,rightPointer:this.pointers.right??-1,...axes};}
}
