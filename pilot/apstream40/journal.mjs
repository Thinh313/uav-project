import {int,canonical,digest,bounded} from '../apflight36/types.mjs';
export class MockJournal {
 #rows=[];#busy=false;#blocked=false;#generation=0;#last=-1;#persist;
 constructor(persist=async()=>{}){if(typeof persist!=='function')throw Error('writer');this.#persist=persist;}
 revoke(){this.#generation++;}
 rows(){return structuredClone(this.#rows);}
 async append(kind,data,t,effect=()=>{}){
  int(t,0,1e12,'event time');if(this.#busy||this.#blocked||t<this.#last||this.#rows.length>=8192){this.#blocked=true;this.revoke();throw Error('JOURNAL_BOUND_CLOCK_OR_CONCURRENCY');}
  this.#busy=true;const g=this.#generation;
  try{const body={n:this.#rows.length+1,atMs:t,kind,data:structuredClone(data),previousSha256:this.#rows.at(-1)?.sha256??null},next=[...this.#rows,{...body,sha256:await digest(body)}];bounded(next,4*2**20);
   await this.#persist(structuredClone(next));this.#rows=next;this.#last=t;if(g!==this.#generation)throw Error('REVOKED_DURING_COMMIT');return effect();
  }catch(e){this.#blocked=true;this.revoke();throw e;}finally{this.#busy=false;}
 }
}
export async function validateJournal(rows){if(!Array.isArray(rows)||rows.length>8192)throw Error('journal bound');bounded(rows,4*2**20);let previous=null,last=-1;
 for(let k=0;k<rows.length;k++){const {sha256,...body}=rows[k];if(body.n!==k+1||body.previousSha256!==previous||body.atMs<last||await digest(body)!==sha256)throw Error('journal chain/order/hash');previous=sha256;last=body.atMs;}return rows.length;
}
