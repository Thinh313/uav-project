from pathlib import Path
import copy,hashlib,json,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent));from combined_oracle import *
O=R/'evidence/betaintegrated01-m1cockpit04/qa/combined-mock02';O.mkdir();start=10*NS;cut=start+1802*NS;rows=[]
for quarter in range(1802*4+1):
 at=start+quarter*250_000_000
 if quarter%4==0:rows.append(dict(kind='heartbeat',hostNs=at,mode=17,armed=True))
 if quarter%2==0:rows.append(dict(kind='landed',hostNs=at,state=2))
 rows.append(dict(kind='position',hostNs=at,bootMs=at//1_000_000,relativeMm=3000))
commands=[dict(kind='RC_OVERRIDE',hostNs=start-3*NS,forwardPitchHeld=True,channels=[1500,1425,1500,1500]+[65535]*14,wireSHA256='a'*64),dict(kind='COMMAND_LONG',hostNs=start-2*NS,command=176,params=[1,17,0,0,0,0,0],wireSHA256='b'*64),dict(kind='RC_OVERRIDE',hostNs=start-1500_000_000,forwardPitchHeld=False,channels=[1500]*4+[65535]*14,wireSHA256='c'*64),dict(kind='RC_OVERRIDE',hostNs=start-NS,forwardPitchHeld=False,channels=[0]*8+[65534]*10,wireSHA256='d'*64)]
wire=dict(passiveTimeline=rows,nativeForwardedTimeline=commands,cutClosedHostNs=cut,passiveApplicationTXBytes=0);tx={'b'*64:[(20,NS,21,NS+10)],'c'*64:[(23,NS+30,24,NS+40)],'d'*64:[(25,NS+50,26,NS+60)]};hb=[dict(record=22,guestNs=NS+20,mode=17,armed=True,validType=True)];cleanup=cleanup_witness(wire,tx,hb);window=assisted_window(rows,start,cut);base=dict(status='CONTROL_NOT_READY',control=dict(criteria={k:True for k in BASE}));base['control']['criteria']['forwardHeldAtCut']=False
native=dict(consents=[dict(record=10,event=dict(leaseId='lease1')),dict(record=27,event=dict(leaseId='lease2'))],revokes=[dict(record=19,event=dict(previouslyActive=True,previousLeaseId='lease1'))],UP=[dict(record=18)],secondLeaseProducerWindowNs=1802*NS,secondLeaseUptimeWindowNs=1802*NS,maxLease2ProducerGapNs=50_000_000,lease2NeutralThroughout=True,neutralAtFailure=True,postFailureTXIntents=0,authorityRestored=False,failures=[dict(event=dict(reason='IOException:CONTROL_AP_EOF'))],terminal=dict(event=dict(reason='CONTROL_FAILED_RESOURCES_CLOSED')),pilotBindingsAfterFirstRelease=0);clocks=dict(APGuestWindowNs=1802*NS,modelWindowNs=1802*NS);restart=dict(exactSHA=True,NO_SESSION=True,ownerActive=False,bindingStagedSHA256=None,newViewEpoch=True)
def qualify(**kw):
 args=dict(base=base,wire=wire,native=native,window=window,clocks=clocks,cleanup=cleanup,restart=restart);args.update(kw);return qualify_facts(**args)
tests=[]
def ck(name,p):tests.append(dict(id=name,pass_=bool(p)))
ck('baselineSyntheticFactsOnly',qualify()['status'].startswith('COMBINED_FACTS_PASS')and qualify()['actualThirtyMinuteAccepted']is False)
for key in ['APGuestWindowNs','modelWindowNs']:
 c=copy.deepcopy(clocks);c[key]=MIN-1;ck('oneNanosecondShort:'+key,qualify(clocks=c)['status']=='COMBINED_NOT_READY')
for key in ['secondLeaseProducerWindowNs','secondLeaseUptimeWindowNs']:
 n=copy.deepcopy(native);n[key]=MIN-1;ck('oneNanosecondShort:'+key,qualify(native=n)['status']=='COMBINED_NOT_READY')
for key,value in [('maxLease2ProducerGapNs',200_000_001),('lease2NeutralThroughout',False),('neutralAtFailure',False),('postFailureTXIntents',1)]:
 n=copy.deepcopy(native);n[key]=value;ck('nativeNegative:'+key,qualify(native=n)['status']=='COMBINED_NOT_READY')
b=copy.deepcopy(base);b['control']['criteria']['forwardHeldAtCut']=True;ck('oldHeldForwardCannotMasquerade',qualify(base=b)['status']=='COMBINED_NOT_READY');b=copy.deepcopy(base);b['control']['criteria']['GCSFailsafeTextAfterCut']=False;ck('missingGCSFailsafeRejects',qualify(base=b)['status']=='COMBINED_NOT_READY');b=copy.deepcopy(base);del b['control']['criteria']['noNativeLandCommandConfounder'];ck('missingBaseCriterionRejects',qualify(base=b)['status']=='COMBINED_NOT_READY')
for field,value in [('ownerActive',True),('bindingStagedSHA256','a'*64),('exactSHA',False),('newViewEpoch',False)]:
 v=copy.deepcopy(restart);v[field]=value;ck('restartNegative:'+field,qualify(restart=v)['status']=='COMBINED_NOT_READY')
bad=copy.deepcopy(rows);next(x for x in bad if x['kind']=='heartbeat'and x['hostNs']==start+100*NS)['mode']=9;ck('badModeInsideCannotPickSubwindow',assisted_window(bad,start,cut)['status']=='NOT_READY');bad=copy.deepcopy(rows);bad=[r for r in bad if not(start+100*NS<=r['hostNs']<=start+101*NS)];ck('oneSecondGapRejects',assisted_window(bad,start,cut)['status']=='NOT_READY');bad=copy.deepcopy(rows);next(x for x in bad if x['kind']=='landed'and x['hostNs']==start+NS)['state']=1;ck('airborneContradictionRejects',assisted_window(bad,start,cut)['status']=='NOT_READY')
badwire=copy.deepcopy(wire);badwire['nativeForwardedTimeline'].append(dict(kind='RC_OVERRIDE',hostNs=cut-NS,forwardPitchHeld=False,channels=[1550]*4+[65535]*14,wireSHA256='e'*64));ck('extraRCAfterCleanupRejects',cleanup_witness(badwire,tx,hb)['status']=='NOT_READY');badhb=hb+[dict(record=22.5,guestNs=NS+21,mode=5,armed=True,validType=True)];ck('newerContradictoryNativeHBRejects',cleanup_witness(wire,tx,badhb)['status']=='NOT_READY')
n=copy.deepcopy(native);n['consents']=[];ck('noGrantsRejectsWithoutCrash',qualify(native=n)['status']=='COMBINED_NOT_READY');n=copy.deepcopy(native);n['pilotBindingsAfterFirstRelease']=1;ck('pilotAfterUPRejects',qualify(native=n)['status']=='COMBINED_NOT_READY');n=copy.deepcopy(native);n['failures'][0]['event']['reason']='JOURNAL_QUOTA';ck('quotaFailureNotLinkLoss',qualify(native=n)['status']=='COMBINED_NOT_READY');b=copy.deepcopy(base);before=copy.deepcopy(b);qualify(base=b);ck('oldOutcomeUnmutated',b==before)
r=dict(status='PASS_PURE_FACTS_NOT_ACTUAL_RUNTIME'if all(t['pass_']for t in tests)else'FAIL',tests=tests,baseline=qualify(),syntheticPositionRows=len(rows),servicesStarted=0,sourceSHA256=hashlib.sha256(Path(__file__).with_name('combined_oracle.py').read_bytes()).hexdigest(),scope='Synthetic clocked fact fixtures/adversarial bounds, NOT real walltime/AP/native execution or30minute acceptance.');(O/'results.json').open('x').write(json.dumps(r,indent=2));print(r['status'],len(tests),[x['id']for x in tests if not x['pass_']])
