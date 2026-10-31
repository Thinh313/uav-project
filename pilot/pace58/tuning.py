"""No numeric model changes. Latency scheduling applies only to this process."""
import ctypes,json,sys
encoder=json.JSONEncoder(separators=(',',':'),allow_nan=False)
def configure(mode):
 result={'mode':mode,'receive':'python-select-timeout','qosChanged':False,'numericModelChanged':False,'fsyncBeforeSend':True}
 if mode=='optimized':
  result.update(receive='blocking-SO_RCVTIMEO-100ms',jsonEncoder='reused-stdlib-exact-settings',perFrameSnapshot='reused-within-same-step-only')
  if sys.platform=='darwin':
   lib=ctypes.CDLL('/usr/lib/libSystem.B.dylib');lib.pthread_set_qos_class_self_np.argtypes=[ctypes.c_uint,ctypes.c_int];lib.pthread_set_qos_class_self_np.restype=ctypes.c_int
   lib.pthread_get_qos_class_np.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_uint),ctypes.POINTER(ctypes.c_int)];lib.pthread_get_qos_class_np.restype=ctypes.c_int
   lib.pthread_self.restype=ctypes.c_void_p;relative=ctypes.c_int();qos=ctypes.c_uint()
   code=lib.pthread_get_qos_class_np(lib.pthread_self(),ctypes.byref(qos),ctypes.byref(relative))
   if code:raise RuntimeError('QOS_GET_BEFORE:'+str(code))
   result['qosBefore']=qos.value
   target=max(qos.value,0x19)
   code=lib.pthread_set_qos_class_self_np(target,0);result.update(qosResult=code,qosClass='PRESERVE_HIGHER_OR_USER_INITIATED',qosRequested=target,qosChanged=code==0 and target!=result['qosBefore'])
   if code:raise RuntimeError('DECLARED_QOS_NOT_APPLIED:'+str(code))
   code=lib.pthread_get_qos_class_np(lib.pthread_self(),ctypes.byref(qos),ctypes.byref(relative))
   if code:raise RuntimeError('QOS_GET_AFTER:'+str(code))
   result['qosAfter']=qos.value
   if result['qosAfter']!=target:raise RuntimeError('QOS_READBACK')
 return result
