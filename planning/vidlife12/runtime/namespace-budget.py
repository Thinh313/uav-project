from pathlib import Path
R=Path(__file__).resolve().parent/'source/aeris_runtime'
p=R/'inventory.py';s=p.read_text().replace("repository()/'evidence/hostdiag11'","repository()/'evidence/vidlife12'").replace("repository()/'evidence/hostdiag11/candidates'","repository()/'evidence/vidlife12/candidates'");p.write_text(s)
p=R/'candidate.py';s=p.read_text();a=" if root==repo/'evidence/hostdiag11/candidates':return";assert a in s;s=s.replace(a," if root==repo/'evidence/vidlife12/candidates':return(*artifact_roots(repo/'evidence/hostdiag11/candidates'),root)\n"+a)
# Extend exact reuse pool membership without removing any original pool.
s=s.replace("repo/'evidence/hosthealth-ipc10/candidates',repo/'evidence/hostdiag11/candidates')","repo/'evidence/hosthealth-ipc10/candidates',repo/'evidence/hostdiag11/candidates',repo/'evidence/vidlife12/candidates')")
s=s.replace("if root==repo/'evidence/hostdiag11/candidates'else[]);origins={}","if root in(repo/'evidence/hostdiag11/candidates',repo/'evidence/vidlife12/candidates')else[]);pool_roots+=([repo/'evidence/hostdiag11/candidates/objects']if root==repo/'evidence/vidlife12/candidates'else[]);origins={}")
s=s.replace("root!=repo/'evidence/hostdiag11/candidates'","root!=repo/'evidence/vidlife12/candidates'")
s=s.replace("repository()/'evidence/hosthealth-ipc10/candidates',repository()/'evidence/hostdiag11/candidates')","repository()/'evidence/hosthealth-ipc10/candidates',repository()/'evidence/hostdiag11/candidates',repository()/'evidence/vidlife12/candidates')")
s=s.replace("if path.parent==repository()/'evidence/hostdiag11/candidates':expected+=","if path.parent in(repository()/'evidence/hostdiag11/candidates',repository()/'evidence/vidlife12/candidates'):expected+=")
a="  if pools!=expected:raise ValueError('IMMUTABLE_REUSE_DECLARED_POOLS')";assert a in s;s=s.replace(a,"  if path.parent==repository()/'evidence/vidlife12/candidates':expected+=['evidence/hostdiag11/candidates/objects']\n"+a);p.write_text(s)
p=R/'public_ui_workload.py';s=p.read_text();a="   eligible=after_action and self.dispatch_headroom(start,age)";assert a in s;s=s.replace(a,"   if key=='video-measure'and after_action and isinstance(o.get('videoLifecycle12'),dict)and o['videoLifecycle12'].get('terminal')is True:\n    reason=o['videoLifecycle12'].get('firstStop',{}).get('reason','UNKNOWN');raise RuntimeError('PUBLIC_UI_VIDEO_STARTUP_TERMINAL:'+str(reason)[:180])\n"+a);p.write_text(s)
print('new namespace and cumulative artifact roots extended, no history exclusion')
