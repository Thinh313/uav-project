import {crc} from '../../services/mavlink.mjs';
// Pinned generated ArduPilot common/RC_CHANNELS_OVERRIDE: id70, CRC124, minimum18bytes.
export function encodeRC(channels,{seq=0,system=255,component=190,targetSystem=42,targetComponent=1}={}){
 if(targetSystem!==42||targetComponent!==1||!Array.isArray(channels)||channels.length!==8||channels.some(v=>!Number.isInteger(v)||!(v===0||v===65535||v>=1000&&v<=2000)))throw Error('RC_TARGET_OR_CHANNEL_DOMAIN');
 const p=Buffer.alloc(18);channels.forEach((v,i)=>p.writeUInt16LE(v,2*i));p[16]=42;p[17]=1;
 const h=Buffer.from([0xfd,18,0,0,seq&255,system,component,70,0,0]),b=Buffer.concat([h,p,Buffer.alloc(2)]);b.writeUInt16LE(crc(b.subarray(1,-2),124),b.length-2);return b;
}
export function channelsFromAxes([roll,pitch,yaw,lift]){return [1500+Math.round(roll*300),1500-Math.round(pitch*300),1500+Math.round(lift*300),1500+Math.round(yaw*300),65535,65535,65535,65535];}
export const RELEASE=[0,0,0,0,65535,65535,65535,65535];
