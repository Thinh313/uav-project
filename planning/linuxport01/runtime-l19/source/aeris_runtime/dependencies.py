"""Explicit temporary pinned leaf closure; no milestone policy/orchestrator imports."""
LEAVES=('pilot/betaintegrated01/runtime/ap_stage.py','pilot/betaintegrated01/runtime/physics.py','pilot/betaintegrated01/runtime/physics_reference.py','pilot/betaintegrated01/runtime/_sim32_kernel.cpython-314-darwin.so','pilot/betaintegrated01/runtime/_sim32_kernel.cpython-314-x86_64-linux-gnu.so','pilot/betaintegrated01/clock/correlation.py','pilot/betaintegrated01/control01/mavlink.py','pilot/betaintegrated01/control01/dialect.json','pilot/betaintegrated01/control05/bootstrap.py')

LEAVES+=tuple('pilot/mission55/vendor/geographiclib/'+n+'.py' for n in ('__init__','accumulator','constants','geodesic','geodesiccapability','geodesicline','geomath','polygonarea'))

def loaded_leaf_origins():
 from pathlib import Path
 import sys,hashlib
 from .paths import repository
 root=repository();allowed={str((root/name).resolve()):name for name in LEAVES};out={}
 for name,module in list(sys.modules.items()):
  if not (name.startswith('pilot.') or name=='geographiclib' or name.startswith('geographiclib.')):continue
  origin=getattr(module,'__file__',None)
  if origin is None:continue
  actual=str(Path(origin).resolve())
  if actual not in allowed:raise RuntimeError('UNDECLARED_TRANSITIVE_LEAF_ORIGIN:'+name+':'+actual)
  out[name]={'path':allowed[actual],'sha256':hashlib.sha256(Path(actual).read_bytes()).hexdigest()}
 if 'geographiclib' in sys.modules and getattr(sys.modules['geographiclib'],'__version__',None)!='2.1':raise RuntimeError('EXACT_VENDORED_GEOGRAPHICLIB2_1_REQUIRED')
 return out

LINUX_KERNEL='pilot/betaintegrated01/runtime/_sim32_kernel.cpython-314-x86_64-linux-gnu.so';LINUX_KERNEL_SHA256='a0dbf90dd96ba72e37bca85ba955c84b5bc0ef9c8c1f4ca92605ceb46cf616c4'
def require_linux_kernel(declared):
 """runtime-l18 (team decision "Yes, provider only", not the owner's): the backend process must have loaded exactly the
 pinned Linux build of the owner's pilot/sim32/kernel.c, and its run config must declare that SHA-256. Unlike the
 allowlist above, this refuses when no kernel is loaded."""
 row=loaded_leaf_origins().get('pilot.betaintegrated01.runtime._sim32_kernel')
 if row!={'path':LINUX_KERNEL,'sha256':LINUX_KERNEL_SHA256}or declared!=LINUX_KERNEL_SHA256:raise RuntimeError('L18_PINNED_LINUX_SIM32_KERNEL_REQUIRED')
 return row
