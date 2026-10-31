"""Darwin physical extent reservation; never changes logical EOF or writes filler."""
import ctypes,os,sys,shutil
class FStore(ctypes.Structure):
 _fields_=[('flags',ctypes.c_uint),('posmode',ctypes.c_int),('offset',ctypes.c_int64),('length',ctypes.c_int64),('bytesalloc',ctypes.c_int64)]
F_PREALLOCATE=42;F_ALLOCATEALL=4;F_PEOFPOSMODE=3

def native_allocate(fd,length):
 if sys.platform!='darwin':raise OSError('DARWIN_F_PREALLOCATE_REQUIRED_NO_FALLBACK')
 assert ctypes.sizeof(FStore)==32 and FStore.length.offset==16 and FStore.bytesalloc.offset==24
 store=FStore(F_ALLOCATEALL,F_PEOFPOSMODE,0,length,0)
 libc=ctypes.CDLL(None,use_errno=True);fcntl=libc.fcntl;fcntl.argtypes=[ctypes.c_int,ctypes.c_int];fcntl.restype=ctypes.c_int
 result=fcntl(fd,F_PREALLOCATE,ctypes.byref(store))
 if result!=0:
  err=ctypes.get_errno();raise OSError(err,os.strerror(err))
 return int(store.bytesalloc)

def reserve(fd,length,out,trace,allocator=None):
 if not isinstance(length,int)or length<=0:raise ValueError('EXTENT_POSITIVE_LENGTH')
 before=os.fstat(fd);position=os.lseek(fd,0,os.SEEK_CUR)
 if before.st_size!=0 or position!=0:raise RuntimeError('PREALLOCATE_REQUIRES_EMPTY_NEW_WAL')
 if shutil.disk_usage(out).free < 20*2**30+768*2**20+length:raise RuntimeError('PREALLOCATE_DISK_HEADROOM')
 allocated=trace.call('preallocate','EXTENT',0,0,length,lambda:(allocator or native_allocate)(fd,length))
 after=os.fstat(fd);after_position=os.lseek(fd,0,os.SEEK_CUR)
 if after.st_size!=0 or after_position!=0:raise RuntimeError('PREALLOCATE_CHANGED_LOGICAL_FILE')
 if allocated<length:raise RuntimeError('PREALLOCATE_PARTIAL_NO_FALLBACK')
 return {'status':'EXTENT_RESERVED','requestedBytes':length,'returnedAllocatedBytes':allocated,'logicalSizeBefore':before.st_size,'logicalSizeAfter':after.st_size,'positionBefore':position,'positionAfter':after_position,'physicalBytesBefore':before.st_blocks*512,'physicalBytesAfter':after.st_blocks*512,'fcntl':F_PREALLOCATE,'flags':F_ALLOCATEALL,'posmode':F_PEOFPOSMODE,'fstoreSize':ctypes.sizeof(FStore),'persistentReservationFlag':False,'fallback':False}
