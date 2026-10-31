import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
export const stable=x=>JSON.stringify(sort(x));
function sort(x){if(Array.isArray(x))return x.map(sort);if(x&&typeof x==='object')return Object.fromEntries(Object.keys(x).sort().map(k=>[k,sort(x[k])]));return x;}
export const digest=x=>createHash('sha256').update(stable(x)).digest('hex');
export const clone=x=>structuredClone(x);
export const CONTRACT=JSON.parse(readFileSync(new URL('./contract.json',import.meta.url),'utf8'));
export const CONTRACT_SHA=digest(CONTRACT),POLICY=Object.freeze(CONTRACT.mockPolicy);
export const AXES=['LJ_X','LJ_Y','RJ_X','RJ_Y','LMJ_X','LMJ_Y','RMJ_X','RMJ_Y','LW','LD','RW','RD'];
export const GROUPS=[['Left Joystick',['LJ_X','LJ_Y']],['Right Joystick',['RJ_X','RJ_Y']],['Left Mini Joystick',['LMJ_X','LMJ_Y']],['Right Mini Joystick',['RMJ_X','RMJ_Y']],['Left Wheel',['LW']],['Left Dial',['LD']],['Right Wheel',['RW']],['Right Dial',['RD']],['Buttons',[]]];
export const INPUT_AXIS={6:'LJ_X',7:'LJ_Y',10:'RJ_X',11:'RJ_Y',15:'LMJ_X',16:'LMJ_Y',20:'RMJ_X',21:'RMJ_Y',2:'LW',3:'LD',13:'RW',14:'RD'};
export const PORTS=['OUTPUT_PORT_1','OUTPUT_PORT_2'];
export const RF_PORTS=['RF_PORT_1','RF_PORT_2'];
// Proposed mock topology only. Actual RF↔RC output association is unresolved.
export const MOCK_RF_ROUTES=Object.freeze({OUTPUT_PORT_1:'RF_PORT_1',OUTPUT_PORT_2:'RF_PORT_2'});
export function exact(x,keys){if(!x||typeof x!=='object'||Array.isArray(x)||Object.keys(x).sort().join()!==[...keys].sort().join())throw Error('EXACT_SCHEMA');}
export function integer(x,min,max){if(!Number.isSafeInteger(x)||x<min||x>max)throw Error('INTEGER_RANGE');return x;}
export function array(x,n,fn){if(!Array.isArray(x)||x.length!==n)throw Error('ARRAY_LENGTH');x.forEach(fn);}
export function context(x){exact(x,['origin','session','boot','target']);if(x.origin!==POLICY.origin||![x.session,x.boot,x.target].every(v=>typeof v==='string'&&v.length>0&&v.length<=64)||!x.target.startsWith('mock:'))throw Error('MOCK_CONTEXT_REQUIRED');return clone(x);}
export function info(x){exact(x,['uuid','dev','ver']);if(!/^[a-f0-9]{32}$/.test(x.uuid)||/^0+$/.test(x.uuid)||!/^[a-f0-9]{8}$/.test(x.dev)||!/^[a-f0-9]{8}$/.test(x.ver))throw Error('IDENTITY_RAW_BYTES');return clone(x);}
export function calibration(x){exact(x,['axis','min','max','trim','deadzone','inverted']);if(!AXES.includes(x.axis)||typeof x.inverted!=='boolean')throw Error('AXIS_SCHEMA');for(const k of ['min','max','trim','deadzone'])integer(x[k],0,4095);if(!(x.min<x.trim&&x.trim<x.max)||x.deadzone>=Math.min(x.trim-x.min,x.max-x.trim))throw Error('CALIBRATION_RANGE');return clone(x);}
export function config(x){exact(x,['format','revision','ports','axes','buttonMask','mappingCoefficients','multiModeButtons','power']);if(x.format!=='MOCK_NORMALIZED_MCU_CONFIG45'||typeof x.revision!=='string'||!x.revision.length||x.revision.length>64)throw Error('CONFIG_ORIGIN');
 array(x.ports,2,p=>{exact(p,['port','assign','min','max','trim','invertMask','protocol','frequencyHz']);if(!PORTS.includes(p.port)||!['STANDARD_SBUS','CUSTOM_SBUS','SUMD'].includes(p.protocol))throw Error('PORT_SYMBOL');integer(p.frequencyHz,0,200);integer(p.invertMask,0,65535);array(p.assign,16,v=>integer(v,0,33));for(const k of ['min','max','trim'])array(p[k],16,v=>integer(v,1000,2000));for(let i=0;i<16;i++)if(!(p.min[i]<=p.trim[i]&&p.trim[i]<=p.max[i])||p.min[i]===p.max[i])throw Error('CHANNEL_RANGE');});if(new Set(x.ports.map(p=>p.port)).size!==2)throw Error('PORT_DUPLICATE');
 array(x.axes,12,calibration);if(new Set(x.axes.map(a=>a.axis)).size!==12)throw Error('AXIS_DUPLICATE');integer(x.buttonMask,1,32767);
 exact(x.mappingCoefficients,['x','y','index']);for(const k of ['x','y'])array(x.mappingCoefficients[k],16,v=>{if(typeof v!=='number'||!Number.isFinite(v)||Math.abs(v)>3.4028234663852886e38)throw Error('FINITE_FLOAT32');});array(x.mappingCoefficients.index,16,v=>integer(v,0,65535));
 // No interpolation/order meaning is inferred from these opaque document coefficients.
 array(x.multiModeButtons,6,b=>{exact(b,['button','mode','trigger','values','step','rollover']);if(!/^MMB[1-6]$/.test(b.button)||!['BISTATE','TRISTATE','STEP'].includes(b.mode)||!['PRESS','DOUBLE_PRESS','TRIPLE_PRESS','HOLD','HOLD_2S','HOLD_5S'].includes(b.trigger)||typeof b.rollover!=='boolean')throw Error('MMB_SYMBOL');array(b.values,3,v=>integer(v,0,4095));integer(b.step,0,4095);});if(new Set(x.multiModeButtons.map(b=>b.button)).size!==6)throw Error('MMB_DUPLICATE');
 exact(x.power,['lowVoltageMv','highCurrentMa','buzzer']);integer(x.power.lowVoltageMv,0,65535);integer(x.power.highCurrentMa,0,65535);if(typeof x.power.buzzer!=='boolean')throw Error('POWER_BOOLEAN');return clone(x);
}
export function calibrationEvidence(x,step,current){exact(x,['step','axes','pressedMask']);integer(x.step,0,8);if(x.step!==step)throw Error('CALIBRATION_STEP');const names=GROUPS[step][1];array(x.axes,names.length,a=>{exact(a,['axis','samples']);if(!names.includes(a.axis))throw Error('CALIBRATION_GROUP');array(a.samples,3,v=>integer(v,0,4095));const [min,trim,max]=a.samples;if(!(min<trim&&trim<max))throw Error('CALIBRATION_SAMPLE_RANGE');});if(new Set(x.axes.map(a=>a.axis)).size!==names.length)throw Error('CALIBRATION_AXIS_DUPLICATE');integer(x.pressedMask,0,4294967295);if(step===8&&(x.pressedMask&current.buttonMask)!==current.buttonMask)throw Error('BUTTONS_NOT_ALL_OBSERVED');if(step!==8&&x.pressedMask!==0)throw Error('WRONG_GROUP_BUTTONS');return clone(x);}
export function normalize(raw,a){integer(raw,a.min,a.max);const delta=raw-a.trim;if(Math.abs(delta)<=a.deadzone)return 0;const v=delta>0?(delta-a.deadzone)/(a.max-a.trim-a.deadzone):(delta+a.deadzone)/(a.trim-a.min-a.deadzone);return a.inverted?-v:v;}
export function encodePhysicalMCU(){throw Error('MCU_WIRE_BLOCKED_UNKNOWN_DIALECT_AND_HERAHUB_APPLICABILITY');}
