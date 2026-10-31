"""Immutable selected source/native archives; active implementation stays repairable."""
from pathlib import Path
from .cleanup import close_fd,finish_cleanup
import gzip,hashlib,io,json,os,re,shutil,tarfile,zipfile,stat
from itertools import chain
from .paths import PACKAGE_ROOT,repository
from .dependencies import LEAVES
from pilot.betaintegrated01.runtime.ap_stage import canonical
MIB=2**20;CAP=8*MIB;CERT='3b3652341ec954f4640892e73df124f41cbb0efc81ace1d6ba83cfdddd319800'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for block in iter(lambda:f.read(MIB),b''):h.update(block)
 return h.hexdigest()
def safe_relative(name,prefix=None):
 if type(name)is not str or Path(name).is_absolute() or '..' in Path(name).parts or '\\' in name or (prefix and not name.startswith(prefix)):raise ValueError('CANDIDATE_RELATIVE_PATH')
 return name
def walk_allocations(root,visit,*,deadline_check=None,symlink_error='CANDIDATE_SYMLINK'):
 """One actual nofollow stat per entry; fd-relative traversal and strict errors.

 A directory identity is additionally fstat-checked before descent. Every fd
 closes even when a visitor/deadline/stat fails. No missing-file exception is
 suppressed, no cached physical sizes or caller capacity estimates are used.
 """
 import stat
 from .cleanup import cleanup
 base=os.fspath(root)
 def check():
  if deadline_check is not None:deadline_check()
 def descend(fd,name):
  failure=None;entries=None
  try:
   entries=os.scandir(fd)
   for entry in entries:
    check();value=entry.stat(follow_symlinks=False);path=name+os.sep+entry.name
    if stat.S_ISLNK(value.st_mode):raise ValueError(symlink_error)
    visit(path,value)
    if stat.S_ISDIR(value.st_mode):
     child=os.open(entry.name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
     try:
      actual=os.fstat(child)
      if(actual.st_dev,actual.st_ino)!=(value.st_dev,value.st_ino):raise RuntimeError('ALLOCATION_DIRECTORY_CHANGED')
     except BaseException as error:
      cleanup(error,[('allocation-child-fd-close',lambda:os.close(child))]);raise
     descend(child,path)
  except BaseException as error:failure=error;raise
  finally:
   operations=[]if entries is None else[('allocation-scandir-close',entries.close)]
   operations.append(('allocation-directory-fd-close',lambda:os.close(fd)))
   final=cleanup(failure,operations)
   if failure is None and final is not None:raise final
 check();value=os.stat(base,follow_symlinks=False)
 if stat.S_ISLNK(value.st_mode):raise ValueError(symlink_error)
 visit(base,value)
 if stat.S_ISDIR(value.st_mode):
  fd=os.open(base,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
  try:
   actual=os.fstat(fd)
   if(actual.st_dev,actual.st_ino)!=(value.st_dev,value.st_ino):raise RuntimeError('ALLOCATION_DIRECTORY_CHANGED')
  except BaseException as error:
   cleanup(error,[('allocation-root-fd-close',lambda:os.close(fd))]);raise
  descend(fd,base)
 check()
def allocated_unique(root,*,deadline_check=None):
 seen=set();n=0
 def visit(path,value):
  nonlocal n
  key=(value.st_dev,value.st_ino)
  if key not in seen:seen.add(key);n+=value.st_blocks*512
 walk_allocations(root,visit,deadline_check=deadline_check)
 return n
# Fixed cumulative artifact domain for the one corrected TRANSPORT15 campaign.
# Historical unselected native build1 is deliberately still charged. Paths are
# an original sealed membership set; disappearance is failure, never free space.
ATOMIC_EVIDENCE='evidence/runtime-transport15-atomic-prep'
OLD15_ARTIFACTS='evidence/runtime-transport15/candidates'
OLD15_MEMBERS=('43a694e73a077eb2ea06481aa68e010021e23e5bb3cf8b27b70bd0ae1814b5a7-inputs.tar.gz', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/candidate.json', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/candidate.sha256', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/native-build-receipt.json', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/native-inputs.tar.gz', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/native.apk', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/qa-gate.json', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/__init__.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/acceptance_profile.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/ack_observer.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/admission.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/android.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/ap_supervisor.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/assets', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/assets/observer-intervals.txt', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/assets/pipeline-writer-pins.json', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/assets/resource-policy.json', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/__init__.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/cancellation.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/checkpoint.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/clock_receiver.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/compact.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/confirmation.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/control.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/geocollect.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/geography.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/lifecycle.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/native_authority.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/native_chain.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/native_chain_json.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/native_release.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/native_stream.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/native_wire.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/oracles.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/receiver.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/rx_group.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/transactions.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/transport.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/verify_capture.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/audit/window.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/backend.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/broker_reader.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/budget_fileio.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/campaign.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/candidate.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/cleanup.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/commands.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/dependencies.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/diagnostic_job.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/emulator.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/entry.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/factory.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/__init__.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/clock_socket.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/delivery.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/diagnostics.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/frame_adapter.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/frame_core.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/journal.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/journal_base', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/journal_base/__init__.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/journal_base/receiver.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/journal_base/writer.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/owner.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/owner_base.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/profile.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/foundation/transport.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/host_health.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/identity.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/inventory.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/io_broker.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/io_conformance.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/launch.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/lifecycle.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/metadata_budget.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/monitor.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/native.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/once_reader.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/once_store.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/operator.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/owned_output.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/paths.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/pipeline_contract.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/policy.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/predecessor15.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/proofs.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/raw_console.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/resources.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/stage_trace.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/state_binding.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/status15_reader.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/status15_timing.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/status15_wire.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/status_socket.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/supervisor.py', 'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b/source/aeris_runtime/telemetry.py', 'd82d689b4743aa40305c1b3c61be9d56947be1249bca1868f28182247a28d6e6.apk', 'e6d63f71a0f89f7b53e54b7231b45ea275ebbe16299c1d6fde82b97734c18ddd-inputs.tar.gz', 'f459c7a90d714afc653985607df0c29587ae1cdc57a97359787b131ad6e31425.apk', 'objects', 'objects/004aa429f8050fe1ca6c8177d9934d2181ef861717f24f9c535b24131d115800', 'objects/050fa7c57dc495bae021d949cfe316a4ab4f5a0d34f1cbbfa6124afeb2319dd5', 'objects/071fd11a084f6f3d25e629d9fb3d093a9d9f0f52af95171b2101f6a9dc5fa57c', 'objects/0848482d495e5f92534b4445d6b50cead2e1ef3ec7550843ef17906e925520ac', 'objects/0c58d5a25687b3b83701460078d6c2d80836abb037f79fea8560e834f14fde3f', 'objects/0f5ff26c590a0fc6414482c4c6134a9166b4b17665bd81952ae41b29ff1fed33', 'objects/0f69ca49e81290c2c83a2ee54858a8fc6f9ff3fdbff640c84f3cb9a70004d276', 'objects/1583035fbb5e4cb1c21ed03f086e3a8e1d3fc45c9fce078afc0fb3b74250c53a', 'objects/17ab9375e5840183dead7fe4df32e233ec2c2d78745e2452696482f9c0657488', 'objects/1a6c610ba439f19d10270e7139ece69afd99cdad2dba44d935dea5a13d5701f5', 'objects/1ad9dfbc36eb45a7db21d685589f03367ce0e4f23bd75726cf22f09ae336c53f', 'objects/21a3fa741ae9bb193867ff6fb096fe2ea7637cf3cb86e55a2c420a17bd31519e', 'objects/22739f336971b7d38fe05755bf1667dff97c7fa231134cfd844a52b6d1cdd3fe', 'objects/2771282eb1a6c8b1417e6d3977c3639024002b9b7c59f249a29f7100a78cc7a7', 'objects/28e314c6e6260eaddb672f01a81ba95b2d66dcece5f4f75e5b29cb9e1fac0361', 'objects/29cd5bc75a36e7d2cd6f295e521e4397a33b0b67087bb8c5f29e1dbea6c2394a', 'objects/32de9069329283ebfd4f936d87819516879b7944b5bf916e3d08b050e3da2459', 'objects/33cd0c1b9588a4eb7556d6ca143f231695bc2a8d52401dfc3565ac4896675776', 'objects/33fa46ad4c9a9e9bbf461386467054c235e5b0d430db6aa1e9174e2e990efe68', 'objects/35f0ac66257c70e75d04ab961daef053b3b9c73d602a5441ae46c8267bfb86dc', 'objects/3b354bd6a2090d02130c2d9ce7c15a99bac5f7ce122276f0e32369a12dd845d5', 'objects/3b59d7b6286ad232e44241ae76702781f94f1e1303ffddb9db13f43ca9f8da1e', 'objects/4174d88dc5251226b349c309abba6368fc20570c2a02b7b1d8b421057e6e4d2e', 'objects/44857a188808207568855c7af8decc01bf9505fc46fa2ebd6a99fef187fe1c6e', 'objects/48d78201a832dec260e6ad044a466997cbb3365124846f56950d6b96611374fc', 'objects/4a3cd907c6de26238fff4ac97811790a6b2f1e81df97be77a91483dda0358e1e', 'objects/4b57b310325f105f4d918a3186fba94fdae258d0e82fb04f209f7bfaa78ba210', 'objects/500ceb18a23c23e5e6bd43fcfbcd3af15822960a497584c4756a2e6602028118', 'objects/511078532bd533519eb178691d79b2acee60f02e6579e7d30d0fc4c3682a00cf', 'objects/516b8485081ce796f761f69beea36ac1ee9ea78a2ecacbe6fcfbb019ebae3ca3', 'objects/54ac130177188701965e5d1403bdc9886559366854ddc29752458bec807e52e5', 'objects/57ff78162830b79255b6f62168ed5354c4fb6448f4aad62c1c403093d5994d34', 'objects/591485a678b79544c468c8e7240a0de2a123fb9e80199bc5f7d4b4143d907589', 'objects/5a1d596a2740fb6b72f2a59bb70a30ad9261bf72f647e76945c93a2261171b00', 'objects/5c91aa845f7204d888afc41ac78ac9d359afafc4a47937f044a4ca63d0a79bf1', 'objects/611fd294a91e1bbccb636b8217bed9d480b08bb02d86721a4d777b75c57bf472', 'objects/632b465c7fc04e5b1e3e9f9cadbcc22b5c50a24b84c83936e00690047c1d64e2', 'objects/6765d2da440adabc0833d8abcad93636d06390f6499a91ad284e0f77117ea212', 'objects/6aa1d88aef931de22cc15cebb0d88cc7422fc573f8ee4d1fde1a9edc71db8d8a', 'objects/6de28ccf8b9099cd4b66c6cbd71bbbe87dc4f134713752de61a437eda575cc60', 'objects/6efcaa33c70bfa1f8d5b5a1cd7a8f715346577fe3d12ed6e013a3bc8e3efcefb', 'objects/714f6d9589614e3c90a0a2829e8b30f00a4df371b82fb44a2e25362b9fc941ed', 'objects/72d497c0875133dd111f130218433b2acf9381dfab817bc30fb6fdd0ac815eea', 'objects/7302bba1768391c2732e56ce1594459834ed1fa80326b1e6632efbc2a20213ee', 'objects/75ecdaa163f9df48d78e9f05bbd53f20df1d767662fd8c616f70557cb0dd6bf9', 'objects/8208f8ddccc7a89ceee9876ef77bbc00464d93e8e6b203ab303cd653e1e50e12', 'objects/8617dd3d694ac92e69435bbcc2058252aede7705ae4ebd04f4a5d20c3446f968', 'objects/8727df1a6746d3f5a7847da4a2a17576de8a32dcb1d8c67f1a0940dd1f95a990', 'objects/8acabaee1e48688029dface7012b7283336457e1534c1f96b30e001cd064eb19', 'objects/8b98bc4c06b94e9d576035fd396c83b3e950c2f8e8cfe573481138db78432a5d', 'objects/90c1e356f9863fe5ab6c2a84557818edbc1746dd8c54f757f51260d72999587b', 'objects/97127a3154bb2390757d8a1da743fde5324087db5a3a8b935bd550e3ac909328', 'objects/9a3f3e11d70809cc58422c4b99fa6cc9569ba3f585a94e7a7b715ee7c2612584', 'objects/a2fcb50552214e52b3469c39ba4b424e3f19b7c867d2508e5afc58f5383c3833', 'objects/a5b0ca68ea1acf15620eb60d2aa75a635591e84f5e3a395857b82ab99c0e42fb', 'objects/aaece1777d8da478be87a879a557e966c65d7b7fbb3b7df103f5a2029c9534ef', 'objects/aaf06e7b18be7f1ea1dfafa79f7a993be05003954b798fc5396bb8ae06cc2909', 'objects/abf0a8f385697700a419ecd7aea68dd90670a90950f9d9ce04b94992c966097b', 'objects/ac307eff9a72f391b1b6e558faa266b4482c5b95ec677f66b24de1fa6890780c', 'objects/ac702f2f48db42c06002391d594de28d8ca4b7c2eee8d0ef0666cb5d19f39780', 'objects/ad780a13b7a477b22b44d373772c28904a94257e26d6ce90aa2eecce2e9999cb', 'objects/b3a391cd167eccd98871dc528b151101ba0ebeb630f136723748568995c67c04', 'objects/b536dfefab008c6095705ed6eca545560322914af2221729d926473632e6695b', 'objects/b567a723d55594f3ec836f88a92e434a62f577d4f2df85d4d622d2ad47612c66', 'objects/b8571a898fdcc8ac7790103f952ec5c575529ff5bba4d6c13d9c81e4dbc406e8', 'objects/bcf7d4f59a285ade1cb040d41ebf2818a1525ceefbf88aaf46bf7a5582855590', 'objects/c02bf49e0999a5fa36a54e7c2ce50efa34108f3d1caa9193613942f016da0979', 'objects/c16352dab66b33138fa434fc57d4e199a4c711f075dd83fa6cb3955dc3482ec6', 'objects/c1c7b7cf66ca0fefb0f7e2e59e1b9fbae57f4e3579a61bc4676b7cdfb42bc742', 'objects/c2baaaa7e51d986fd66d65a1e1bdbd356b573cbdccbab3dec9e0f34b515b5a3d', 'objects/c36e648fb712d9a8659b88082beb08d2d2cf361b280b4997b8185de8472e1852', 'objects/c778d75ca95054cca5a4c61945773b448963687083ea00b059d20a529086c750', 'objects/cc96bc78ca595ef787ef9d399241def2d0e213609d85c1f1a47a612131759d27', 'objects/d20c8694f2eff8bb8d038135c2a836cc43ad0d4ff519e87cd0b706e2222c938a', 'objects/de992cdf9d0423b8c734a1ff7fb809e2ed868b9ce2e2127756396bb974fecc4a', 'objects/deccb152392ec2a49ece12dcd5d54a51f04ae35d8c69d4fe8e0292089d15a777', 'objects/e4394875af5d0ce2a4bd08b429b268bacc00b62d78698b54b17420600cd0d7ea', 'objects/e47b41de6edd6b2ffa073c353f49306062dbefe920a5603d0c4d12dcbe772249', 'objects/e614f398177be098bf110352fe75348da36efc92cf5ed4e70d0b3049d894fe10', 'objects/eeca2616dd27a31f1d779b0ff62a0f2395ac7c147c6655d8be9456ac2e1458ce', 'objects/ef322bf8156aedc51c9d206c66e2ed601fb4a7054c949364d7c47ea4118ad7b3', 'objects/ef59f0a1906910e180ebb24e08eb625da92194b4198b8cb2e22a93ef12fc812a', 'objects/ef9fd2e284da5ca2d124f9c8c206bf1dd2c211a5040e57c0d47ce64daa26bc1b', 'objects/f3bc1edb98939c73035666b9506340a1e71ac1dedd73152c77471eea8a98a194', 'objects/f459c7a90d714afc653985607df0c29587ae1cdc57a97359787b131ad6e31425', 'objects/f77b7a24bd4a6967399cf5890fd0816ee718814014335edd814a2df9845f20d4', 'objects/f7edb0f26931d0f12a24b30577e863e76c006fe7941130ea53ef97b77d2918cb', 'objects/f90de9675777a396056a26e3df78109b7caf8ba01fc964b299915e1538c3f76c', 'objects/f9aa0247dc9249750834f06930f9a7ccad0bbde77088e508fb3841cc82b343e9', 'objects/fad8867b1d8c9612ffd3152abf1a0e9af69dfc37181f7f9ac94eca114447805c', 'objects/ff1b0c8ef1fe0b59b326ce21194b3b3bc1384e8ae2af79c037f2c9a3f34f486f')
def artifact_roots(root):
 root=Path(root).absolute();repo=repository()
 if any(p.is_symlink()for p in[root,*root.parents]):raise ValueError('ARTIFACT_ROOT_SYMLINK')
 root=root.resolve()
 if root==repo/'evidence/vidlife12/candidates':return(*artifact_roots(repo/'evidence/hostdiag11/candidates'),root)
 if root==repo/'evidence/hostdiag11/candidates':return(repo/OLD15_ARTIFACTS,repo/ATOMIC_EVIDENCE/'candidates',repo/'evidence/betasim-integrated01/candidates',repo/'evidence/hosthealth-ipc10/candidates',root)
 if root==repo/'evidence/hosthealth-ipc10/candidates':return(repo/OLD15_ARTIFACTS,repo/ATOMIC_EVIDENCE/'candidates',repo/'evidence/betasim-integrated01/candidates',root)
 if root==repo/'evidence/betasim-integrated01/candidates':return(repo/OLD15_ARTIFACTS,repo/ATOMIC_EVIDENCE/'candidates',root)
 return (repo/OLD15_ARTIFACTS,root)if root==repo/ATOMIC_EVIDENCE/'candidates'else(root,)
def allocated_artifact_union(root,*,deadline_check=None):
 seen=set();total=0
 for directory in artifact_roots(root):
  if directory==repository()/'evidence/hostdiag11/candidates'and not directory.exists():continue
  members=set();base=str(directory)
  def visit(path,value):
   nonlocal total
   key=(value.st_dev,value.st_ino)
   if key not in seen:seen.add(key);total+=value.st_blocks*512
   if path!=base:members.add(path[len(base)+1:])
  walk_allocations(directory,visit,deadline_check=deadline_check)
  if directory==repository()/OLD15_ARTIFACTS and not set(OLD15_MEMBERS).issubset(members):raise ValueError('CUMULATIVE_OLD15_ARTIFACT_PATH_MISSING')
  if directory==repository()/'evidence/hosthealth-ipc10/candidates':
   fixed='8e6b9a467f97776247b45e6cfaf88357e566c17b079416921aff19d0ee49e9ef';original=directory/fixed/'candidate.json';raw=original.read_bytes();v=json.loads(raw)
   if raw!=canonical(v)+b'\n'or hashlib.sha256(canonical(v)).hexdigest()!=fixed:raise ValueError('CUMULATIVE_IPC10_ORIGINAL_MANIFEST')
   expected={fixed,fixed+'/candidate.json',fixed+'/candidate.sha256',fixed+'/source','objects'}
   for name,h in v['sourceSHA256'].items():
    expected.add(fixed+'/source/'+name);expected.add('objects/'+h)
    parent=Path(fixed+'/source/'+name).parent
    while parent!=Path('.'):expected.add(parent.as_posix());parent=parent.parent
   for name,h in v['retainedObjects'].items():expected.add(fixed+'/'+name);expected.add('objects/'+h)
   if not expected.issubset(members):raise ValueError('CUMULATIVE_IPC10_ARTIFACT_PATH_MISSING')
 return total
def put(path,raw,*,budget=None,owner=None,closing=False):
 if budget is not None:
  if owner is None:raise ValueError('EXPLICIT_METADATA_OWNER_REQUIRED')
  return budget.write(owner,path,raw,closing=closing)
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 f=path.open('xb')
 try:f.write(raw);f.flush();os.fsync(f.fileno())
 finally:finish_cleanup([('artifact-file-close',f.close)])
 fd=os.open(path.parent,os.O_RDONLY)
 try:os.fsync(fd)
 finally:close_fd(fd)
def _readonly_content_origin(path,digest,raw):
 path=Path(path)
 if not path.exists():return None
 st=path.lstat()
 if any(p.is_symlink()for p in[path,*path.parents])or not stat.S_ISREG(st.st_mode)or st.st_mode&0o222 or st.st_size!=len(raw)or sha(path)!=digest:raise ValueError('IMMUTABLE_REUSE_ORIGIN_NOT_READONLY_EXACT')
 return path

def immutable_object_plan(root,values,held_native=()):
 """No mutation: only exact existing readonly object pools can supply links."""
 root=Path(root);repo=repository();pool_roots=[repo/OLD15_ARTIFACTS/'objects',repo/ATOMIC_EVIDENCE/'candidates/objects'];pool_roots+=([repo/'evidence/betasim-integrated01/candidates/objects']if root in(repo/'evidence/hosthealth-ipc10/candidates',repo/'evidence/hostdiag11/candidates',repo/'evidence/vidlife12/candidates')else[]);pool_roots+=([repo/'evidence/hosthealth-ipc10/candidates/objects']if root in(repo/'evidence/hostdiag11/candidates',repo/'evidence/vidlife12/candidates')else[]);pool_roots+=([repo/'evidence/hostdiag11/candidates/objects']if root==repo/'evidence/vidlife12/candidates'else[]);origins={};declared={};held={hashlib.sha256(raw).hexdigest():(Path(path),raw)for path,raw in held_native}
 for h,raw in values.items():
  target=root/'objects'/h
  if target.exists():origins[h]=_readonly_content_origin(target,h,raw);continue
  for index,pool in enumerate(pool_roots):
   source=_readonly_content_origin(pool/h,h,raw)
   if source is not None:origins[h]=source;declared[h]={'pool':index,'bytes':len(raw),'mode':stat.S_IMODE(source.stat().st_mode)};break
  if h not in origins and h in held:
   source,heldraw=held[h]
   expected_parent=repo/'evidence/betasim-integrated01/candidates'if root in(repo/'evidence/hosthealth-ipc10/candidates',repo/'evidence/hostdiag11/candidates',repo/'evidence/vidlife12/candidates')else root
   if source.parent!=expected_parent or _readonly_content_origin(source,h,raw)is None:raise ValueError('RETAINED_HELD_NATIVE_ORIGIN_SCOPE')
   origins[h]=source;declared[h]={'heldNative':str(source.relative_to(repo)),'bytes':len(raw),'mode':stat.S_IMODE(source.stat().st_mode)}
 return origins,{'version':1,'poolRoots':[str(p.relative_to(repo))for p in pool_roots],'objects':declared,'writablePlanningSourceLinked':False,'oldOriginModeOrBytesChanged':False}

def _object(store,raw,origin=None):
 h=hashlib.sha256(raw).hexdigest();target=store/h
 if target.exists():
  if _readonly_content_origin(target,h,raw)is None:raise ValueError('IMMUTABLE_OBJECT_CONFLICT')
 elif origin is not None:
  _readonly_content_origin(origin,h,raw);os.link(origin,target)
 else:put(target,raw);target.chmod(0o444)
 return h,target

def _product_native_verify(receipt,archive,apk):
 if receipt.get('format')!='aeris-development-build'or receipt.get('version')!=2 or receipt.get('productionSigning')is not False or receipt.get('certificateSHA256')!=CERT:raise ValueError('PRODUCT_DEVELOPMENT_RECEIPT')
 pins=receipt.get('sourcePins');count=receipt.get('sourceCount');application=receipt.get('package','vn.rtr.aeris.mission')
 if application not in('vn.rtr.aeris.mission','vn.rtr.aeris.betasim09'):raise ValueError('EXACT_PRODUCT_APPLICATION_DOMAIN')
 if application=='vn.rtr.aeris.betasim09':
  old='native/betasim-integrated01/src/vn/rtr/aeris/mission/';new='native/betasim-application09/';expected={old+n+'.java'for n in('ExportBudget','InputJournal','FlightPads','NativeInputBridge','ProductActivity','OperationGate','WorkspaceStore')}|{new+n for n in('AndroidManifest.xml','build.py','protocols/product-protocol.json','src/vn/rtr/aeris/mission/ProductStatusReceiver.java')}
  if type(pins)is not dict or set(pins)!=expected:raise ValueError('EXACT_NEW_APPLICATION11_SELECTED_INPUTS')
 if type(pins)is dict and any(Path(name).name in('Compact10.java','NativeSegments.java','ControlOwner.java','ControlSession.java')for name in pins):raise ValueError('PRODUCT_LEGACY_COMPACT_OR_CONTROL_WRITER_NOT_SELECTED')
 if type(pins)is not dict or type(count)is not int or not 1<=count<=256 or len(pins)!=count:raise ValueError('PRODUCT_EXACT_SOURCE_COUNT')
 if hashlib.sha256(apk).hexdigest()!=receipt['sha256']or len(apk)!=receipt['bytes']:raise ValueError('PRODUCT_APK_HASH_SIZE')
 if hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest()!=receipt['sourceSHA256']:raise ValueError('PRODUCT_SOURCE_IDENTITY')
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz')as t:
  members=t.getmembers();names=[v.name for v in members]
  if set(names)!=set(pins)or len(names)!=count or any(not v.isfile()or v.size>2*MIB for v in members):raise ValueError('PRODUCT_FULL_SOURCE_ARCHIVE')
  for member in members:
   safe_relative(member.name,'native/betasim-application09/'if member.name.startswith('native/betasim-application09/')and application=='vn.rtr.aeris.betasim09'else'native/betasim-integrated01/')
   if hashlib.sha256(t.extractfile(member).read()).hexdigest()!=pins[member.name]:raise ValueError('PRODUCT_ARCHIVED_INPUT_SHA')
 with zipfile.ZipFile(io.BytesIO(apk))as z:
  identity=json.loads(z.read('assets/source-identity.json'))
  if identity.get('format')!='aeris-betasim-product-source-identity'or identity.get('version')!=1 or identity.get('sourceSHA256')!=receipt['sourceSHA256']or identity.get('package')!=application or identity.get('production')is not False:raise ValueError('PRODUCT_PACKAGED_SOURCE_IDENTITY')
  raw=z.read('assets/product-protocol.json');h=hashlib.sha256(raw).hexdigest()
  if h!=receipt['productProtocolSHA256']or h!=identity.get('productProtocolSHA256'):raise ValueError('PRODUCT_PACKAGED_PROTOCOL_SHA')
 return receipt

def _native_verify(receipt,archive,apk):
 if receipt.get('productKind')=='BETASIM_INTEGRATED':return _product_native_verify(receipt,archive,apk)
 if receipt.get('productionSigning') is not False or receipt.get('certificateSHA256')!=CERT or receipt.get('sourceCount')!=51 or type(receipt.get('sourceCount')) is not int or type(receipt.get('sourcePins')) is not dict or len(receipt['sourcePins'])!=51:raise ValueError('DEVELOPMENT_NATIVE51_RECEIPT')
 if hashlib.sha256(apk).hexdigest()!=receipt['sha256'] or len(apk)!=receipt['bytes']:raise ValueError('NATIVE_APK_HASH_SIZE')
 if hashlib.sha256(json.dumps(receipt['sourcePins'],sort_keys=True).encode()).hexdigest()!=receipt['sourceSHA256']:raise ValueError('NATIVE_SOURCE_IDENTITY')
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as t:
  members=t.getmembers();names=[x.name for x in members]
  if set(names)!=set(receipt['sourcePins']) or len(names)!=51 or any(not x.isfile() or x.size>2*MIB for x in members):raise ValueError('NATIVE51_INPUT_ARCHIVE')
  for x in members:
   safe_relative(x.name,'native/mission-runtime/')
   if hashlib.sha256(t.extractfile(x).read()).hexdigest()!=receipt['sourcePins'][x.name]:raise ValueError('NATIVE_RETAINED_INPUT_SHA')
 with zipfile.ZipFile(io.BytesIO(apk)) as z:
  identity=json.loads(z.read('assets/source-identity.json'))
  if identity.get('sourceSHA256')!=receipt['sourceSHA256'] or identity.get('package')!='vn.rtr.aeris.mission' or identity.get('production') is not False:raise ValueError('NATIVE_APK_PACKAGED_IDENTITY')
  for key,field in [('release','releaseProtocolSHA256'),('ioadmit','ioadmitProtocolSHA256'),('terminal','terminalProtocolSHA256'),('mission-bootstrap','missionProtocolSHA256')]:
   h=hashlib.sha256(z.read('assets/'+key+'-protocol.json')).hexdigest()
   if h!=receipt[field] or identity[field]!=h:raise ValueError('NATIVE_PACKAGED_PROTOCOL')
 return receipt

def freeze(root,native_receipt,qa_gate,*,label,_reuse_from=None,_reuse15_from=None,preview_only=False):
 if type(preview_only)is not bool:raise ValueError('CANDIDATE_PREVIEW_BOOLEAN')
 raw_root=Path(root).absolute()
 if any(p.is_symlink()for p in[raw_root,*raw_root.parents]):raise ValueError('CANDIDATE_ROOT_NO_SYMLINK')
 root=raw_root.resolve();repo=repository();receipt_raw=Path(native_receipt).read_bytes();native=json.loads(receipt_raw);gate=json.loads(Path(qa_gate).read_bytes())
 if type(label)is not str or re.fullmatch('[a-z0-9-]{1,64}',label)is None or gate.get('status')!='PASS':raise ValueError('INDEPENDENT_CHANGED_CLOSURE_GATE_REQUIRED')
 payload={str(Path('aeris_runtime')/p.relative_to(PACKAGE_ROOT)):p.read_bytes() for p in sorted(PACKAGE_ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.json','.txt','.parm')}
 source_pins={n:hashlib.sha256(raw).hexdigest() for n,raw in payload.items()}
 if gate.get('sourceSHA256')!=source_pins or gate.get('nativeBuildReceiptSHA256')!=hashlib.sha256(receipt_raw).hexdigest():raise ValueError('INDEPENDENT_GATE_EXACT_CHANGED_CLOSURE')
 if native.get('productKind')=='BETASIM_INTEGRATED'and root!=repo/'evidence/vidlife12/candidates':raise ValueError('EXACT_NEW_PRODUCT_ARTIFACT_ROOT')
 apk_path=(repo/native['apk']).resolve();archive_path=(repo/native['inputArchive']).resolve()
 if _reuse15_from is not None:
  predecessor=repo/OLD15_ARTIFACTS/'c26586cc36f2a540a001fb616460aad90255cb936b92cc4f76311609acc9ed4b'
  if root!=repo/ATOMIC_EVIDENCE/'candidates'or Path(_reuse15_from).resolve()!=predecessor.resolve()or Path(native_receipt).resolve()!=predecessor/'native-build-receipt.json'or _reuse_from is not None:raise ValueError('EXACT_NATIVE15_FRESH_ATOMIC_SCOPE_REUSE')
  inherited=load(predecessor,predecessor.name)
  if inherited['native']['APK_SHA256']!='f459c7a90d714afc653985607df0c29587ae1cdc57a97359787b131ad6e31425'or inherited['native']['sourceSHA256']!='43a694e73a077eb2ea06481aa68e010021e23e5bb3cf8b27b70bd0ae1814b5a7'or sha(native_receipt)!='f7edb0f26931d0f12a24b30577e863e76c006fe7941130ea53ef97b77d2918cb':raise ValueError('EXACT_INSTALLED_NATIVE15_ORIGINAL_RECEIPT')
  apk=(predecessor/'native.apk').read_bytes();original=(predecessor/'native-inputs.tar.gz').read_bytes()
  if hashlib.sha256(original).hexdigest()!='500ceb18a23c23e5e6bd43fcfbcd3af15822960a497584c4756a2e6602028118':raise ValueError('EXACT_NATIVE15_GZIP_BYTES')
 elif _reuse_from is None:
  if root!=repo/'evidence/vidlife12/candidates'or apk_path.parent!=repo/'evidence/betasim-integrated01/candidates'or archive_path.parent!=apk_path.parent or native.get('sha256')!='8bc0a7c612c010f77e3e8c66fa6126d1d6992821eafa4f88c31a598bc188b1e1':raise ValueError('EXACT_IPC10_RETAINED_NATIVE8BC_SOURCE')
  apk=apk_path.read_bytes();original=archive_path.read_bytes()
 else:
  fixed='13255030352488d60e805b108939725f1e438b93551cdb9adcc4bb46784e46f9'
  predecessor=repo/'evidence/runtime-navigation12/candidates'/fixed
  if Path(_reuse_from).resolve()!=predecessor.resolve()or Path(native_receipt).resolve()!=predecessor/'native-build-receipt.json':raise ValueError('EXACT_UNCHANGED_NAVIGATION12_NATIVE_REUSE')
  inherited=load(predecessor,fixed)
  if inherited['native']['APK_SHA256']!='eb83d04026cc4b5da6962d7efb6578542b573758c4269969fc87dc53087fd9f1'or sha(native_receipt)!=inherited['native']['buildReceiptSHA256']:raise ValueError('UNCHANGED_NATIVE12_ORIGINAL_RECEIPT')
  apk=(predecessor/'native.apk').read_bytes();original=(predecessor/'native-inputs.tar.gz').read_bytes()

 if hashlib.sha256(original).hexdigest()!=native['inputArchiveSHA256']:raise ValueError('NATIVE_BUILD_INPUT_ARCHIVE_SHA')
 archive=original if original[:2]==b'\x1f\x8b' else gzip.compress(original,mtime=0);_native_verify(native,archive,apk)
 extras={'native.apk':apk,'native-inputs.tar.gz':archive,'native-build-receipt.json':receipt_raw,'qa-gate.json':Path(qa_gate).read_bytes()}
 # Build the exact immutable manifest and allocation plan BEFORE any write.
 store=root/'objects';unique={hashlib.sha256(v).hexdigest():v for v in[*payload.values(),*extras.values()]};held_native=[(apk_path,apk),(archive_path,archive)]if native.get('productKind')=='BETASIM_INTEGRATED'and _reuse_from is None and _reuse15_from is None else[]
 origins,reuse=immutable_object_plan(root,unique,held_native);objects={name:(hashlib.sha256(raw).hexdigest(),store/hashlib.sha256(raw).hexdigest())for name,raw in payload.items()};extra_objects={name:(hashlib.sha256(raw).hexdigest(),store/hashlib.sha256(raw).hexdigest())for name,raw in extras.items()}
 external={name:sha(repo/name) for name in LEAVES}
 for variant in ('nominal','loss'):
  for name in ('run-profile02.json','control.parm','typed-profile.json'):
   rel='pilot/betaintegrated01/cockpit04/profiles/'+variant+'/'+name;external[rel]=sha(repo/rel)
 for rel in ('runtime/betaintegrated01/dist/arducopter-m1-stagepipe-03','runtime/betaintegrated01/dist/clockprobe','runtime/betaintegrated01/dist/copter.parm'):external[rel]=sha(repo/rel)
 manifest={'format':'aeris-runtime-candidate','version':1,'label':label,'sourceSHA256':{n:h for n,(h,p) in objects.items()},'externalFrozenSHA256':external,'native':{'package':'vn.rtr.aeris.mission','APK_SHA256':native['sha256'],'sourceSHA256':native['sourceSHA256'],'buildReceiptSHA256':hashlib.sha256(receipt_raw).hexdigest(),'sourcePins':native['sourcePins'],'developmentOnly':True},'retainedObjects':{n:h for n,(h,p) in extra_objects.items()},'qaGateSHA256':sha(qa_gate),'activeSourceMayChangeAfterAttempt':True,'artifactCapBytes':CAP,'simulationOnly':True}
 if native.get('productKind')=='BETASIM_INTEGRATED':
  from .product_inputs import validate
  product=validate()
  if gate.get('productSourceSHA256')!=product['pins']:raise ValueError('INDEPENDENT_PRODUCT_READONLY_GRAPH_GATE')
  manifest['productSourceSHA256']=product['pins'];manifest['productInputClosure']=product;manifest['native'].update(productKind='BETASIM_INTEGRATED',productProtocolSHA256=native['productProtocolSHA256'],package=native.get('package','vn.rtr.aeris.mission'),activity='vn.rtr.aeris.mission.ProductActivity'if native.get('package')=='vn.rtr.aeris.betasim09'else'.ProductActivity')
 if native.get('productKind')=='BETASIM_INTEGRATED':manifest['immutableObjectReuse']=reuse
 digest=hashlib.sha256(canonical(manifest)).hexdigest();target=root/digest
 if target.exists():raise ValueError('CANDIDATE_EXISTS_NO_REWRITE')
 destinations=[target/'candidate.json',target/'candidate.sha256',*[target/'source'/n for n in payload],*[target/n for n in extras],*[store/h for h in unique]];directories=set()
 for destination in destinations:
  parent=destination.parent
  while parent.is_relative_to(root):
   if not parent.exists():directories.add(parent)
   if parent==root:break
   parent=parent.parent
 round4=lambda n:((n+4095)//4096)*4096
 new_objects=sum(round4(len(raw))for h,raw in unique.items()if h not in origins);manifest_bytes=canonical(manifest)+b'\n';namespace_bytes=round4(len(manifest_bytes))+round4(65)+len(directories)*4096;additional=new_objects+namespace_bytes;before=allocated_artifact_union(root)
 if before+additional>CAP or shutil.disk_usage(repo).free-additional<10*2**30+256*MIB:raise ValueError('CANDIDATE_PREFLIGHT_ARTIFACT8MiB_DISK10GiB:'+str({'current':before,'newObjects':new_objects,'manifestAndDirectoryBound':namespace_bytes,'newDirectoryCount':len(directories),'projected':before+additional,'cap':CAP}))
 reuse_before={h:{'origin':str(path.relative_to(repo)),'mode':stat.S_IMODE(path.stat().st_mode),'linkCount':path.stat().st_nlink,'sha256':sha(path)}for h,path in origins.items()}
 # IPC10 reuses the selected APK/archive as already immutable inputs. Never
 # chmod old artifacts, mutate their bytes or reset native lifetime state.
 for path,raw in held_native:
  if path.parent!=repo/'evidence/betasim-integrated01/candidates'or _readonly_content_origin(path,hashlib.sha256(raw).hexdigest(),raw)is None:raise ValueError('RETAINED_NATIVE_HOLD_DRIFT')
 if preview_only:return {'status':'PURE_FREEZE_ALLOCATION_PREVIEW_NO_MUTATION','path':str(target),'sha256':digest,'sourceFiles':len(payload),'nativeAPKSHA256':native['sha256'],'allocationPreflight':{'beforeBytes':before,'newObjectBoundBytes':new_objects,'manifestAndDirectoryBoundBytes':namespace_bytes,'projectedBytes':before+additional,'cap':CAP},'sourceAndGateValidated':True,'candidateCreated':False,'oldNativeModeOrBytesChanged':False,'immutableOrigins':reuse_before}
 root.mkdir(parents=True,exist_ok=True);store.mkdir(exist_ok=True)
 objects={name:_object(store,raw,origins.get(hashlib.sha256(raw).hexdigest()))for name,raw in payload.items()};extra_objects={name:_object(store,raw,origins.get(hashlib.sha256(raw).hexdigest()))for name,raw in extras.items()}
 target.mkdir();(target/'source').mkdir()
 for name,(h,obj) in objects.items():dest=target/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);os.link(obj,dest)
 for name,(h,obj) in extra_objects.items():os.link(obj,target/name)
 for directory in sorted([p for p in target.rglob('*') if p.is_dir()],key=lambda p:len(p.parts),reverse=True):
  fd=os.open(directory,os.O_RDONLY)
  try:os.fsync(fd)
  finally:close_fd(fd)
 put(target/'candidate.json',manifest_bytes);put(target/'candidate.sha256',(digest+'\n').encode());(target/'candidate.json').chmod(0o444);(target/'candidate.sha256').chmod(0o444)
 if allocated_artifact_union(root)>CAP:raise ValueError('ARTIFACT8MiB_FAILED_PREFIX_RETAINED')
 return {'path':str(target),'sha256':digest,'allocatedUniqueBytes':allocated_artifact_union(root),'sourceFiles':len(payload),'nativeAPKSHA256':native['sha256'],'allocationPreflight':{'beforeBytes':before,'newObjectBoundBytes':new_objects,'manifestAndDirectoryBoundBytes':namespace_bytes,'projectedBytes':before+additional},'immutableReuseLinks':[{'sha256':h,**row,'linkCountAfter':origins[h].stat().st_nlink,'modeAfter':stat.S_IMODE(origins[h].stat().st_mode),'bytesUnchanged':sha(origins[h])==h}for h,row in reuse_before.items()]}
def freeze_reusing_native(root,predecessor,qa_gate,*,label):
 """Package exact N12 development bytes; no new build/sign receipt is issued."""
 predecessor=Path(predecessor).resolve()
 return freeze(root,predecessor/'native-build-receipt.json',qa_gate,label=label,_reuse_from=predecessor)

def freeze_reusing_native15(root,predecessor,qa_gate,*,label):
 """One fresh atomic scope, exact installed f459 bytes; no build or install."""
 predecessor=Path(predecessor).resolve()
 return freeze(root,predecessor/'native-build-receipt.json',qa_gate,label=label,_reuse15_from=predecessor)

def load(path,expected_sha):
 path=Path(path).resolve();manifest_raw=(path/'candidate.json').read_bytes();v=json.loads(manifest_raw)
 if manifest_raw!=canonical(v)+b'\n':raise ValueError('EXACT_CANONICAL_MANIFEST_BYTES')
 if type(expected_sha)is not str or re.fullmatch('[a-f0-9]{64}',expected_sha)is None or hashlib.sha256(canonical(v)).hexdigest()!=expected_sha or v.get('format')!='aeris-runtime-candidate' or type(v.get('version'))is not int or v['version']!=1 or v.get('simulationOnly')is not True:raise ValueError('CANDIDATE_DIGEST_SCHEMA')
 for name,h in v['sourceSHA256'].items():
  safe_relative(name,'aeris_runtime/');p=path/'source'/name
  if p.is_symlink() or sha(p)!=h:raise ValueError('CANDIDATE_CODE_DRIFT:'+name)
  if v['native'].get('productKind')=='BETASIM_INTEGRATED'and(any(q.is_symlink()for q in[p,*p.parents])or not stat.S_ISREG(p.stat().st_mode)or p.stat().st_mode&0o222):raise ValueError('PRODUCT_CODE_NOT_IMMUTABLE_REGULAR_SOURCE')
 for name,h in v['externalFrozenSHA256'].items():
  safe_relative(name)
  if sha(repository()/name)!=h:raise ValueError('FROZEN_LEAF_DRIFT:'+name)
 if v['native'].get('productKind')=='BETASIM_INTEGRATED':
  from .product_inputs import validate
  product=validate(v.get('productInputClosure'))
  if v.get('productSourceSHA256')!=product['pins']:raise ValueError('PRODUCT_TRANSITIVE_READONLY_SOURCE_DRIFT')
 reuse=v.get('immutableObjectReuse')
 if reuse is not None:
  if reuse.get('version')!=1 or reuse.get('writablePlanningSourceLinked')is not False or reuse.get('oldOriginModeOrBytesChanged')is not False:raise ValueError('IMMUTABLE_REUSE_SCHEMA')
  pools=reuse['poolRoots'];expected=[str(Path(OLD15_ARTIFACTS)/'objects'),str(Path(ATOMIC_EVIDENCE)/'candidates/objects')]
  if path.parent in(repository()/'evidence/hosthealth-ipc10/candidates',repository()/'evidence/hostdiag11/candidates',repository()/'evidence/vidlife12/candidates'):expected+=[str(Path('evidence/betasim-integrated01/candidates/objects'))]
  if path.parent in(repository()/'evidence/hostdiag11/candidates',repository()/'evidence/vidlife12/candidates'):expected+=[str(Path('evidence/hosthealth-ipc10/candidates/objects'))]
  if path.parent==repository()/'evidence/vidlife12/candidates':expected+=['evidence/hostdiag11/candidates/objects']
  if pools!=expected:raise ValueError('IMMUTABLE_REUSE_DECLARED_POOLS')
  for h,row in reuse['objects'].items():
   if re.fullmatch('[a-f0-9]{64}',h)is None or type(row.get('bytes'))is not int or row['bytes']<0 or type(row.get('mode'))is not int or row['mode']&0o222:raise ValueError('IMMUTABLE_REUSE_VALUE_SCHEMA')
   if'heldNative'in row:
    if set(row)!={'heldNative','bytes','mode'}:raise ValueError('IMMUTABLE_HELD_NATIVE_SCHEMA')
    safe_relative(row['heldNative']);origin=repository()/row['heldNative']
    if origin.parent!=(repository()/'evidence/betasim-integrated01/candidates'if path.parent in(repository()/'evidence/hosthealth-ipc10/candidates',repository()/'evidence/hostdiag11/candidates',repository()/'evidence/vidlife12/candidates')else path.parent)or h not in(v['retainedObjects']['native.apk'],v['retainedObjects']['native-inputs.tar.gz']):raise ValueError('IMMUTABLE_HELD_NATIVE_SELECTED_SCOPE')
   else:
    if set(row)!={'pool','bytes','mode'}or type(row['pool'])is not int or not 0<=row['pool']<len(pools):raise ValueError('IMMUTABLE_OLD_POOL_SCHEMA')
    origin=repository()/pools[row['pool']]/h
   if any(p.is_symlink()for p in[origin,*origin.parents])or not origin.is_file()or stat.S_IMODE(origin.stat().st_mode)!=row['mode']or origin.stat().st_size!=row['bytes']or sha(origin)!=h:raise ValueError('IMMUTABLE_REUSE_ORIGIN_DRIFT')
 for name,h in v['retainedObjects'].items():
  safe_relative(name)
  if sha(path/name)!=h:raise ValueError('RETAINED_CANDIDATE_OBJECT_DRIFT')
 receipt=json.loads((path/'native-build-receipt.json').read_bytes());_native_verify(receipt,(path/'native-inputs.tar.gz').read_bytes(),(path/'native.apk').read_bytes())
 if sha(path/'native-build-receipt.json')!=v['native']['buildReceiptSHA256'] or receipt['sourcePins']!=v['native']['sourcePins'] or receipt['sourceSHA256']!=v['native']['sourceSHA256'] or receipt['sha256']!=v['native']['APK_SHA256']:raise ValueError('RETAINED_NATIVE_MANIFEST_BINDING')
 return v
