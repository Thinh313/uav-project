import{exact,int,str,digest,bounded,fail}from'./types.mjs';
export async function validateLedger(rows){
 if(!Array.isArray(rows)||rows.length>256)fail('ledger row bound');bounded(rows,262144);let tail=null,last=-1,epoch=null;const seen=new Set();
 for(let i=0;i<rows.length;i++){const e=rows[i];exact(e,['n','epoch','atMs','kind','data','previousSha256','sha256'],'ledger entry');int(e.atMs,0,1e12,'ledger clock');str(e.epoch);str(e.kind);if(e.epoch!==epoch){if(seen.has(e.epoch))fail('interleaved ledger epoch');seen.add(e.epoch);epoch=e.epoch;last=-1;}if(e.atMs<last||e.n!==i+1||e.previousSha256!==tail)fail('ledger order');const{sha256,...body}=e;if(await digest(body)!==sha256)fail('ledger hash');last=e.atMs;tail=e.sha256;}return rows;
}
export class Ledger{
 constructor(persist=async()=>{},idFactory=()=>crypto.randomUUID(),rows=[]){this.persist=persist;this.idFactory=idFactory;this.rows=structuredClone(rows);this.epoch=idFactory();this.busy=false;this.blocked=false;this.last=-1;this.generation=0;}
 revoke(){this.generation++}
 async append(kind,data,t,effect=()=>{}){
  int(t,0,1e12,'event time');if(this.busy||this.blocked||t<this.last||this.rows.length>=256){this.blocked=true;this.revoke();fail('writer/clock/evidence gate')}
  this.busy=true;const generation=this.generation;
  try{const body={n:this.rows.length+1,epoch:this.epoch,atMs:t,kind,data:structuredClone(data),previousSha256:this.rows.at(-1)?.sha256??null},next=[...this.rows,{...body,sha256:await digest(body)}];bounded(next,262144);await this.persist(next);this.rows=next;this.last=t;if(generation!==this.generation)fail('session revoked during commit');return effect();}catch(e){this.blocked=true;this.revoke();throw e}finally{this.busy=false}
 }
}
