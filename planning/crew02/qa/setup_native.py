"""Actual Android touches; initialize identity before opening AP, no auto flight."""
from ui01 import *
import subprocess
owned();run=sys.argv[1]
subprocess.run([sys.executable,'-B',str(Path(__file__).parent/'start.py'),run],cwd=R,check=True)
tap01('pane-close');adb('shell','input','tap',52,171);tap01('payload');tap01('crew-init-native-key');tap01('crew-listen');capture(run+'-explicit-key-and-listen');tap01('op-close');tap01('open-sitl83');tap01('connect83');capture(run+'-readonly')
subprocess.run([sys.executable,'-B',str(Path(__file__).parent/'wait_health.py'),run],cwd=R,check=True)
tap01('close83');adb('shell','input','tap',52,171);tap01('payload');tap01('crew-attach');tap01('crew-join-A');tap01('crew-discover');tap01('crew-aircraft-claim');capture(run+'-a-pilot-only');tap01('op-close');print('A_JOINED_AIRCRAFT_ONLY_B_NOT_JOINED')
