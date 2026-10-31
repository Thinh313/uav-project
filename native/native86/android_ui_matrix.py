"""Native UI actions only, observed 1280x800 control coordinates; PNG/AX receipts, no DOM injection."""
import sys,time,json
from android_qa import *
owned();steps=[]
def shot(name):
 time.sleep(.4);capture(name);raw,t=dump();steps.append({'name':name,'screenshot':name+'.png','xmlSha256':hashlib.sha256(raw).hexdigest(),'nodes':len(list(t.iter('node')))})
for theme in ['night','day']:
 if theme=='day':adb('shell','input','tap','1143','32')
 for view,y in [('plan',239),('preflight',307),('fly',171),('review',375)]:
  adb('shell','input','tap','52',y);shot('android86-'+theme+'-'+view)
 adb('shell','input','tap','52','171')
 for name,x,y in [('authority',850,32),('aircraft',296,32),('link',1005,32),('concept',187,32),('battery',1216,32),('input',52,456),('payload',1229,231),('camera-settings',1229,553),('camera-meta',560,638)]:
  adb('shell','input','tap',x,y);shot('android86-'+theme+'-sheet-'+name);adb('shell','input','keyevent','111');time.sleep(.2)
 adb('shell','input','tap','52','537');shot('android86-'+theme+'-workspace');adb('shell','input','keyevent','111')
reports('android86-ui-final');(E/'android-ui-matrix01.json').open('x').write(json.dumps({'scope':'OWNED_API33_ANDROID1280X800_NOT_HERA','steps':steps,'visualReview':'PENDING_REVIEW','rendererReports':'SELF_OBSERVED_NOT_ATTESTATION'},indent=2));print('MATRIX_CAPTURED',len(steps))
