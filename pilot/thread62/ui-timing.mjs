// Measures actual draws in this adapter; frozen scene's startup-only buffer is not used.
export class UITiming{
 constructor(){this.run=null;this.rows=[];this.last=null;this.reported=0;this.active=false;this.overflow=false;this.closedPublished=false}
 drawn(now,state,world){
  const active=!!(state?.controllerActive&&state?.run&&state?.owned);
  if(active&&state.run!==this.run){this.run=state.run;this.rows=[];this.last=null;this.reported=0;this.overflow=false;this.closedPublished=false;delete world.dataset.uiFrames}
  if(active){if(this.rows.length>=12000)this.overflow=true;else this.rows.push([now,this.last===null?null:now-this.last,state.physics?.frame??null,state.physics?.serverAgeMs?.high??null]);this.last=now}
  this.active=active;
  if(this.run&&now-this.reported>=1000){this.reported=now;world.dataset.uiPacing=JSON.stringify(this.summary());if(!active&&!this.closedPublished){world.dataset.uiFrames=JSON.stringify({run:this.run,rows:this.rows,overflow:this.overflow,domain:'browser-performance-now-ms',scope:'actual-draw-observer-not-physics'});this.closedPublished=true}}
 }
 summary(){const x=this.rows.slice(1).map(r=>r[1]).sort((a,b)=>a-b);const q=p=>x.length?x[Math.floor((x.length-1)*p)]:null;return{run:this.run,active:this.active,frames:this.rows.length,overflow:this.overflow,intervalMedianMs:q(.5),intervalP95Ms:q(.95),intervalP99Ms:q(.99),intervalMaxMs:x.at(-1)??null,measuredHz:this.rows.length>1?(this.rows.length-1)*1000/(this.rows.at(-1)[0]-this.rows[0][0]):null,clockDomain:'browser-performance-now-ms',source:'THREAD62_ACTUAL_DRAW_FULL_RUN',notFrozenSceneStartupBuffer:true}}
}
export function timingLabel(t){return t?.frames>1&&Number.isFinite(t.measuredHz)?'WebGL2 · '+t.measuredHz.toFixed(0)+'fps · p95 '+t.intervalP95Ms.toFixed(1)+'ms'+(t.active?'':' · lượt vừa đo'):'WebGL2 · chưa có phép đo'}
export function pendingStatus(previous,next){if(next.pendingStart)return next.busy?'Đang mở phiên SITL đã đăng ký…':'Kết quả mở phiên chưa rõ. Không retry; xem backend8819 để đối chiếu.';if(previous?.pendingStart)return next.controllerActive?'Phiên SITL đã mở; theo dõi telemetry.':'Phiên đã được đối chiếu và đóng; xem hồ sơ kiểm.';return null}
