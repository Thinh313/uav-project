import{unseal,sha}from'../mapping51/common.mjs';
import{make92,stable92}from'../../native/native94/assets/mission92.mjs';
import{FIXTURE92}from'../../native/native94/assets/mission-fixtures92.mjs';
import{compile94}from'../../native/native94/assets/offline94.mjs';
export const PROFILE={id:'WB02_SYNTHETIC_NATIVE92_PREPARATION',version:1,home:FIXTURE92.home,camera:FIXTURE92.camera,aglM:[10,30],speedMps:[.5,2],terrain:'SYNTHETIC_FLAT',flightDispatch:false};
export async function prepareSITL(plan,{confirmSyntheticHomeAmsl10=false}={}){
 unseal(plan);if(plan.operational!==false||plan.provenance!=='SYNTHETIC_FLAT_NADIR')throw Error('SITL_SYNTHETIC_SCOPE');const d=plan.input,o=d.options;
 if(confirmSyntheticHomeAmsl10!==true)throw Error('SITL_EXPLICIT_HOME_AMSL10_CONFIRMATION_REQUIRED');
 if(d.home.lat!==PROFILE.home.lat||d.home.lon!==PROFILE.home.lon)throw Error('SITL_HOME_OUTSIDE_VERIFIED_PROFILE');
 if(stable92(d.camera)!==stable92(PROFILE.camera))throw Error('SITL_CAMERA_PROFILE_MISMATCH');
 if(o.altitudeAglM<10||o.altitudeAglM>30||o.speedMS<.5||o.speedMS>2)throw Error('SITL_PROFILE_RANGE_NO_CLAMP_AGL10_30_SPEED0_5_2');
 if(o.terrain!==PROFILE.terrain||o.datumAcknowledged!==true)throw Error('SITL_DATUM_UNCONFIRMED');
 const mission=await make92({name:plan.acquisition.feature.name.slice(0,80),kml:d.kml,featureId:d.featureId,options:structuredClone(o),camera:structuredClone(d.camera),home:structuredClone(PROFILE.home),altitudeDatum:'RELATIVE_HOME_ON_EXPLICIT_SYNTHETIC_FLAT'}),result=await compile94(mission);
 const binding={workbenchSha256:plan.sha256,kmlSha256:plan.acquisition.sourceSha256,profileSha256:sha(PROFILE),modelSha256:mission.sha256,planSha256:result.compiled.plan.sha256,missionSha256:result.compiled.plan.missionSha256};
 return {format:'wb02-native92-preparation',version:1,operational:false,authorityRestorable:false,firmwareEligibility:'NOT_DISCOVERED_PREPARATION_ONLY',binding,bindingSha256:sha(binding),mission,compiled:result.compiled,flightDispatch:false};
}
export function sitlFixture(kind='polygon'){if(!['polygon','corridor'].includes(kind))throw Error('SITL_FIXTURE_KIND');const{amsl,...home}=FIXTURE92.home;return{kml:FIXTURE92.samples[kind],featureId:'f-0001',home,camera:structuredClone(FIXTURE92.camera),options:{...FIXTURE92.options,altitudeAglM:20,speedMS:2,datumAcknowledged:false}};}
