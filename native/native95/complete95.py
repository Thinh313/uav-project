from ui94 import *
run=sys.argv[1];owned();tap94('open-sitl83')
end=time.monotonic()+180
while time.monotonic()<end:
 tap94('Preflight / Fly SITL')
 button=[x for x in last()['controls'] if x['id']=='complete83' and not x['disabled'] and not x['covered']]
 if button:
  capture(run+'-ground-complete')
  tap94('complete83');time.sleep(1)
  capture(run+'-review-saved')
  journal(run+'-closed-workspace')
  reports(run+'-closed-ui')
  raw=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-','.')
  (E/(run+'-closed-files.tar')).open('xb').write(raw)
  print('CLOSED_NATIVE_REVIEW',flush=True);break
 time.sleep(3)
else:
 capture(run+'-completion-not-observed');raise AssertionError('OBSERVED_COMPLETION_DEADLINE_NO_PASS')
