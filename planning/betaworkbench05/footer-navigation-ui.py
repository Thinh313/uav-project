from pathlib import Path
import importlib.util,time,json
p=Path(__file__).with_name('actual-ui-journey.py');s=importlib.util.spec_from_file_location('q',p);q=importlib.util.module_from_spec(s);s.loader.exec_module(q);q.step=6000;rows=[]
plan=['Diện tích mẫu','GSD dự kiến','Vị trí chụp','Độ phủ đạt mẫu','Lượt dự kiến'];flight=['Cao / Home','Tốc độ đất','Trạng thái','Nguồn bay','Quyền payload']
try:
 q.tap('nav-plan');q.check('datum');q.tap('compile')
 for theme in ['night','day']:
  if theme=='day':q.tap('theme')
  for view in ['fly','plan','preflight','fly','review']:
   q.tap('nav-'+view);v=q.obs();f=v['footer'];want=flight if view=='fly'else plan;assert [x['label']for x in f]==want,(view,f)
   if view!='fly':assert f[0]['value'].endswith(' ha')and f[1]['value'].endswith(' cm/px'),f
   assert not v['geometry']['horizontalOverflow']and not v['geometry']['panelOverflow']
   rows.append({'theme':theme,'view':view,'footer':f,'geometry':v['geometry']});name='android-footer-'+theme+'-'+view+'-'+str(len(rows))+'.png';(q.E/name).open('xb').write(q.adb('exec-out','screencap','-p'))
 (q.E/'android-footer-navigation01.json').open('x').write(json.dumps({'status':'PASS','source':'ACTUAL_ANDROID_WEBVIEW_MOCK_HOST_NO_AP','rows':rows,'requirements':['correct_labels','correct_units_after_fly','no_horizontal_overflow']},indent=2));print('ANDROID_FOOTER_LABELS_UNITS_NAVIGATION10_PASS')
except BaseException as e:q.log('FOOTER_UI_FAILURE',{'error':str(e)});raise
