"""Root-L2 ephemeral-only falsification of conservative wildcard bind candidate."""
from pathlib import Path
import hashlib,json,os,socket
R=Path(__file__).resolve().parents[2];rows=[]
def spare():
 with socket.socket()as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
for address in ['127.0.0.1','0.0.0.0']:
 for reuse in [False,True]:
  for position in [0,1]:
   handles=[];error=None
   with socket.socket()as foreign:
    if reuse:foreign.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    foreign.bind((address,0));foreign.listen(1);ports=[spare(),spare()];ports[position]=foreign.getsockname()[1]
    try:
     for port in ports:
      s=socket.socket();handles.append(s);s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('0.0.0.0',port));s.listen(1)
    except OSError as exc:error={'port':port,'errno':exc.errno,'error':str(exc)}
    finally:
     for s in reversed(handles):s.close()
    rows.append({'foreignAddress':address,'foreignReuse':reuse,'position':position,'ports':ports,'candidateWildcardBlocked':error is not None,'error':error,'handlesClosed':all(s.fileno()==-1 for s in handles)})
report={'status':'CANDIDATE_REJECTED_COEXISTENCE'if any(not r['candidateWildcardBlocked']for r in rows)else'CANDIDATE_BLOCKS_ALL_ACTIVE_FIXTURES','rows':rows,'scope':'Only ephemeral bind/listen/close; no connect/accept/dataread, no actualcampaignports. Production module unchanged; oldG9causeUNKNOWN.'}
p=R/'evidence/beta06/generation10/builder-wildcard-candidate01.json'
with p.open('x')as f:json.dump(report,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps({'status':report['status'],'rows':rows}))
