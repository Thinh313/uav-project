"""Actual Android observer/audio gesture, data-link loss and safe LAND/end.
Native ADB screenshots only; no WebView DOM, CDP or browser permission workaround.
"""
import ast
from pathlib import Path
p=Path(__file__).with_name('full-manual-ui.py');tree=ast.parse(p.read_text());prefix=[]
for n in tree.body:
 if isinstance(n,ast.Try):break
 prefix.append(n)
exec(compile(ast.Module(body=prefix,type_ignores=[]),str(p)+'#definitions-only','exec'),globals())
import hashlib
LABEL='media05'
def capture(n):
 w=adb('shell','dumpsys','window').decode();assert re.search('mCurrentFocus=.*vn.rtr.aeris.simhand01/',w)
 b=adb('exec-out','screencap','-p');(E/(n+'.png')).open('xb').write(b);return Image.open(io.BytesIO(b)).convert('RGB')
def mask(im):return tuple(all(c>180 for c in v)for v in im.crop((1150,55,1170,75)).getdata())
def icon_audio():
 ref=Image.open(E/'visual-observer03/after.png').convert('RGB');expected=mask(ref);assert sum(expected)>12
 end=time.monotonic()+8
 while True:
  w=adb('shell','dumpsys','window').decode();assert re.search('mCurrentFocus=.*vn.rtr.aeris.simhand01/',w)
  b=adb('exec-out','screencap','-p');im=Image.open(io.BytesIO(b)).convert('RGB')
  if mask(im)==expected:break
  assert time.monotonic()<end,'OBSERVED_MUTE_ICON_NOT_CONFIRMED_NO_TAP';time.sleep(.2)
 (E/'media05-before-audio.png').open('xb').write(b);save('media05-audio-intent',{'source':'INSPECTED_ACTUAL_NATIVE_SCREENSHOT_FOREGROUND_MASK','reference':'visual-observer03/after.png','maskRegion':[1150,55,1170,75],'matchedForegroundPixels':sum(expected),'x':1160,'y':65,'action':'ONE_TRUSTED_AUDIO_ENABLE_TAP','authorityRestored':False});adb('shell','input','tap',1160,65);time.sleep(.7);im=capture('media05-after-audio');assert mask(im)!=expected,'AUDIO_ICON_DID_NOT_CHANGE';return True
s=state();assert s['lifecycle']['closed']and not s['controllerActive']
adb('shell','am','force-stop','vn.rtr.aeris.simhand01');adb('shell','am','start','-W','-n','vn.rtr.aeris.simhand01/.ShellActivity','--es','initialPath','/phone')
tap('media05-start',285,399,'evidence/simstability03/android-open01/001-after-open.png',[129,375,443,423]);tap('media05-pre',61,354,'evidence/simstability03/android-open01/001-after-open.png',[35,328,87,380]);tap('media05-reference',141,495,'evidence/simstability03/visual-pre02/after.png',[129,484,152,507]);step('media05-scroll','scroll',107,166,466,608)
s=waitfor(lambda s:bool((s.get('vehicle')or{}).get('home'))and bool(s['preflight']['checks'])and all(c['pass']for c in s['preflight']['checks']if c['id']!='configuration'),95);save('media05-home-observed',s);assert s['vehicle']['home']['horizontalDeltaM']<1 and abs(s['vehicle']['home']['amslDeltaM'])<.5
tap('media05-home',141,370,'evidence/simstability03/visual-scroll02/after.png',[129,359,152,382]);tap('media05-refresh',201,247,'evidence/simstability03/visual-scroll02/after.png',[130,224,272,270],True);waitfor(lambda s:s['preflight']['ready'],4);tap('media05-approve',285,433,'evidence/simstability03/visual-refresh03/after.png',[129,409,443,457],True);waitfor(lambda s:bool(s['approvalId']),4);tap('media05-takeoff',285,495,'evidence/simstability03/visual-approve03/after.png',[130,472,442,518],True);s=waitfor(lambda s:(s.get('vehicle')or{}).get('armed')and s['vehicle']['mode']=='GUIDED'and-s['physics']['position'][2]>4.5,45);save('media05-airborne',s)
adb('shell','am','force-stop','vn.rtr.aeris.simhand01');adb('shell','am','start','-W','-n','vn.rtr.aeris.simhand01/.ShellActivity','--es','initialPath','/observer');time.sleep(3)
(E/'media05-audioflinger-before.txt').open('xb').write(adb('shell','dumpsys','media.audio_flinger'));icon_audio();(E/'media05-audioflinger-enabled.txt').open('xb').write(adb('shell','dumpsys','media.audio_flinger'));(E/'media05-package-uid.txt').open('xb').write(adb('shell','cmd','package','list','packages','-U','vn.rtr.aeris.simhand01'));save('media05-source-before-link-loss',state())
adb('reverse','--remove','tcp:8896');time.sleep(2);a=capture('media05-link-lost-a');time.sleep(.7);b=capture('media05-link-lost-b');roi=(400,180,1050,580);ha=hashlib.sha256(a.crop(roi).tobytes()).hexdigest();hb=hashlib.sha256(b.crop(roi).tobytes()).hexdigest();save('media05-freeze-comparison',{'roi':roi,'sameRenderedPixels':ha==hb,'aSHA256':ha,'bSHA256':hb,'scope':'ACTUAL_SCENE_PIXELS_DURING_ANDROID_DATA_LINK_LOSS_NOT_AUDIO_PCM_PROOF'});(E/'media05-audioflinger-stale.txt').open('xb').write(adb('shell','dumpsys','media.audio_flinger'));assert not state()['input']['active']
adb('reverse','tcp:8896','tcp:8896');time.sleep(.5);adb('shell','am','force-stop','vn.rtr.aeris.simhand01');adb('shell','am','start','-W','-n','vn.rtr.aeris.simhand01/.ShellActivity','--es','initialPath','/phone')
tap('media05-land',1167,689,'evidence/simstability03/visual-fly02/after.png',[1102,666,1232,712],True);s=waitfor(lambda s:(s.get('vehicle')or{}).get('mode')=='LAND'and s['vehicle']['armed']is False and s['physics']['ground'],45);save('media05-ground-disarm',s);tap('media05-review',61,467,'evidence/simstability03/visual-fly02/after.png',[35,440,87,492]);step('media05-reviewscroll','scroll',107,166,466,608);tap('media05-end',285,433,'evidence/simstability03/visual-auto04-reviewscroll/after.png',[129,410,443,456],True);s=waitfor(lambda s:s['lifecycle']['closed']and s['review']and s['review']['run']==s['run'],15);save('media05-closed',s);print('MEDIA05_COMPLETED',{'run':s['run'],'status':s['review']['status'],'freezePixelsEqual':ha==hb,'audioPCMMeasured':False},flush=True)
