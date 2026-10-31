"""Current APK02 source consumer review: no Android/AP/socket launch or product edit."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess

R=Path(__file__).resolve().parents[4]
P=R/'planning/betaintegrated01/m1control02/native'
E=R/'evidence/betaintegrated01-m1control02/native/review01'
W=R/'native/betaintegrated01/.build/control02-native-review'
J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    free=shutil.disk_usage(R).free
    assert free>=20*2**30 and not W.exists()
    E.mkdir(parents=True,exist_ok=False);W.mkdir()
    receipt=json.loads((R/'evidence/betaintegrated01-m1control01/native/build-02.json').read_text())
    assert all(sha(R/path)==digest for path,digest in receipt['sourcePins'].items())
    sources=[R/path for path in receipt['sourcePins'] if path.endswith('.java') and Path(path).name not in ['ControlActivity.java','ControlConfig.java','ControlOwner.java','TouchControls.java','PendingExplicitAction.java']]
    shared=R/'planning/betaintegrated01/m1control01/qa'
    sources += [shared/'ProfileFixture.java',shared/'SessionQA.java',P/'ReleaseLandReview.java']
    pins={str(p.relative_to(R)):sha(p)for p in sources}
    activity=(R/'native/betaintegrated01/control01/src/vn/rtr/aeris/control01/ControlActivity.java').read_text()
    touch=(R/'native/betaintegrated01/control01/src/vn/rtr/aeris/control01/TouchControls.java').read_text()
    static=[]
    def check(name,ok):
        static.append({'id':name,'pass':bool(ok),'scope':'SOURCE_STRUCTURE_NOT_ANDROID_CALLBACK_PROOF'})
    check('UI_UP_STOP_THEN_REAL_STATE_SAMPLE', 'public void released(){stopProducer();sampleNow();}' in activity)
    check('UI_CONSENT_SAMPLE_QUEUED_BEFORE_ACTION_THEN_PRODUCER', 'sampleNow();long at=SystemClock.elapsedRealtimeNanos();owner.action(action,' in activity and 'if("CONSENT".equals(action))startProducer();' in activity)
    check('TOUCH_UP_CENTERS_BOTH_AND_SETS_SINGLE_PENDING_RELEASE', 'clear();releasePending=true;sink.released();' in touch and 'boolean release=releasePending;releasePending=false;' in touch)
    check('UI_PRODUCER_USES_FRESH_CLOCKS_AND_PRESERVES_LAST_MOTION_TIME', 'SystemClock.uptimeMillis()*1000000L;long elapsed=SystemClock.elapsedRealtimeNanos();' in touch and 'lastMotionUptime,axes' in touch)
    check('LAND_UI_ONLY_AFTER_RC_CLEANUP_AND_NEW_CONSENT', 'buttons.get("LAND").setEnabled(opened&&consent&&armed&&!s.optBoolean("rcOverrideActiveLocally"))' in activity)
    check('HOME_CLICK_BINDS_DISPLAYED_CANDIDATE_NOT_UNSEEN_NEW_FETCH', 'owner.action(action,"touch-action-"+UUID.randomUUID(),displayedHomeHash,at)' in activity and 'displayedHomeHash=f.optString("homeHash",null)' in activity)
    logs=[];results=[];class_count=0
    try:
        cmd=[J/'javac','--release','8','-d',W,*sources]
        p=subprocess.run([str(x)for x in cmd],cwd=R,capture_output=True,text=True,timeout=60);logs.append({'argv':[str(x)for x in cmd],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
        if p.returncode==0:
            cmd=[J/'java','-cp',W,'ReleaseLandReview',E/'fixtures']
            p=subprocess.run([str(x)for x in cmd],cwd=R,capture_output=True,text=True,timeout=90);logs.append({'argv':[str(x)for x in cmd],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
            if p.returncode==0:
                results=json.loads(p.stdout)['results']
    finally:
        class_count=len(list(W.rglob('*.class')));shutil.rmtree(W)
    after={str(p.relative_to(R)):sha(p)for p in sources}
    unchanged=all(sha(R/path)==digest for path,digest in receipt['sourcePins'].items())
    out={'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS_SCOPED_NATIVE_REVIEW' if results and all(x['pass']for x in results+static)and after==pins and unchanged else'FAIL',
         'staticChecks':static,'results':results,'commands':logs,'sourceBefore':pins,'sourceAfter':after,'sourceChanged':pins!=after,'APK02AllInputPinsUnchanged':unchanged,
         'sourceReuse':'PreviousQA ProfileFixture/SessionQA.F scaffolding reused; new Builder checks are not an independent QA claim',
         'currentAPK':{'path':receipt['apk'],'sha256':receipt['sha256']},'runtimeLaunches':{'Android':0,'AP':0,'socket':0,'ADB':0},'builds':{'APK':0,'AP':0,'pureJVMCompilation':True},
         'removedClassFiles':class_count,'scratchPath':str(W.relative_to(R)),'scratchExistsAfter':W.exists(),'freeBytesBefore':free,
         'limits':['Source UI coherence is not actual Android callback proof','Mock AP observed mode17 is not evidence of physical/AP response or RCtimeout behavior','Kernel/remote packet age is not measured','No hardware/manualHID/flight/Beta readiness claim']}
    (E/'results.json').open('x').write(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'mockGroups':len(results),'staticGroups':len(static),'failed':[x['id']for x in results+static if not x['pass']],'sourceChanged':out['sourceChanged']}))
    raise SystemExit(0 if out['status'].startswith('PASS') else 1)


if __name__=='__main__':main()
