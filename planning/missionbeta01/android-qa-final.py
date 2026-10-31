import importlib.util,json,time
from pathlib import Path
sp=importlib.util.spec_from_file_location('q',Path(__file__).with_name('android-journey.py'));q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
before=json.loads((q.E/'review-before-android-restart01.json').read_text());s=q.state();after={'reviews':[{k:r.get(k)for k in ['run','accepted','rawHead','planSha256']}for r in s['reviews']],'authority':s['flight']['authority'],'payloadLeases':s['payloadAuthority']['current']['leaseCount']};assert before==after;assert s['client']['active']is False
(q.E/'review-after-android-restart01.json').open('x').write(json.dumps({'status':'PASS_COLD_ANDROID_RESTART_CLOSED_HISTORY_IDENTICAL_NO_AUTHORITY','snapshot':after,'clientActive':s['client']['active']},indent=2));result=[]
for theme in ['night','day']:
 if theme=='day':q.tap('theme')
 for view in ['plan','preflight','fly','review']:
  q.tap('nav-'+view);v=q.obs();assert not v['geometry']['horizontalOverflow']and not v['geometry']['panelOverflow'];critical={k:c for k,c in v['controls'].items()if k in ['theme','workspace','nav-plan','nav-preflight','nav-fly','nav-review','fit','zoom-in','zoom-out','layers','details','compile','approve','b-arm','b-auto','b-pause','b-resume','b-rtl','beta-export-raw']and c['w']>0};assert all(c['w']>=48 and c['h']>=48 for c in critical.values());image=q.shot('qa-%s-%s01.png'%(theme,view));result.append({'theme':theme,'view':view,'geometry':v['geometry'],'criticalControls':critical,'screenshot':image})
 q.tap('workspace');v=q.obs();assert v['controls']['close-modal']['visible'];image=q.shot('qa-%s-workspace01.png'%theme);result.append({'theme':theme,'view':'workspace-modal','geometry':v['geometry'],'screenshot':image});q.tap('close-modal')
q.tap('theme');(q.E/'android-ui-qa01.json').open('x').write(json.dumps({'status':'PASS_RECORDED_GEOMETRY_AND_CRITICAL_TARGETS_VISUAL_REVIEW_PENDING','viewport':{'width':1280,'height':800},'results':result,'otherDevices':'NOT_CHECKED','independentHumanQA':False},indent=2));print('ANDROID_QA_CAPTURED',len(result))
