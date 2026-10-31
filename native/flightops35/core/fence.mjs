import {canonical,digest,exact,str,fail} from './common.mjs';
import {frame,polygon,classify} from './geometry.mjs';
/** Abstract synthetic fence peer. Not a MAVLink transport or ArduPilot enforcement adapter. */
export class MockFence {
 constructor(){this.plan=null;this.digest=null;this.target=null;this.readback=false;this.breach=null;}
 async upload(p,target){exact(p,['format','version','origin','rule','polygons'],'fence');str(target);if(p.format!=='aeris-fence35'||p.version!==1||p.rule!=='SINGLE_INCLUSION'||!Array.isArray(p.polygons)||p.polygons.length!==1||p.polygons[0].coordinates.length!==1)fail('Unsupported AP semantics; no silent holes/union conversion');polygon(p.polygons[0],frame(p.origin));this.plan=structuredClone(p);this.digest=await digest(p);this.target=target;this.readback=false;this.breach=null;return{target,sha256:this.digest,ackOnly:true,operational:false}}
 async compare(p,target){this.readback=!!this.plan&&target===this.target&&canonical(p)===canonical(this.plan)&&await digest(p)===this.digest;return this.readback}
 observe(position,target){if(!this.readback||target!==this.target)fail('Fence readback/target missing');const project=frame(this.plan.origin);this.breach=classify(project(position),polygon(this.plan.polygons[0],project))<0;return{breach:this.breach,origin:'SYNTHETIC',operational:false,autopilotEnforcementProven:false}}
 disconnect(){this.readback=false;this.breach=null;}
}
