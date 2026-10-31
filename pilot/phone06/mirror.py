"""Read-only USB HTTP native WAL mirror. No ADB, AP/GCS commands or device-private access."""
from pathlib import Path
import argparse,json,time,urllib.request,base64,hashlib,os,signal,sys,shutil
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
class NoRedirect06(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):raise ValueError("PHONE_MIRROR_REDIRECT_REFUSED")
def main():
 a=argparse.ArgumentParser();a.add_argument('--run',required=True);a.add_argument('--generation',required=True);a.add_argument('--source-id',required=True);args=a.parse_args();import re
 if not re.fullmatch('s[a-f0-9]{20}',args.run)or not re.fullmatch('[a-f0-9-]{36}',args.generation)or not re.fullmatch('[a-f0-9]{64}',args.source_id):raise ValueError('PHONE_MIRROR_CONTEXT')
 root=R/'evidence/phone06/runtime/runs'/args.run;capfile=R/'.local/phone06/secrets'/(args.run+'.cap');st=capfile.lstat()
 if not capfile.is_file()or capfile.is_symlink()or st.st_mode&0o077 or st.st_uid!=os.getuid():raise ValueError('PHONE_MIRROR_OWNED_CAPABILITY_FILE')
 capability=capfile.read_text()
 if not re.fullmatch('[a-f0-9]{64}',capability):raise ValueError('PHONE_MIRROR_CAPABILITY_FORMAT')
 opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect06());offset=0;start=time.monotonic();stop=False;last=None;error=None;n=0
 def stopped(*_):nonlocal stop;stop=True
 for sig in(signal.SIGINT,signal.SIGTERM):signal.signal(sig,stopped)
 try:
  with(root/'native-mirror.jsonl').open('xb')as out,(root/'clock-history.jsonl').open('xb')as clocks:
   while not stop:
    if time.monotonic()-start>=900 or shutil.disk_usage(R).free<21*2**30:raise ValueError('PHONE_MIRROR_RESOURCE_OR_DEADLINE')
    request=urllib.request.Request('http://127.0.0.1:5967/wal06',headers={'Authorization':'Bearer '+capability,'X-Run':args.run,'X-Generation':args.generation,'X-Source-Id':args.source_id,'X-Offset':str(offset)})
    before=time.monotonic_ns()
    with opener.open(request,timeout=1)as response:
     if response.geturl()!='http://127.0.0.1:5967/wal06':raise ValueError('PHONE_MIRROR_ENDPOINT_CHANGED')
     raw=response.read(131073)
     if len(raw)>131072:raise ValueError('PHONE_MIRROR_RESPONSE_BOUND')
    after=time.monotonic_ns();q=json.loads(raw)
    if q.get('format')!='aeris-phone06-wal-prefix'or q.get('run')!=args.run or q.get('generation')!=args.generation or q.get('sourceId')!=args.source_id or q.get('offset')!=offset or q.get('committedClosed')is not False:raise ValueError('PHONE_MIRROR_RESPONSE_BINDING')
    b=base64.b64decode(q['dataBase64'],validate=True)
    if len(b)>65536 or q['nextOffset']!=offset+len(b)or q['nextOffset']>q['committedBytes']or q['committedBytes']>32*2**20:raise ValueError('PHONE_MIRROR_COMMITTED_PREFIX_BOUND')
    out.write(b);out.flush();os.fsync(out.fileno());offset+=len(b);n+=1;native=q['nativeElapsedMs']
    if type(native)is not int or native<0:raise ValueError('PHONE_MIRROR_NATIVE_CLOCK')
    bracket={'run':args.run,'n':n,'nativeElapsedMs':native,'hostBeforeMonoNs':str(before),'hostAfterMonoNs':str(after),'widthMs':(after-before)/1e6,'status':'BOUNDED_BRACKET'if after-before<=250000000 else'UNUSABLE','source':'PHONE_NATIVE_ELAPSED_HTTP_RESPONSE_PROXY_NOT_SENSOR_TIME'};clocks.write((json.dumps(bracket)+'\n').encode());clocks.flush();os.fsync(clocks.fileno());temp=root/'clock-bracket.new';temp.write_text(json.dumps(bracket)+'\n');os.replace(temp,root/'clock-bracket.json');last={'bytesMirrored':offset,'committedRecords':q['committedRecords'],'committedHead':q['committedHead']};time.sleep(.2)
 except Exception as e:error=type(e).__name__+':'+str(e)[:200]
 finally:
  # Native closes the public feed on invalidation. Missing terminal raw is explicitly partial.
  with(root/'mirror-closure.json').open('x')as f:json.dump({'run':args.run,'error':error,'lastPrefix':last,'complete':False,'terminalClosedFetched':False,'finalSAFRequired':True,'hostGCSCommandBytes':0,'capabilityLogged':False},f,indent=2);f.flush();os.fsync(f.fileno())
 if error:raise SystemExit(2)
if __name__=='__main__':main()
