"""Pure mock AP admission replay; no current run or runtime read."""
from pathlib import Path
import importlib.util,json,copy
spec=importlib.util.spec_from_file_location('admission05',Path(__file__).with_name('qa-ap-admission.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);g=m.GIB;a={'durationMs':30001,'minimumBytes':29*g,'samples':[{'hostMonoMs':i*1000,'freeBytes':30*g}for i in range(31)]};cases=[]
def reject(name,v):
 try:m.admission_decision(v);raise RuntimeError('MUST_REJECT')
 except AssertionError:cases.append(name)
m.admission_decision(a);cases.append('valid31samples30s29GiB');reject('short31samplewindow',{**a,'samples':[{**x,'hostMonoMs':x['hostMonoMs']/2}for x in a['samples']]});reject('declaredshort',{**a,'durationMs':29999});reject('only30samples',{**a,'samples':a['samples'][:-1]});reject('under29',{**a,'samples':[{**x,'freeBytes':29*g-1}for x in a['samples']]});reject('peak_decline_not_just_firstlast',{**a,'samples':[{**x,'freeBytes':30*g+(512*2**20 if i==15 else 0)}for i,x in enumerate(a['samples'])]});reject('NaNclock',{**a,'samples':[{**x,'hostMonoMs':float('nan')if i==15 else x['hostMonoMs']}for i,x in enumerate(a['samples'])]});reject('nonmonotonic',{**a,'samples':[{**x,'hostMonoMs':-1 if i==15 else x['hostMonoMs']}for i,x in enumerate(a['samples'])]});print(json.dumps({'status':'PASS','checks':len(cases),'cases':cases,'runtimeStarted':False,'adbCalls':0},indent=2))
