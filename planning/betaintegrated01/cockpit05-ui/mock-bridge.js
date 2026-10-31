/* Presentation-only local mock. No Android/native/wire/network/persistence capability. */
(function () {
  'use strict';
  const epoch = 5, allowed = new Set(['LOAD', 'STATE', 'SAVE_DRAFT', 'NAVIGATE', 'REVIEWS']);
  let selectedView = 'review', sequence = 0, emitted = 0;
  const draft = {version:1,id:'survey-ui-mock',revision:1,kind:'polygon',name:'Khảo sát giao diện mẫu',datum:'WGS84',altitudeDatum:'RELATIVE_HOME',units:'m',geometry:[[10.85394,106.80694],[10.85394,106.80712],[10.85412,106.80712],[10.85412,106.80694]],altitudeM:3,corridorWidthM:10,trainingOnly:true};
  const rows = ['m1cockpit03-nominal01', 'm1cockpit03-nominal02'].map((id, i) => ({id,run:id,epoch:'mock-epoch',boot:'mock-boot',generation:'mock-generation',surveyRevision:1,surveySHA256:'0'.repeat(64),nativeTerminalSHA256:null,status:i?'UNKNOWN_PENDING_GROUND_VERIFICATION':'FAILED',groundDistinctFreshGroups:0,completionClaim:false,coverageClaim:false,authorityRestorable:false,actualImages:0,trajectory:[],mockOnly:true}));
  const workspace = {draft,draftSHA256:'0'.repeat(64),reviews:rows,authorityRestorable:false};
  const copy = value => JSON.parse(JSON.stringify(value));
  function data() { emitted = Math.max(emitted + 1, Math.round(performance.now() * 1e6)); return {chosenView:selectedView,presentedView:selectedView,viewReady:true,viewEpoch:epoch,workspace:copy(workspace),native:{phase:'NO_SESSION',authorityRestorable:false},nowElapsedNs:emitted,nativeObservedElapsedNs:0,noMedia:true,ownerActive:false,trajectory:[],mockOnly:true}; }
  function deliver(id, type, ok, error, detail) { setTimeout(() => { const snapshot=data(); if(type==='REVIEWS') snapshot.selectedReview=detail?copy(detail):null; window.AerisCockpit.receive({version:1,id,viewEpoch:epoch,type,ok,error:error||null,data:snapshot}); },0); }
  window.AerisWorkspace = Object.freeze({post(message) {
    let input;
    try {
      if(typeof message!=='string'||message.length>16384)throw new Error('Yêu cầu mock vượt giới hạn.');
      input=JSON.parse(message); const match=new RegExp('^ui-'+epoch+'-([1-9][0-9]*)$').exec(input.id||'');
      if(input.version!==1||input.viewEpoch!==epoch||!match||Number(match[1])<=sequence||!allowed.has(input.type))throw new Error('Mock chỉ nhận yêu cầu giao diện trong phiên hiện tại.');
      sequence=Number(match[1]);
      if(input.type==='NAVIGATE'){if(!['survey','preflight','fly','review'].includes(input.payload.view))throw new Error('Màn hình mock không hợp lệ.');selectedView=input.payload.view;}
      if(input.type==='SAVE_DRAFT'){const next=window.AerisUIModel.validateDraft(input.payload);if(next.revision!==workspace.draft.revision)throw new Error('Revision mock đã thay đổi.');workspace.draft={...next,id:draft.id,revision:next.revision+1,version:1,trainingOnly:true};workspace.draftSHA256='0'.repeat(64);}
      deliver(input.id,input.type,true,null,input.type==='REVIEWS'?rows.find(row=>row.id===input.payload.id):null);
    } catch(error) { if(input&&typeof input.id==='string')deliver(input.id,input.type||'STATE',false,String(error.message)); }
  }});
  document.addEventListener('DOMContentLoaded', () => deliver('BOOT','LOAD',true));
})();
