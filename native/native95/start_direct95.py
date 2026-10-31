from ui94 import *
run=sys.argv[1]
launch=json.loads((E/'runs'/run/'launch.json').read_text())
assert launch['run']==run and launch['hostGCSController'] is False
owned()
assert json.loads(adb('shell','getprop','ro.boot.qemu').decode())==1
claim={k:launch[k] for k in ['run','containerId','pid','startedAt','binarySha256']}
adb('shell','am','force-stop',P)
adb('shell','am','start','-n',P+'/.ShellActivity','--es','source87','direct','--es','owned95',"'"+json.dumps(claim,separators=(',',':'))+"'")
time.sleep(1.5)
tap94('open-sitl83')
capture(run+'-before-connect')
reports(run+'-before-connect')
show()
