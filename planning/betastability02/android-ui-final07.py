"""Record actual Android geometry/screenshots. Human QA is not implied."""
import importlib.util,json
from pathlib import Path
sp=importlib.util.spec_from_file_location('saf',Path(__file__).with_name('saf-helpers.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);q=h.q
assert q.state()['flight']['authority'] is None
result=[]
for theme in ['night','day']:
 if theme=='day':q.tap('theme')
 for view in ['plan','preflight','fly','review']:
  q.tap('nav-'+view);v=q.obs();assert not v['geometry']['horizontalOverflow']and not v['geometry']['panelOverflow']
  critical={k:c for k,c in v['controls'].items()if k in ['theme','workspace','nav-plan','nav-preflight','nav-fly','nav-review','fit','zoom-in','zoom-out','layers','details','compile','approve','b-arm','b-auto','b-pause','b-resume','b-rtl','beta-export-raw']and c['w']>0}
  assert all(c['w']>=48 and c['h']>=48 for c in critical.values()),critical
  image=q.shot('qa-%s-%s07.png'%(theme,view));result.append({'theme':theme,'view':view,'geometry':v['geometry'],'criticalControls':critical,'screenshot':image})
 q.tap('workspace');v=q.obs();assert v['controls']['close-modal']['visible'];image=q.shot('qa-%s-workspace07.png'%theme);result.append({'theme':theme,'view':'workspace-modal','geometry':v['geometry'],'screenshot':image});q.tap('close-modal')
q.tap('theme');h.save_receipt('android-ui-qa07.json',{'status':'PASS_RECORDED_GEOMETRY_AND_CRITICAL_TARGETS_VISUAL_REVIEW_PENDING','viewport':{'width':1280,'height':800},'results':result,'otherDevices':'NOT_CHECKED','independentHumanQA':False})
print('ANDROID_QA_CAPTURED',len(result),flush=True)
