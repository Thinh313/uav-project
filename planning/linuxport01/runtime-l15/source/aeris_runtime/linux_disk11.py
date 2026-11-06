"""Linux probe for darwin_disk11.HostDiskObserver; same bounded, non-authorizing contract.

procfs replaces libproc. Linux has no per-process UUID, so the 16-byte identity
is derived from boot_id, pid and starttime; (pid, starttime) still detects PID
reuse. Written bytes come from /proc/<pid>/io and footprint is VmRSS. An
unreadable process raises like proc_pid_rusage EPERM and the observer skips it.
No command lines, environment, file contents or recursive host scan.
"""
from pathlib import Path
import errno,hashlib,os,re,stat,sys,time
from .darwin_disk11 import MAX_PIDS,PATHS,UNKNOWN,F_PRESENT,F_MISSING,F_ERROR,F_SYMLINK,F_NOT_REGULAR

def fixed_paths(spec,swaps='/proc/swaps'):
 """Exact declared candidates, including absent paths, never a recursive scan."""
 avd=Path(spec['AVD']).absolute()
 rows=[avd/n for n in('userdata-qemu.img.qcow2','userdata-qemu.img','cache.img.qcow2','cache.img','sdcard.img','encryptionkey.img','snapshots/default_boot/ram.img')]
 for line in Path(swaps).read_text().splitlines()[1:]:
  fields=line.split()
  if len(fields)>=2 and fields[1]=='file':rows.append(Path(fields[0]))
 if len(rows)>PATHS or len(set(map(str,rows)))!=len(rows):raise ValueError('HOSTDISK11_PATH_SET')
 return rows

class LinuxProbe:
 """Read-only procfs/statvfs calls. Missing data is an errno, not zero."""
 def __init__(self,volume,*,now=time.monotonic_ns,proc='/proc'):
  if sys.platform!='linux':raise RuntimeError('HOSTDISK11_LINUX_ONLY')
  self.volume=Path(volume);self.now=now;self.proc=Path(proc);self.boot=(self.proc/'sys/kernel/random/boot_id').read_bytes().strip()
  if len(self.boot)!=36:raise RuntimeError('HOSTDISK11_BOOT_ID')
 def volume_free(self):
  value=os.statvfs(self.volume);return value.f_bavail*value.f_frsize
 def volume_device(self):return self.volume.stat().st_dev
 def volume_inode(self):return self.volume.stat().st_ino
 def swap_used(self):
  try:
   text=(self.proc/'meminfo').read_text();total=re.search(r'^SwapTotal:\s+(\d+) kB$',text,re.M);free=re.search(r'^SwapFree:\s+(\d+) kB$',text,re.M)
   if total is None or free is None or int(free.group(1))>int(total.group(1)):return UNKNOWN
   return(int(total.group(1))-int(free.group(1)))*1024
  except OSError:return UNKNOWN
 def pids(self):
  try:names=os.listdir(self.proc)
  except OSError as e:raise OSError(e.errno or errno.EIO,'proc_listallpids')from e
  values=sorted(int(n)for n in names if n.isdigit()and int(n)>0)
  if not values:raise OSError(errno.EIO,'proc_listallpids')
  return values[:MAX_PIDS],len(values)>=MAX_PIDS
 def process(self,pid):
  base=self.proc/str(pid)
  fields=(base/'stat').read_bytes().rsplit(b')',1)[1].split();start=int(fields[19])
  io=re.search(r'^write_bytes: (\d+)$',(base/'io').read_text(),re.M)
  if io is None:raise OSError(errno.EIO,'proc_pid_io')
  rss=re.search(r'^VmRSS:\s+(\d+) kB$',(base/'status').read_text(),re.M);raw=(base/'comm').read_bytes().rstrip(b'\n')
  identity=hashlib.sha256(self.boot+b'\0'+str(pid).encode()+b'\0'+str(start).encode()).digest()[:16]
  return {'pid':pid,'start':start,'uuid':identity,'written':int(io.group(1)),'footprint':int(rss.group(1))*1024 if rss else 0,'name':raw[:8],'nameTruncated':len(raw)>8,'nameUnavailable':not raw}
 def physical(self,path):
  try:
   if any(p.is_symlink()for p in[path,*path.parents]):return(F_SYMLINK,0,0,0,0)
   s=path.lstat()
   if not stat.S_ISREG(s.st_mode):return(F_NOT_REGULAR,0,s.st_dev,s.st_ino,0)
   return(F_PRESENT,0,s.st_dev,s.st_ino,s.st_blocks*512)
  except FileNotFoundError:return(F_MISSING,errno.ENOENT,0,0,0)
  except OSError as e:return(F_ERROR,e.errno or errno.EIO,0,0,0)
