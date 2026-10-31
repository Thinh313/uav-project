/** Online clock qualification from signed original Android receipt/event and a
 * private Root writer challenge. No browser-supplied host bracket is accepted. */
import{randomBytes}from'node:crypto';import{need,freeze}from'./mission.mjs';
export class NativeClock{
 constructor({writer,clock,processEpoch}){this.writer=writer;this.clock=clock;this.processEpoch=processEpoch;this.challenge=null;this.grantId=null;this.savedCalibrationSHA=null;}
 async first(grantId){need(!this.challenge||this.grantId!==grantId,'NATIVE_CLOCK_NO_REISSUE');const nonce=randomBytes(16).toString('hex'),proof=await this.writer.clockProof(nonce),c=proof.clock;
  const send=BigInt(c.nodeSentNs),recv=BigInt(proof.nodeReceivedNs),r0=BigInt(c.rootReceivedHostNs),r1=BigInt(c.rootPreparedHostNs);need(recv>=send&&r1>=r0&&recv-send<=200000000n,'NATIVE_ROOT_CLOCK_BRACKET_200MS');
  // Keep the private Root proof and its independent clock relation for cold join.
  this.offset=null;this.challenge=freeze({nonce,processEpoch:this.processEpoch,grantId,nodeIssuedNs:String(process.hrtime.bigint()),rootProof:proof});this.grantId=grantId;return{nonce,processEpoch:this.processEpoch,grantId};}
 qualify(body,receivedNs=process.hrtime.bigint()){
  need(this.challenge&&body.grantId===this.grantId,'NATIVE_CLOCK_GRANT');const receipt=body.clockReceipt,c=receipt?.challenge;need(c&&c.nonce===this.challenge.nonce&&c.processEpoch===this.processEpoch&&c.grantId===this.grantId,'NATIVE_CLOCK_SIGNED_CHALLENGE_RECEIPT');
  const issued=BigInt(this.challenge.nodeIssuedNs),received=BigInt(receipt.receivedElapsedNs),sample=BigInt(body.observedElapsedNs),now=BigInt(receivedNs);need(sample>=received&&now>=issued,'NATIVE_CLOCK_ORIGINAL_ORDER');
  // Challenge outbound and signed response inbound bracket Android->Node offset.
  // Lower uses challenge issue; upper uses first response receipt. Freeze it once;
  // later samples can never slide the bracket forward to revive old input.
  if(!this.offset){this.offset={lower:issued-received,upper:now-sample};need(this.offset.lower<=this.offset.upper&&this.offset.upper-this.offset.lower<=250000000n,'NATIVE_CLOCK_UNCERTAINTY_250MS');}
  const lower=sample+this.offset.lower,upper=sample+this.offset.upper<now?sample+this.offset.upper:now;need(lower<=upper&&now-lower<=250000000n,'NATIVE_CLOCK_SAMPLE_FRESH_250MS');return{clockDomain:'QUALIFIED_HOST_MONOTONIC_BRACKET',lowerMs:Number(lower/1000000n),upperMs:Number(upper/1000000n),proof:{challenge:this.challenge.nonce,nodeIssuedNs:this.challenge.nodeIssuedNs,offsetLowerNs:String(this.offset.lower),offsetUpperNs:String(this.offset.upper),rootProof:this.challenge.rootProof,originalAndroidObservedElapsedNs:body.observedElapsedNs,originalReceiptElapsedNs:receipt.receivedElapsedNs,originalCalibrationLowerNodeNs:String(sample+this.offset.lower),originalCalibrationUpperNodeNs:String(sample+this.offset.upper),causalIntersectionUpperNodeNs:String(upper),lowerNeverAdvanced:true,nodeReceivedNs:String(now)}};
 }
 reset(){this.challenge=null;this.grantId=null;this.savedCalibrationSHA=null;this.offset=null;}
}
