from ui98 import *
owned();run=sys.argv[1];out=E/'runs'/run;connected=events98(run,'SOCKET_CONNECTED')[0][0]['elapsedMs'];target=connected+140000;start=time.monotonic();samples=[]
while True:
 now=float(adb('shell','cat','/proc/uptime').split()[0])*1000;tail=json.loads(adb('exec-out','tail','-n','1','/data/user/0/'+P+'/files/direct95/'+run+'/raw.jsonl'));assert tail['kind']!='CLOSED','NATIVE_CLOSED_DURING_AGED_CONDITION';assert time.monotonic()-start<180;free=__import__('shutil').disk_usage(R).free;assert free>20.5*2**30;samples.append({'androidElapsedMs':now,'tailRow':tail['n'],'freeBytes':free})
 if now>=target:break
 time.sleep(1)
(out/'aged-readonly-condition.json').open('x').write(json.dumps({'status':'PASS_READONLY_HISTORY_CONDITION','minimumAgeMs':140000,'observedAgeMs':now-connected,'nativeSocketConnectedAtMs':connected,'samples':samples,'note':'Same attached synthetic payload and two local stations; zero actuator grant before fresh preflight'},indent=2));print('AGED_READONLY_140_SECONDS_REACHED',flush=True)
