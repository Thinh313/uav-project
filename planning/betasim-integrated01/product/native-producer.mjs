/** Online identity for the development Android SIM producer, not HID attestation.
 * Registration MUST come from Root's DUMP-protected, APK/source/PID-bound probe.
 * A browser's own public key or platform label is never an enrollment source.
 */
import{verifyTouchMapping}from'./touch-mapping.mjs';
import{createPublicKey,verify}from'node:crypto';import{need,sha,freeze}from'./mission.mjs';
export const DOMAIN=Buffer.from('AERIS_SIM_NATIVE_INPUT_V1\n','ascii');
const b64=(text,maximum)=>{need(typeof text==='string'&&text.length<=maximum*4/3+8,'NATIVE_SIGNATURE_BASE64_BOUND');const bytes=Buffer.from(text,'base64');need(bytes.length<=maximum&&bytes.toString('base64')===text,'NATIVE_SIGNATURE_CANONICAL_BASE64');return bytes;};
export class NativeProducer{
 static async fromRootWriter(writer){const reply=await writer.nativeRegistration(),r=reply.nativeRegistration;need(r?.format==='aeris-root-native-producer-registration'&&r.version===1&&r.authorityGranted===false&&r.rootRegistrationRef&&r.originalObservationRef,'NATIVE_GENUINE_ROOT_PRIVATE_REGISTRATION');return new NativeProducer({...r,scope:'ROOT_PRIVILEGED_NATIVE_STATUS_VERIFIED',authorityRestorable:false,originalStatusRef:r.originalObservationRef});}
 constructor(rootRegistration){
  need(rootRegistration?.scope==='ROOT_PRIVILEGED_NATIVE_STATUS_VERIFIED'&&rootRegistration.authorityRestorable===false&&rootRegistration.originalStatusRef,'NATIVE_ROOT_REGISTRATION_REQUIRED');
  const p=rootRegistration;need(Number.isSafeInteger(p.pid)&&p.pid>0&&/^[a-f0-9]{32}$/.test(p.processEpoch)&&/^[a-f0-9]{64}$/.test(p.sourceSHA256),'NATIVE_ROOT_IDENTITY');
  const der=b64(p.publicKeyX509Base64,256);need(sha(der)===p.keyId,'NATIVE_ROOT_KEY_FINGERPRINT');this.key=createPublicKey({key:der,format:'der',type:'spki'});need(this.key.asymmetricKeyType==='ec'&&this.key.asymmetricKeyDetails?.namedCurve==='prime256v1','NATIVE_ROOT_P256');
  this.registration=freeze(structuredClone(p));this.sequences=new Map();
 }
 verifyEnvelope(envelope){
  need(envelope?.format==='aeris-native-input-signed-envelope'&&envelope.version===1&&envelope.algorithm==='SHA256withECDSA'&&envelope.keyId===this.registration.keyId,'NATIVE_SIGNED_ENVELOPE');
  const raw=b64(envelope.payloadBase64,16384),signature=b64(envelope.signatureBase64,80);
  need(verify('sha256',Buffer.concat([DOMAIN,raw]),this.key,signature),'NATIVE_SIGNATURE_INVALID');
  const body=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw));need(body&&body.pid===this.registration.pid&&body.processEpoch===this.registration.processEpoch&&body.authorityRestorable===false,'NATIVE_SIGNED_PROCESS_CONTEXT');
  need(Number.isSafeInteger(body.observedElapsedNs)&&body.observedElapsedNs>=0,'NATIVE_ORIGINAL_CLOCK');
  return{body:freeze(body),original:{payloadBase64:envelope.payloadBase64,signatureBase64:envelope.signatureBase64,keyId:envelope.keyId,rawPayloadSHA256:sha(raw),rootRegistrationRef:this.registration.originalStatusRef}};
 }
 input(envelope,{grantId,missionSHA256,context}){
  const result=this.verifyEnvelope(envelope),q=result.body;
  need(q.format==='aeris-native-pad-sample'&&q.version===1&&q.profileId==='WORKBENCH_SIM_V1'&&q.simulationOnly===true&&q.grantId===grantId&&q.missionSHA256===missionSHA256,'NATIVE_SELECTED_MISSION_GRANT');
  for(const[k,v]of Object.entries(context))need(q[k]===v,'NATIVE_SIGNED_SELECTED_CONTEXT:'+k);
  need(Number.isSafeInteger(q.sequence)&&q.sequence>0&&q.sequence<=32768&&q.sequence>(this.sequences.get(grantId)??0),'NATIVE_INPUT_REPLAY');
  need(this.sequences.size<128||this.sequences.has(grantId),'NATIVE_GRANT_GENERATION_CAP');
  need(Array.isArray(q.axes)&&q.axes.length===4&&q.axes.every(x=>typeof x==='number'&&Number.isFinite(x)&&x>=-1&&x<=1),'NATIVE_SIGNED_AXES');
  need(Number.isSafeInteger(q.originalEventUptimeMs)&&q.originalEventUptimeMs>0&&Number.isSafeInteger(q.uiFrameAckElapsedNs)&&q.uiFrameAckElapsedNs>0&&q.observedElapsedNs-q.uiFrameAckElapsedNs>=0&&q.observedElapsedNs-q.uiFrameAckElapsedNs<=200e6,'NATIVE_REAL_UI_FRAME_ACK_200MS');
  const ids=q.activePointerIds;need(Array.isArray(ids)&&ids.length<=2&&ids.every(x=>Number.isInteger(x)&&x>=0&&x<=31)&&new Set(ids).size===ids.length,'NATIVE_POINTER_IDS');
  if(q.sourceKind==='NATIVE_ANDROID_POINTER_STATE_SAMPLE')need(ids.length>0,'NATIVE_NO_POINTER_NO_LEASE');
  else need(q.sourceKind==='NATIVE_ANDROID_POINTER_RELEASE'&&ids.length===0&&q.axes.every(x=>x===0),'NATIVE_RELEASE_CAUSE');
  need(typeof q.nativeJournalGeneration==='string'&&/^[a-f0-9]{32}$/.test(q.nativeJournalGeneration)&&Number.isSafeInteger(q.nativeJournalIntentSequence)&&q.nativeJournalIntentSequence>=1&&q.nativeJournalIntentSequence<=24576&&q.nativeJournalIntentSequence%2===1,'NATIVE_ORIGINAL_AJ02_INTENT_REFERENCE');verifyTouchMapping(q);this.sequences.set(grantId,q.sequence);return result;
 }
}
