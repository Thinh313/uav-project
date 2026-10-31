import{LIMITS}from'./config.mjs';const mocks=new WeakSet();export const isMock=x=>mocks.has(x)&&Object.getPrototypeOf(x)===MockTransport.prototype;
export class MockTransport{
 #ctx=null;#listener=null;#up=new Map();#out=[];#fail=null;
 constructor(){mocks.add(this);Object.freeze(this);}connect(context,links,listener){this.#ctx=structuredClone(context);this.#up=new Map(links.map(s=>[s,true]));this.#listener=listener;}disconnect(){this.#ctx=null;this.#listener=null;this.#up.clear();}
 failNext(mode){if(!['BEFORE_SEND','UNCERTAIN_AFTER_SEND'].includes(mode))throw Error('Mock fault mode');this.#fail=mode;}
 send(envelope){if(!this.#ctx||!this.#up.get(envelope.linkId)||JSON.stringify(envelope.context)!==JSON.stringify(this.#ctx))throw Error('Mock closed/foreign send');if(!(envelope.bytes instanceof Uint8Array)||envelope.bytes.length>280||this.#out.length>=LIMITS.transactions)throw Error('Mock outbound capacity/type');if(this.#fail==='BEFORE_SEND'){this.#fail=null;throw Error('MOCK_REFUSED_BEFORE_SEND');}this.#out.push(structuredClone(envelope));if(this.#fail==='UNCERTAIN_AFTER_SEND'){this.#fail=null;return{status:'SEND_UNCERTAIN'};}return{status:'MOCK_SEND_ADMITTED_NOT_ACK'};}
 deliver(bytes,{linkId='mock-a',context=this.#ctx}={}){if(!this.#listener||!this.#up.get(linkId))return false;this.#listener({kind:'bytes',bytes:bytes.slice(),linkId,context:structuredClone(context)});return true;}
 down(linkId){if(!this.#up.has(linkId))throw Error('Unknown mock link');this.#up.set(linkId,false);this.#listener?.({kind:'link-down',linkId,context:structuredClone(this.#ctx)});}
 snapshot(){return{kind:'IN_MEMORY_MOCK_NO_IO',connected:!!this.#ctx,links:[...this.#up].map(([id,up])=>({id,up})),outbound:this.#out.map(x=>({...structuredClone(x),bytes:[...x.bytes]})),automaticRetries:0};}
}
export function createHardwareTransport(){throw Error('Hardware/SDK/network transport NOT_IMPLEMENTED; mock only');}

Object.freeze(MockTransport.prototype);
