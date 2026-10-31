export const fail=m=>{throw Error(m)};
export const exact=(v,keys,name='schema')=>{if(!v||typeof v!=='object'||Array.isArray(v)||Object.keys(v).sort().join()!==keys.slice().sort().join())fail(name);return v};
export const num=(v,lo,hi,name)=>{if(typeof v!=='number'||!Number.isFinite(v)||v<lo||v>hi)fail(name);return v};
export const str=(v,max=100)=>{if(typeof v!=='string'||!v.length||v.length>max)fail('string bound');return v};
export const canonical=v=>{if(v===null||typeof v!=='object'){if(typeof v==='number'&&!Number.isFinite(v)||v===undefined)fail('canonical value');return JSON.stringify(v)}if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}'};
export const digest=async v=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(typeof v==='string'?v:canonical(v))))].map(x=>x.toString(16).padStart(2,'0')).join('');
export const utc=v=>{if(typeof v!=='string'||!/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(v)||!Number.isFinite(Date.parse(v))||new Date(Date.parse(v)).toISOString()!==v)fail('UTC ISO timestamp');return Date.parse(v)};
export const isHash=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
