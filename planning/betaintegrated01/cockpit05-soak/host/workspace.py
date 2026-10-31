"""Pure content-addressed inventory/preservation checks for05 workspace snapshots."""
import hashlib,json,re


def inventory(files):
    if type(files)is not dict or len(files)>128:raise ValueError('WORKSPACE_FILE_COUNT')
    entries={};revisions=[];mock=[];total=0
    for name,body in files.items():
        if type(name)is not str or '/'in name or type(body)is not bytes or len(body)>2**20:raise ValueError('WORKSPACE_MEMBER_BOUND')
        total+=len(body)
        if total>8*2**20:raise ValueError('WORKSPACE_SNAPSHOT_BOUND')
        sha=hashlib.sha256(body).hexdigest();value=json.loads(body)
        if name.startswith('draft-'):
            m=re.fullmatch(r'draft-(\d{6})-([0-9a-f]{64})\.json',name)
            if not m or m[2]!=sha or value.get('revision')!=int(m[1]):raise ValueError('DRAFT_CONTENT_ADDRESS_REVISION')
            revisions.append(value['revision'])
        elif name.startswith('review-'):
            if not name.endswith('-'+sha+'.json'):raise ValueError('REVIEW_CONTENT_ADDRESS')
            if 'MOCK'in str(value.get('name',''))or'MOCK'in str(value.get('id',''))or'MOCK'in str(value.get('run','')):
                if value.get('actualImages')!=0 or value.get('authorityRestorable')is not False or value.get('completionClaim')is not False or value.get('status')not in('FAILED','UNKNOWN','UNKNOWN_PENDING_GROUND_VERIFICATION','PENDING_NATIVE_TERMINAL_OR_VERIFICATION'):raise ValueError('MOCK_RECORD_CLAIM')
                mock.append(name)
        else:raise ValueError('EXPLICIT_DRAFT_REVIEW_SNAPSHOT_ONLY')
        entries[name]=sha
    return {'entries':entries,'draftRevisions':sorted(revisions),'MOCKReviews':mock,'bytes':total,'source':'ROOT_PRIVATE05_READ_ONLY_SNAPSHOT_NOT_NATIVE_FLIGHT_EVIDENCE'}


def verify_preserved(before,after,*,actualDraftRevision=6,requireNewDraft=True):
    if before['draftRevisions']!=[1,2,3,4,5]or len(before['MOCKReviews'])!=3:raise ValueError('EXPECTED_PRIOR05_MOCK_BASELINE')
    changed=[p for p,h in before['entries'].items()if after['entries'].get(p)!=h]
    if changed:raise ValueError({'PRIOR_WORKSPACE_REMOVED_OR_CHANGED':changed})
    if type(actualDraftRevision)is not int or actualDraftRevision!=6:raise ValueError('ACTUAL_SEPARATE_REVISION6_REQUIRED')
    if requireNewDraft and actualDraftRevision not in after['draftRevisions']:raise ValueError('NEW_ACTUAL_DRAFT6_NOT_OBSERVED')
    return {'status':'PRIOR05_WORKSPACE_EXACT_BYTES_PRESERVED','files':len(before['entries']),'priorRevisions':before['draftRevisions'],'priorMOCKReviewCount':3,'newActualDraftRevision':actualDraftRevision if actualDraftRevision in after['draftRevisions']else None,'priorMOCKReviewsPromoted':False,'flightAccepted':False}
