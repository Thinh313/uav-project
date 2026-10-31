import{verifyFlightFiles as canonicalVerifyFlightFiles}from'../../../field02/flight/handoff-raw.mjs';import{BINARY}from'./profile.mjs';
export const QUALIFIED_PROFILE='beta06g13-native-arm64-exec-4.7.1',QUALIFIED_IMAGE='sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84',QUALIFIED_BINARY_PATH='.local/beta06g3/arducopter';
/** Additional exact profile fence; canonical raw/CRC/mission/closure algorithm is unchanged. */
export function assertQualifiedFlightFiles(files){
 const json=n=>{if(!Buffer.isBuffer(files[n]))throw Error('QUALIFIED_PROFILE_FILE:'+n);return JSON.parse(files[n]);},request=json('request.json'),raw=files['raw.jsonl'];if(!Buffer.isBuffer(raw)||raw.length>16*2**20)throw Error('QUALIFIED_RAW_BOUND');const rows=raw.toString().trimEnd().split('\n').map(JSON.parse),sessions=rows.filter(x=>x.kind==='SESSION');if(sessions.length!==1||sessions[0].data.context.binarySha256!==BINARY)throw Error('QUALIFIED_EXACT_BINARY_SESSION');
 const preflights=rows.filter(x=>x.kind==='PREFLIGHT');if(preflights.some(x=>x.data.assessment?.profileId!==QUALIFIED_PROFILE))throw Error('QUALIFIED_PREFLIGHT_ID');
 if(request.mode==='sitl'){const l=json('launch.json'),s=sessions[0].data.context,a=l.command;const at=flag=>a[a.indexOf(flag)+1];
  if(l.qualifiedProfile!==QUALIFIED_PROFILE||l.binarySha256!==BINARY||l.binaryPath!==QUALIFIED_BINARY_PATH||l.imageId!==QUALIFIED_IMAGE||l.platform!=='linux/arm64'||l.observerEnabled!==false||l.binaryMode!=='0755'||l.retained!==true||l.speedup!==1||l.hardDeadlineS!==540||s.origin!=='OBSERVED_OWNED_SITL'||s.containerId!==l.containerId||s.pid!==l.pid||s.startedAt!==l.startedAt)throw Error('QUALIFIED_LAUNCH_CONTEXT');
  if(!Array.isArray(a)||a[1]!=='create'||a.includes('--rm')||at('--platform')!=='linux/arm64'||at('--cpus')!=='1'||at('--memory')!=='256m'||at('--pull')!=='never'||at('--model')!=='quad'||at('--speedup')!=='1'||a.filter(x=>x.startsWith('AERIS_DIRECT_TRACE=')).join()!=='AERIS_DIRECT_TRACE=0'||!a.some(x=>x.endsWith('/'+QUALIFIED_BINARY_PATH+':/aeris/arducopter:ro'))||a.some(x=>/entry\.sh|clockprobe|LD_PRELOAD|AERIS_DIRECT_TRACE=1|AERIS_AP_TRACE|AERIS_INSTRUMENT/.test(x)))throw Error('QUALIFIED_COMMAND_PROFILE');
  const image=a.findIndex(x=>x==='rtr-aeris-sim32-trace-builder@'+QUALIFIED_IMAGE);if(image<0||a[image+1]!=='/aeris/arducopter')throw Error('QUALIFIED_DIRECT_ENTRY');
 }
 return{qualifiedProfile:QUALIFIED_PROFILE,binarySha256:BINARY,mode:request.mode,sourceSession:sessions[0].data.context.session};
}
export async function verifyFlightFiles(files){assertQualifiedFlightFiles(files);return canonicalVerifyFlightFiles(files);}
