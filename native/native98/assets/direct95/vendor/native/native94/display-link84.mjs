import{NativeMission83}from'./link83.mjs';
/** Presentation qualification only; base mission, upload and flight gates unchanged. */
export class DisplayLink84 extends NativeMission83{
 process63(m){const before=this.trace.length;super.process63(m);if(m.id!==33||m.system!==42||m.component!==1||this.trace.length!==before+1)return;
  const gps=this.samples[24]?.fields;this.trace.at(-1).qualified84=!!(gps?.fix_type>=3&&this.freshness(0,1500)&&this.freshness(24,1500)&&this.freshness(33,1500));
 }
}
