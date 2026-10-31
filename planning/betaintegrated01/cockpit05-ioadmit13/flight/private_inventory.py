"""Read-only private inventory; genuinely absent new-app directories mean no files.
Each absence is separately observed and command-bound; errors/links are never empty.
"""
import re
from pathlib import Path
from . import contract
ROOTS=('files/control-runs','files/workspace03','files/review-links')
def inventory(op,roots=ROOTS,*,allow_empty=False,before_read=lambda:None):
 if type(roots)not in(tuple,list)or not 1<=len(roots)<=3 or len(set(roots))!=len(roots):raise ValueError('PRIVATE_INVENTORY_ROOTS')
 existing=[];absent=[]
 for root in roots:
  if type(root)is not str or re.fullmatch(r'files/(?:workspace03|review-links|control-runs(?:/[A-Za-z0-9_.:-]{1,128})?)',root)is None or '..'in Path(root).parts:raise ValueError('PRIVATE_INVENTORY_PATH')
  before_read();out,err,code,_=op.command(['shell','run-as',contract.PACKAGE,'ls','-ld',root],timeout=3,check=False);message=out+err
  if len(message)>16384:raise ValueError('PRIVATE_DIRECTORY_PROOF_BOUND')
  if code==0:
   lines=out.splitlines()
   if err or len(lines)!=1 or not lines[0].startswith(b'd')or not lines[0].rstrip().endswith(root.encode()):raise ValueError('PRIVATE_ROOT_NOT_REGULAR_DIRECTORY')
   existing.append(root)
  else:
   lines=message.splitlines()
   if len(lines)!=1 or root.encode()not in lines[0]or b'No such file or directory'not in lines[0]or b'Permission denied'in message or b'run-as:'in message:raise ValueError('PRIVATE_DIRECTORY_UNKNOWN_NOT_EMPTY')
   absent.append(root)
 values={}
 if existing:
  before_read();raw,err,code,_=op.command(['exec-out','run-as',contract.PACKAGE,'find',*existing,'-type','f','-exec','sha256sum','{}','+'],timeout=20)
  if code!=0 or err or len(raw)>1024*1024:raise ValueError('PRIVATE_FIND_FAILED_OR_BOUND')
  for line in raw.decode().splitlines():
   parts=line.split(None,1)
   if len(parts)!=2:raise ValueError('PRIVATE_FIND_NON_HASH_OUTPUT')
   h,name=parts;name=name.strip()
   if re.fullmatch('[a-f0-9]{64}',h)is None or '..'in Path(name).parts or name in values or not any(name.startswith(x+'/')for x in existing):raise ValueError('PRIVATE_MAP_SCHEMA')
   values[name]=h
 if len(values)>4096 or not values and not allow_empty:raise ValueError('PRIVATE_MAP_EMPTY_OR_BOUND')
 return dict(files=values,absentDirectories=absent,existingDirectories=existing,absenceIsObservedNotSeeded=True)
