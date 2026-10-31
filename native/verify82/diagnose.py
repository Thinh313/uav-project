from pathlib import Path
import json,time,sys
from android_qa import adb,owned,E
owned();name=sys.argv[1];assert name in ['headless04','headless05','warm04','warm05']
rows=[]
for i in range(8):
 before=time.monotonic();guest=adb('shell','cat','/proc/uptime',timeout=10).decode().strip();after=time.monotonic();rows.append({'hostBefore':before,'hostAfter':after,'guestUptime':float(guest.split()[0]),'rttMs':(after-before)*1000});time.sleep(.4)
start,end=rows[0],rows[-1];host=((end['hostAfter']+end['hostBefore'])-(start['hostAfter']+start['hostBefore']))/2;guest=end['guestUptime']-start['guestUptime'];receipt={'rows':rows,'hostIntervalSec':host,'guestIntervalSec':guest,'guestHostRatio':guest/host,'maxAdbRttMs':max(x['rttMs']for x in rows),'scope':'Shell clock/transport only; not UI/frame/flight performance'}
for cmd,key in [(('shell','cat','/proc/meminfo'),'guest-meminfo'),(('shell','dumpsys','webviewupdate'),'webview'),(('shell','dumpsys','meminfo','vn.rtr.aeris.cockpit82'),'app-meminfo'),(('logcat','-d','-t','350'),'logcat')]:
 try:(E/(name+'-'+key+'.txt')).open('xb').write(adb(*cmd,timeout=10))
 except Exception as e:receipt[key+'Error']=str(e)
(E/(name+'-diagnostic.json')).open('x').write(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k!='rows'}))
