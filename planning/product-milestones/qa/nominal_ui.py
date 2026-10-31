from ui01 import *
import subprocess
owned();run=sys.argv[1]
def script(name,*args):subprocess.run([sys.executable,'-B',str(Path(__file__).parent/(name+'.py')),*args],cwd=R,check=True)
script('start',run)
tap01('pane-close');tap01('open-sitl83');tap01('connect83');capture(run+'-readonly')
script('wait_health',run)
tap01('close83');adb('shell','input','tap',52,171);tap01('payload');tap01('op-attach');tap01('op-discover');tap01('op-join');select01('op-actor','Payload B');tap01('op-join');select01('op-actor','Phi công A');tap01('op-close');tap01('open-sitl83');capture(run+'-before-preflight')
script('start_auto',run,'upload','nominal')
script('payload_nominal',run)
tap01('open-sitl83')
script('finish_nominal',run)
