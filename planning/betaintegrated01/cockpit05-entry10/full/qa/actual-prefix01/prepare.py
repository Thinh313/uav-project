from pathlib import Path
import hashlib,json,ast
R=Path(__file__).resolve().parents[6];S=R/'planning/betaintegrated01/cockpit05-entry10/runtime/verify_capture.py';text=S.read_text();prefix=text[:text.index('    # AP stage groups stream')]
prefix=prefix.replace('from .journal import verify_journal',"from importlib import import_module\nverify_journal=import_module('planning.betaintegrated01.cockpit05-entry10.runtime.journal').verify_journal")
prefix=prefix.replace('def verify_capture(', 'def verify_prefix(').replace("    assert phase == 'RX' and len(origins) == 1 and stage_rows == frame == journal['frames']", "    assert phase == 'SENT' and len(origins) == 1 and stage_rows == frame == journal['frames'] and journal['pendingPhase']=='UNKNOWN' and journal['unknownSends']==1")
prefix=prefix.replace("                elif kind == 'EVENT':", "                elif kind == 'UNKNOWN':\n                    assert phase=='SENT' and body['frame']==frame and payload=={'errorType':'ValueError','reason':'SEND_RAISED','sendCalled':True}\n                elif kind == 'EVENT':")
prefix+='''    return dict(status='EXACT_COMPLETE_SENT_PREFIX_MODEL_CLOCK_BYTES_ONLY',completeFrames=frame,stageRows=stage_rows,unknownTailFrame=frame,unknownTailModelIntentMatched=True,journal=journal,APstage=stage,clockRegistered=clock_registered,clockMatched=clock_matched,maximumFrameGroupNs=maximum_group_ns,actualThirtyMinuteAccepted=False,wholeBetaAccepted=False)
'''
ast.parse(prefix);Q=Path(__file__).parent;P=Q/'model_clock_prefix.py';P.open('x').write(prefix)
(Q/'derivation.json').open('x').write(json.dumps({'originalFrozenSource':str(S.relative_to(R)),'originalSHA256':hashlib.sha256(S.read_bytes()).hexdigest(),'derivedSHA256':hashlib.sha256(prefix.encode()).hexdigest(),'changes':['Importexplicitnewstrictjournal','Renameverify_prefix','AcceptONLYonefinalValueError/SEND_RAISED/UNKNOWNtailinsteadcompletephase','Returntruthfulincompleteprefixresult; separateAPgroupaudit required'],'modelClockLoopOtherwiseExact':True,'rawCopies':0,'execution':'NOT_RUN_BY_PREPARATION'},indent=2)+'\n')
print('PREPARED_QA_ONLY_PREFIX_NO_RAW_EXECUTION')
