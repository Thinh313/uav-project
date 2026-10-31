import {randomUUID,randomBytes} from 'node:crypto';
import {normalize,DEFAULT_CAL} from '../simtrain52/contracts.mjs';
export class Authority{
 constructor(clock=()=>performance.now(),release=()=>{}){this.clock=clock;this.release=release;this.challenges=new Map();this.revoke('NEW');}
 issue(){const now=this.clock(),id=randomBytes(12).toString('hex');for(const [k,v]of this.challenges)if(now-v>200)this.challenges.delete(k);if(this.challenges.size>20)this.challenges.clear();this.challenges.set(id,now);return id;}
 valid(id){const at=this.challenges.get(id),now=this.clock();return at!==undefined&&now>=at&&now-at<=200;}
 claim(session,boot,challenge){if(!this.valid(challenge))throw Error('CHALLENGE_STALE');this.revoke('EXPLICIT_NEW_LEASE');this.session=session;this.boot=boot;this.lease=randomUUID();this.state='NEUTRAL_REQUIRED';this.seq=-1;this.clientAt=-1;this.last=this.clock();return this.lease;}
 revoke(reason){const was=this.state==='ACTIVE';this.state='REVOKED';this.reason=reason;this.axes=[0,0,0,0];this.lease=null;this.last=null;if(was)this.release(reason);}
 receive(e,session,boot){try{
  if(!e||Object.keys(e).sort().join(',')!=='axes,boot,challenge,clientAt,focused,lease,seq,session')throw Error('INPUT_SCHEMA');
  if(!['ACTIVE','NEUTRAL_REQUIRED'].includes(this.state)||!this.lease)throw Error('EXPLICIT_LEASE_REQUIRED');
  this.tick();if(!this.lease)throw Error('INPUT_EXPIRED');
  if(e.session!==session||e.session!==this.session||e.boot!==boot||e.boot!==this.boot||e.lease!==this.lease)throw Error('SESSION_BOOT_LEASE');
  if(!this.valid(e.challenge))throw Error('CHALLENGE_STALE');
  if(!Number.isSafeInteger(e.seq)||e.seq<=this.seq||!Number.isFinite(e.clientAt)||e.clientAt<0||e.clientAt<this.clientAt||e.focused!==true||!Array.isArray(e.axes)||e.axes.length!==4)throw Error('INPUT_SEQUENCE_CLOCK_FOCUS');
  const axes=e.axes.map(x=>normalize(x,DEFAULT_CAL));this.seq=e.seq;this.clientAt=e.clientAt;this.last=this.clock();
  if(this.state==='NEUTRAL_REQUIRED'&&!axes.every(x=>Math.abs(x)<=.02))return false;
  this.axes=axes;this.state='ACTIVE';this.reason='EXPLICIT_SIMULATOR_LEASE';return true;
 }catch(e){this.revoke(e.message);throw e}}
 tick(){if(this.last!==null&&(this.clock()<this.last||this.clock()-this.last>200))this.revoke('INPUT_STALE_OR_SUSPENDED');}
 snapshot(){return {state:this.state,reason:this.reason,axes:this.axes,lease:this.lease};}
}
