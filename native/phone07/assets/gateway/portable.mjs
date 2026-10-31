export class Buffer extends Uint8Array{
 static from(v,encoding='utf8'){if(typeof v==='string'){if(encoding==='base64'){const s=atob(v);return new Buffer(Uint8Array.from(s,c=>c.charCodeAt(0)));}return new Buffer(new TextEncoder().encode(v));}return new Buffer(v);}
 toString(encoding='utf8'){if(encoding==='base64'){let s='';for(const b of this)s+=String.fromCharCode(b);return btoa(s);}if(encoding==='hex')return Array.from(this,b=>b.toString(16).padStart(2,'0')).join('');return new TextDecoder().decode(this);}
 equals(other){return this.length===other.length&&this.every((v,i)=>v===other[i]);}
}
export const randomUUID=()=>crypto.randomUUID();export const randomBytes=n=>{if(n>1024)throw Error('RANDOM_BOUND');return crypto.getRandomValues(new Buffer(n));};
