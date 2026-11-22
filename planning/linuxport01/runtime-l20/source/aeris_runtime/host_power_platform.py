"""Host power command and parser per platform. Thresholds stay with callers.

Darwin: unchanged `pmset -g batt` text and parsing. Linux: `cat` of exactly
one mains `online` file and one system battery `capacity` file in sysfs, so
the original output is "<0|1>\n<0..100>\n". Missing or ambiguous supplies
refuse; no source is ever assumed or defaulted.
"""
from pathlib import Path
import re,sys

SYSFS=Path('/sys/class/power_supply')
LINUX=re.compile(r'([01])\n([0-9]{1,3})\n')

def _read(p):return Path(p).read_text().strip()

def linux_sources(root=SYSFS):
 mains=[];batteries=[]
 for d in sorted(Path(root).iterdir()):
  kind=_read(d/'type')
  if kind=='Mains'and(d/'online').is_file():mains.append(d/'online')
  elif kind=='Battery'and(d/'capacity').is_file()and(not(d/'scope').exists()or _read(d/'scope')=='System'):batteries.append(d/'capacity')
 if len(mains)!=1 or len(batteries)!=1:raise RuntimeError('UNKNOWN_POWER_SOURCES')
 return mains[0],batteries[0]

def power_argv(platform=sys.platform,root=SYSFS):
 if platform=='darwin':return['pmset','-g','batt']
 if platform=='linux':
  ac,battery=linux_sources(root);return['cat',str(ac),str(battery)]
 raise RuntimeError('UNSUPPORTED_POWER_PLATFORM')

def parse_power(text,platform=sys.platform):
 """Return (AC, batteryPercent) from original command text, else UNKNOWN_POWER."""
 if platform=='darwin':
  m=re.search(r'(\d+)%',text)
  if m is None:raise RuntimeError('UNKNOWN_POWER')
  return"'AC Power'"in text,int(m.group(1))
 if platform=='linux':
  m=LINUX.fullmatch(text)
  if m is None:raise RuntimeError('UNKNOWN_POWER')
  return m.group(1)=='1',int(m.group(2))
 raise RuntimeError('UNSUPPORTED_POWER_PLATFORM')
