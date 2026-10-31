"""Pure helper-policy checks. Does not call ADB or create runtime evidence."""
from pathlib import Path
import importlib.util,json,ast
p=Path(__file__).with_name('qa-runtime.py');spec=importlib.util.spec_from_file_location('runtime04',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);g=m.GIB;tests=[]
def reject(label,fn):
    try:fn();raise AssertionError('MUST_REJECT_'+label)
    except(AssertionError,RuntimeError)as e:
        assert not str(e).startswith('MUST_REJECT_');tests.append(label)
s=[{'mono':i,'free':30*g}for i in range(31)];m.budget_decision(s);tests.append('31_samples30seconds29GiB')
reject('fewer_samples',lambda:m.budget_decision(s[:-1]));reject('compressed_time',lambda:m.budget_decision([{**x,'mono':x['mono']/2}for x in s]));reject('under29',lambda:m.budget_decision([{**x,'free':28*g}for x in s]));reject('peak_then_decline',lambda:m.budget_decision([{**x,'free':30*g+(512*2**20 if i==15 else 0)}for i,x in enumerate(s)]));m.trend_decision([],0,29*g);tests.append('normal_runtime');reject('under28',lambda:m.trend_decision([],1,28*g-1));reject('forecast_below20',lambda:m.trend_decision([(0,31*g)],1,30*g));plan=m.plan();assert plan['cachedAPI']==33 and plan['hardDurationS']==1200 and plan['pollMs']==250 and plan['command'].count('-no-snapshot')==1 and plan['command'][plan['command'].index('-cores')+1]=='4';tests.append('declared_API33_4CPU2GiB_no_snapshot');print(json.dumps({'status':'PASS','checks':len(tests),'cases':tests,'runtimeStarted':False,'adbCalls':0},indent=2))
