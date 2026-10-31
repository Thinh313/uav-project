/** Original flight implementation and MockSocket, with only revised evidence root/pins admission. */
import path from'node:path';import{ROOT,verifyOverlay}from'./overlay.mjs';
const{FlightBeta06G5:Base}=await import('../beta06g5/flight/adapter.mjs');
export class FlightBeta06G5 extends Base{
 pins(){const original=super.pins(),manifestPath=globalThis[Symbol.for('aeris.g5.mockcompat.manifest')],overlay=verifyOverlay(manifestPath);return{...original,files:{...original.files,...overlay.files},revisionOverlay:{format:overlay.format,path:path.relative(ROOT,manifestPath),scope:overlay.scope}};}
 async action(route,d){if((route==='connect'&&d?.mode!=='mock')||(this.current&&this.current.mode!=='mock'))throw Error('MOCKCOMPAT_NO_SITL_ADMISSION');return super.action(route,d);}
 async connect(d){if(d?.mode!=='mock')throw Error('MOCKCOMPAT_NO_SITL_ADMISSION');return super.connect(d);}
}
