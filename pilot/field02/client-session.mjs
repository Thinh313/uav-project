import {randomUUID} from 'node:crypto';
/** Volatile foreground fence. Never persisted and never restores command authority. */
export class ClientSession02 {
 constructor({now=()=>performance.now(),onRevoke=()=>{},ttlMs=3000}={}){this.now=now;this.onRevoke=onRevoke;this.ttlMs=ttlMs;this.current=null;this.epoch=0;}
 revoke(reason){const c=this.current;if(!c||!c.active)return; c.active=false;c.reason=reason;this.onRevoke({reason,instance:c.instance,epoch:c.epoch,authorityRestored:false});}
 tick(){const c=this.current;if(c?.active&&this.now()-c.heartbeatAt>this.ttlMs)this.revoke('CLIENT_HEARTBEAT_EXPIRED');return this.view();}
 action(q){if(!q||typeof q.instance!=='string'||!/^[-a-zA-Z0-9_]{8,100}$/.test(q.instance))throw Error('CLIENT_INSTANCE_REQUIRED');this.tick();
  if(q.action==='activate'){this.revoke('NEW_FOREGROUND_EPOCH');this.current={id:randomUUID(),epoch:++this.epoch,instance:q.instance,platform:q.platform==='ANDROID_WEBVIEW'?'ANDROID_WEBVIEW':'HOST_BROWSER',active:true,heartbeatAt:this.now(),reason:'EXPLICIT_FOREGROUND',authorityRestored:false};return this.view();}
  if(['background','stop'].includes(q.action)){if(q.instance!==this.current?.instance)throw Error('CLIENT_INSTANCE_MISMATCH');this.revoke('CLIENT_'+q.action.toUpperCase());return this.view();}
  if(q.action==='heartbeat'){if(q.instance!==this.current?.instance)throw Error('CLIENT_INSTANCE_MISMATCH');this.assert(q);this.current.heartbeatAt=this.now();return this.view();}throw Error('CLIENT_ACTION_ALLOWLIST');
 }
 assert(q){this.tick();const c=this.current;if(!c?.active||q.clientId!==c.id||q.clientEpoch!==c.epoch||q.clientInstance!==c.instance)throw Error('ACTIVE_FOREGROUND_CLIENT_EPOCH_REQUIRED');return c;}
 view(){const c=this.current;return c?{...c,ageMs:this.now()-c.heartbeatAt,ttlMs:this.ttlMs,authorityRestored:false}:{active:false,epoch:this.epoch,ttlMs:this.ttlMs,authorityRestored:false};}
}
