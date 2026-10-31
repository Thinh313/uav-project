from ui94 import *
rows=[x for x in last()['controls']if's911f759c58644e3b8676'in x['id']];assert len(rows)==1;tap94(rows[0]['id']);time.sleep(.6);capture('05-review-offline-final');reports('final05-ui');adb('shell','am','force-stop',P);raw=adb('exec-out','tar','-C','/data/user/0/'+P+'/files','-cf','-','.');(E/'android94-final05-closed-files.tar').open('xb').write(raw)
from android94 import old_private
old_private('old-private-final05');(E/'android-stop-request05.json').open('x').write(json.dumps({'reason':'FINAL05_VERIFIED_STOP_OWNED_RUNTIME'}));print('FINAL05_CLOSED_REQUESTED',flush=True)
