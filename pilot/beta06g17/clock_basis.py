"""MOCK-ONLY candidate: explicit shared macOS uptime basis, never a time patch."""
import re,subprocess,sys,time
BASIS='MACOS_CLOCK_UPTIME_RAW_NS_SAME_HOST_BOOT_V1'
UUID_RE=r'[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}'
class ClockContractError(ValueError):pass
def require(value,message):
 if not value:raise ClockContractError(message)
def now_ns(*,reader=None,clock_id=None,platform=None):
 require((sys.platform if platform is None else platform)=='darwin','UNSUPPORTED_CLOCK_PLATFORM_NO_FALLBACK')
 expected=getattr(time,'CLOCK_UPTIME_RAW',None);require(type(expected)is int and callable(getattr(time,'clock_gettime_ns',None)),'UPTIME_RAW_NS_UNAVAILABLE_NO_FALLBACK')
 selected=expected if clock_id is None else clock_id;require(type(selected)is int and selected==expected,'WRONG_CLOCK_SLEEP_BASIS_NO_FALLBACK')
 try:value=(time.clock_gettime_ns if reader is None else reader)(selected)
 except Exception as exc:raise ClockContractError('UPTIME_RAW_NS_READ_FAILED_NO_FALLBACK')from exc
 require(type(value)is int and value>=0,'NONNEGATIVE_INTEGER_UPTIME_NS_REQUIRED');return value
def now_s(**kwargs):return now_ns(**kwargs)/1000000000
def boot_id():
 raw=subprocess.check_output(['/usr/sbin/sysctl','-n','kern.bootsessionuuid'],timeout=2);require(len(raw)<=128,'BOUNDED_HOST_BOOT_ID_REQUIRED')
 value=raw.decode('ascii').strip();require(re.fullmatch(UUID_RE,value)is not None,'EXACT_HOST_BOOT_UUID_REQUIRED');return value
def same_contract(expected_boot,observed_boot,basis):
 require(basis==BASIS,'MIXED_CLOCK_BASIS_REFUSED');require(isinstance(expected_boot,str)and re.fullmatch(UUID_RE,expected_boot)is not None and expected_boot==observed_boot,'SAME_HOST_BOOT_REQUIRED');return True
