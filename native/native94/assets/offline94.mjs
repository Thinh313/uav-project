import{parseKml94}from'./offline94/kml.mjs';import{compile}from'./offline94/auto.mjs';import{validate92,stable92}from'./mission92.mjs';
export async function inspect94(model){await validate92(model);return{ok:true,modelSha256:model.sha256,document:parseKml94(model.draft.kml)};}
export async function compile94(model){await validate92(model);const d=model.draft,plan=await compile({...d,homeConfirmed:d.options.datumAcknowledged});return{ok:true,compiled:{modelSha256:model.sha256,modelRevision:model.revision,plan}};}
export async function replay94(w){if(w.compiled&&stable92((await compile94(w.mission)).compiled)!==stable92(w.compiled))throw Error('LOCAL_COMPILE_REPLAY_MISMATCH');return w;}
export async function attest94(controller){
 if(controller.local94)throw Error('OFFLINE_PLANNING_NO_FLIGHT_TRANSPORT');
 if(controller.dirty||controller.blocked||controller.live?.run||!controller.doc?.compiled)throw Error('COMMITTED_IDLE_PLAN_REQUIRED');
 const w=await replay94(await controller.validate94(controller.doc));
 const snapshot=stable92(w),head=controller.head;
 const actual=await controller.host('mission-compile',{model:w.mission});
 if(head!==controller.head||snapshot!==stable92(controller.doc)||stable92(actual.compiled)!==stable92(w.compiled))throw Error('HOST_ATTESTATION_PLAN_MISMATCH');
 controller.update(await controller.host('state'));return actual;
}
