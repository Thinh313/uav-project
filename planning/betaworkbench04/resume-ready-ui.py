from pathlib import Path
import importlib.util,time
f=Path(__file__).with_name('actual-ui-journey.py');spec=importlib.util.spec_from_file_location('qa04_ui',f);q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q);q.step=100
try:
 s=q.state();assert s['flight']['source']=='OBSERVED_OWNED_SITL'and s['flight']['live']['stage']=='DISARMED'and not s['flight']['authority'];q.log('STARTUP_REASSESSMENT',{'run':s['flight']['run'],'reason':'Initial assessment correctly blocked while GNSS/EKF/Home were starting; no grant/arm was sent'})
 q.tap('b-preflight');q.wait(lambda s:s['flight']['preflight']['ready'],20);q.tap('b-grant');q.wait(lambda s:s['flight']['authority']is not None);q.tap('b-upload');q.wait(lambda s:s['flight']['live']['readback63']);q.tap('b-arm');s=q.wait(lambda s:s['flight']['live']['stage']=='ARMED_HOME_REVIEW');v=q.obs();h=s['flight']['homeReview'];assert h['sha256'][:10]in(v['homeText']or'');q.log('AUTOMATED_SIM_HOME_REVIEW',{'shown':v['homeText'],'reviewSha256':h['sha256'],'scope':'AUTOMATED_QA_NOT_HUMAN_OR_HERA_APPROVAL'});q.check('b-home-after');q.tap('b-auto');q.wait(lambda s:s['flight']['live']['stage']=='AUTO');q.log('AUTO_OBSERVED',{'run':s['flight']['run']})
 q.tap('b-discover');q.tap('b-select');q.tap('b-payload-grant');q.tap('b-gimbal');q.tap('video-capture');q.wait(lambda s:len(s['captures'])>0);q.wait(lambda s:s['flight']['completion']['complete'],150)
 q.tap('video-save');q.tap('b-close');q.wait(lambda s:len(s['reviews'])>0);q.log('NOMINAL_REVIEW',q.state()['reviews'][-1]);print('NOMINAL_UI_COMPLETE',flush=True)
except BaseException as e:q.log('RESUME_FAILURE',{'error':str(e)});raise
