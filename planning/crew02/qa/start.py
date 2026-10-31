from ui98 import *
owned();run=sys.argv[1];launch=json.loads((E/'runs'/run/'launch.json').read_text());assert launch['run']==run and launch['hostGCSController']is False;claim={k:launch[k]for k in ['run','containerId','pid','startedAt','binarySha256']};adb('shell','am','force-stop',P);adb('shell','am','start','-n',P+'/.ShellActivity','--es','source87','direct','--es','owned95',"'"+json.dumps(claim,separators=(',',':'))+"'");time.sleep(1)
end=time.monotonic()+20
while True:
 try:last();break
 except (AssertionError,IndexError):
  assert time.monotonic()<end,'WEBVIEW_STARTUP_NOT_FRESH';time.sleep(.3)
capture(run+'-direct-plan');show()
