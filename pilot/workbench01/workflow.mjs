// UI/workflow state has no transport and never persists authority.
export class Workflow{
 constructor(){this.planSha256=null;this.approved=null;this.phase='plan';this.link=true;this.records=[];this.proposalConsent=null;}
 setPlan(plan){this.planSha256=plan.sha256;this.approved=null;this.records=[];this.proposalConsent=null;this.phase='plan';}
 approve(plan,ready,consent){if(this.planSha256!==plan.sha256||!ready.readyForMock||consent!==true||!this.link)throw Error('MOCK_APPROVAL_REFUSED');this.approved=plan.sha256;this.phase='preflight';}
 start(plan){if(!this.link||this.approved!==plan.sha256||this.planSha256!==plan.sha256)throw Error('MOCK_START_REFUSED');this.phase='fly';}
 end(records){if(this.phase!=='fly')throw Error('MOCK_NOT_RUNNING');this.records=records;this.approved=null;this.phase='review';}
 disconnect(){this.link=false;this.approved=null;this.phase=this.phase==='fly'?'review':this.phase;}
 reconnect(){this.link=true;this.approved=null;}
 restore(plan,records){this.setPlan(plan);this.records=records;this.phase='review';this.approved=null;}
 confirmProposal(proposal,explicit){if(explicit!==true||proposal.planSha256!==this.planSha256||this.phase!=='review')throw Error('REFLY_CONSENT_REQUIRED');this.proposalConsent=proposal.sha256;return {status:'PROPOSAL_CONFIRMED_NO_FLIGHT',proposalSha256:proposal.sha256};}
}
