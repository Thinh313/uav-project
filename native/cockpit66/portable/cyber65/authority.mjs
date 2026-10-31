import {clone,canonical,exact} from './contracts.mjs';
const issuers=new WeakSet();
export class MockIdentity {
 #credentials=new WeakMap();
 constructor(){issuers.add(this);}
 issue(subject){if(!['pilot-a','payload-b'].includes(subject))throw Error('SUBJECT_NOT_ENROLLED');const c=Object.freeze({kind:'OPAQUE_LOCAL_MOCK_CREDENTIAL'});this.#credentials.set(c,subject);return c;}
 resolve(c){const s=c&&this.#credentials.get(c);if(!s)throw Error('MOCK_IDENTITY_REQUIRED');return s;}
}
Object.freeze(MockIdentity.prototype);
export const MOCK_POLICY=Object.freeze({origin:'PROPOSED_ENGINEERING_MOCK_NOT_APPROVED_FLIGHT_POLICY',operatorAgeMs:1500,grantMs:1400,transferMs:800,maxEvents:256});
export class Authority {
 #identity;#now;#last=-1;#epoch=0;#ctx=null;#phase='DISCONNECTED';#operators=new Map();#grants=new Map();#pending=new Map();#events=[];#n=0;#rev=0;#scopes;#dropped=0;
 constructor({identity,now,scopes}){
  if(!issuers.has(identity)||Object.getPrototypeOf(identity)!==MockIdentity.prototype)throw Error('BRANDED_MOCK_IDENTITY_ONLY');
  if(typeof now!=='function'||!Array.isArray(scopes)||new Set(scopes).size!==scopes.length||scopes.length>16||scopes.some(s=>!/^aircraft$|^(camera|gimbal):[a-z0-9-]{1,32}$/.test(s)))throw Error('BOUNDED_SCOPE_CONFIGURATION');
  this.#identity=identity;this.#now=now;this.#scopes=[...scopes];
 }
 #event(kind,detail={}){if(this.#events.length===MOCK_POLICY.maxEvents){this.#events.shift();this.#dropped++;}this.#events.push({n:++this.#n,atMs:this.#last,kind,...clone(detail)});}
 #clear(reason){this.#grants.clear();this.#pending.clear();this.#operators.clear();this.#epoch++;this.#event('ALL_AUTHORITY_CLEARED',{reason});}
 #time(){if(this.#phase==='INVALID_CLOCK')throw Error('AUTHORITY_CLOCK_INVALID');const t=this.#now();if(!Number.isFinite(t)||t<0||t<this.#last){this.#phase='INVALID_CLOCK';this.#clear('CLOCK_REGRESSION_OR_INVALID');throw Error('AUTHORITY_CLOCK_INVALID');}this.#last=t;return t;}
 #role(subject,scope){if(!this.#scopes.includes(scope))throw Error('UNKNOWN_SCOPE');if(scope==='aircraft'&&subject!=='pilot-a')throw Error('PILOT_ROLE_REQUIRED');}
 #context(c){if(!this.#ctx||canonical(c)!==canonical(this.context()))throw Error('CURRENT_AUTHORITY_CONTEXT_REQUIRED');}
 #actor(c,ctx){this.tick();this.#context(ctx);if(this.#phase!=='CONNECTED')throw Error('AUTHORITY_NOT_CONNECTED');const s=this.#identity.resolve(c),a=this.#operators.get(s);if(!a||this.#last-a.atMs>MOCK_POLICY.operatorAgeMs)throw Error('OPERATOR_NOT_FRESH');return s;}
 context(){return {...clone(this.#ctx),authorityEpoch:this.#epoch};}
 connect(context){exact(context,['sessionId','generation','configSha256']);if(!/^[a-zA-Z0-9_-]{1,64}$/.test(context.sessionId)||!Number.isSafeInteger(context.generation)||context.generation<1||!/^[a-f0-9]{64}$/.test(context.configSha256))throw Error('TYPED_TRANSPORT_CONTEXT_REQUIRED');this.#time();this.#clear('EXPLICIT_CONNECT_NO_RESUME');this.#ctx=clone(context);this.#phase='CONNECTED';return this.context();}
 disconnect(reason='EXPLICIT_DISCONNECT'){this.#time();this.#clear(reason);this.#phase='DISCONNECTED';}
 heartbeat(credential,ctx){this.#time();this.#context(ctx);if(this.#phase!=='CONNECTED')throw Error('AUTHORITY_NOT_CONNECTED');const subject=this.#identity.resolve(credential);this.#operators.set(subject,{atMs:this.#last});this.#event('LOCAL_MOCK_IDENTITY_FRESH',{subject});}
 tick(){const t=this.#time();for(const [s,a]of this.#operators)if(t-a.atMs>MOCK_POLICY.operatorAgeMs)this.#lose(s,'OPERATOR_STALE');for(const [s,g]of this.#grants)if(t>=g.expiresMs){this.#grants.delete(s);this.#pending.delete(s);this.#event('GRANT_EXPIRED_NO_RESTORE',{scope:s});}for(const [s,p]of this.#pending)if(t>=p.expiresMs){this.#pending.delete(s);this.#grants.delete(s);this.#event('TRANSFER_EXPIRED_NO_RESTORE',{scope:s});}}
 #lose(subject,reason){this.#operators.delete(subject);for(const [scope,g]of this.#grants)if(g.owner===subject||this.#pending.get(scope)?.to===subject){this.#grants.delete(scope);this.#pending.delete(scope);this.#event('SUBJECT_SCOPE_REVOKED',{scope,subject,reason});}}
 lose(credential,ctx){const subject=this.#actor(credential,ctx);this.#lose(subject,'EXPLICIT_MOCK_LINK_LOSS');}
 // Explicit fixture bootstrap represents owner acceptance, not an automatic role grant.
 claim(credential,scope,ctx,acknowledge){const subject=this.#actor(credential,ctx);this.#role(subject,scope);if(acknowledge!=='ACCEPT_EXCLUSIVE_MOCK_SCOPE')throw Error('EXPLICIT_CONSENT_REQUIRED');if(this.#grants.has(scope)||this.#pending.has(scope))throw Error('SCOPE_ALREADY_OWNED');const g={scope,owner:subject,revision:++this.#rev,expiresMs:this.#last+MOCK_POLICY.grantMs};this.#grants.set(scope,g);this.#event('EXPLICIT_SCOPE_CLAIM',g);return clone(g);}
 release(credential,scope,ctx){const subject=this.#actor(credential,ctx),g=this.#grants.get(scope);if(g?.owner!==subject)throw Error('CURRENT_OWNER_REQUIRED');this.#grants.delete(scope);this.#pending.delete(scope);this.#event('RELEASED_NO_RESTORE',{scope,subject});}
 invalidateScope(scope,reason){if(!this.#scopes.includes(scope))throw Error('UNKNOWN_SCOPE');this.#grants.delete(scope);this.#pending.delete(scope);this.#event('SCOPE_INVALIDATED_NO_RESTORE',{scope,reason});}
 transfer(credential,scope,to,ctx){const from=this.#actor(credential,ctx),g=this.#grants.get(scope);this.#role(to,scope);if(!['pilot-a','payload-b'].includes(to)||to===from||!this.#operators.has(to)||this.#last-this.#operators.get(to).atMs>MOCK_POLICY.operatorAgeMs)throw Error('FRESH_RECIPIENT_REQUIRED');if(g?.owner!==from||this.#pending.has(scope))throw Error('CURRENT_OWNER_NO_PENDING_REQUIRED');g.revision=++this.#rev;const p={id:'transfer-'+this.#rev,scope,from,to,revision:g.revision,expiresMs:Math.min(g.expiresMs,this.#last+MOCK_POLICY.transferMs),authorityEpoch:this.#epoch};this.#pending.set(scope,p);this.#event('TRANSFER_FREEZES_SCOPE',p);return clone(p);}
 accept(credential,id,ctx){const to=this.#actor(credential,ctx),p=[...this.#pending.values()].find(x=>x.id===id);if(!p||p.to!==to||p.authorityEpoch!==this.#epoch||this.#last>=p.expiresMs)throw Error('FRESH_RECIPIENT_CONSENT_REQUIRED');const from=this.#operators.get(p.from),g=this.#grants.get(p.scope);if(!from||this.#last-from.atMs>MOCK_POLICY.operatorAgeMs||g?.owner!==p.from||g.revision!==p.revision)throw Error('FROM_OWNER_NO_LONGER_VALID');this.#role(to,p.scope);const next={scope:p.scope,owner:to,revision:++this.#rev,expiresMs:this.#last+MOCK_POLICY.grantMs};this.#grants.set(p.scope,next);this.#pending.delete(p.scope);this.#event('TRANSFER_ACCEPTED',next);return clone(next);}
 decline(credential,id,ctx){const to=this.#actor(credential,ctx),p=[...this.#pending.values()].find(x=>x.id===id);if(!p||p.to!==to)throw Error('RECIPIENT_REQUIRED');this.#pending.delete(p.scope);this.#grants.delete(p.scope);this.#event('DECLINED_NO_RESTORE',{scope:p.scope});}
 ticket(credential,scope,ctx){const owner=this.#actor(credential,ctx);this.#role(owner,scope);const g=this.#grants.get(scope);if(g?.owner!==owner||this.#pending.has(scope))throw Error('EXCLUSIVE_ACTIVE_OWNER_REQUIRED');return {scope,owner,revision:g.revision,expiresMs:g.expiresMs,...this.context()};}
 valid(ticket){try{this.tick();this.#context({sessionId:ticket.sessionId,generation:ticket.generation,configSha256:ticket.configSha256,authorityEpoch:ticket.authorityEpoch});const g=this.#grants.get(ticket.scope);return this.#phase==='CONNECTED'&&g?.owner===ticket.owner&&g.revision===ticket.revision&&!this.#pending.has(ticket.scope)&&this.#last<g.expiresMs&&this.#operators.has(ticket.owner);}catch{return false;}}
 snapshot(){try{this.tick();}catch{}return {context:this.context(),phase:this.#phase,grants:clone([...this.#grants.values()]),pending:clone([...this.#pending.values()]),operators:clone([...this.#operators.keys()]),events:clone(this.#events),historyComplete:this.#dropped===0,dropped:this.#dropped,policy:MOCK_POLICY,authentication:'LOCAL_MOCK_ONLY_NOT_REMOTE_AUTHENTICATION',flightLossAction:'UNSPECIFIED_NOT_EXECUTED'};}
}
