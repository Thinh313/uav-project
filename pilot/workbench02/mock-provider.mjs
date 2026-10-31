import{shaBytes}from'./native-bridge.mjs';
/** Explicit test provider, never represented as Android/SAF device execution. */
export class MockProvider{
 constructor(validate,{body=null,head='ROOT',pickJson=null,pickKml=null}={}){this.validate=validate;this.body=body;this.head=head;this.foreground=true;this.session='mock-session-0000000000000001';this.instance='mock-native';this.pickJson=pickJson;this.pickKml=pickKml;this.exports=[];this.sequence=0;this.receiver=null;this.fail=null;}
 environment(){return JSON.stringify({format:'aeris-native-workbench02',platform:'MOCK_NATIVE_BRIDGE',instance:this.instance,session:this.session,foreground:this.foreground});}
 request(raw){const q=JSON.parse(raw);Promise.resolve().then(async()=>{let result,error;try{if(this.fail)throw Error(this.fail);if(!this.foreground||q.session!==this.session||q.instance!==this.instance)throw Error('MOCK_NATIVE_CONTEXT');const n=Number(q.id.split(':').at(-1));if(n<=this.sequence)throw Error('MOCK_NATIVE_REPLAY');this.sequence=n;const a=q.args;
  if(q.action==='load')result={status:this.body===null?'EMPTY':'COMMITTED',head:this.head,body:this.body,bodySha256:this.body===null?null:await shaBytes(this.body)};
  else if(q.action==='save'){if(a.expectedHead!==this.head)throw Error('MOCK_CAS');await this.validate(a.body);if(await shaBytes(a.body)!==a.bodySha256)throw Error('MOCK_BODY_SHA');const old=this.head;this.body=a.body;this.head=await shaBytes(this.body+':'+old);result={status:'COMMITTED',head:this.head,previousHead:old,bodySha256:a.bodySha256};}
  else if(q.action==='export'){await this.validate(a.body);if(await shaBytes(a.body)!==a.bodySha256)throw Error('MOCK_BODY_SHA');this.exports.push(a.body);result={status:'MOCK_SAF_READBACK_ONLY',bodySha256:a.bodySha256,bytes:new TextEncoder().encode(a.body).length};}
  else{const body=q.action==='pick-kml'?this.pickKml:this.pickJson;if(body===null)throw Error('SAF_CANCELLED_NO_SUCCESS');if(q.action==='pick-json')await this.validate(body);result={status:'PICK_READ_VERIFIED',body,bodySha256:await shaBytes(body)};}
  result.platform='MOCK_NATIVE_BRIDGE';result.authorityRestored=false;
 }catch(e){error=e.message;}this.receiver?.({...q,ok:!error,...(error?{error}:{result})});});}
}
