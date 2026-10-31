"""Exclusive bounded engineering artifact preparation; never executes the artifact."""
from pathlib import Path
import hashlib
import os
import stat

BINARY_SHA256='1d3479f1fd2b9c6d85c95f38eeb8c105e6735ea1dc372736ddc07efd5162fc41'
BINARY_BYTES=7_172_336
FLOOR_BYTES=20 * 2**30
RESERVE_BYTES=64 * 1024
CHUNK_BYTES=64 * 1024


def _directory_fd(path):
    path=Path(path).absolute()
    fd=os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts[1:]:
            nxt=os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd);fd=nxt
        return fd
    except BaseException:
        os.close(fd);raise


def _hash_fd(fd):
    os.lseek(fd,0,os.SEEK_SET)
    h=hashlib.sha256()
    while True:
        block=os.read(fd,CHUNK_BYTES)
        if not block:break
        h.update(block)
    return h.hexdigest()


def _identity(s):
    return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,stat.S_IMODE(s.st_mode))


def prepare(source, destination, *, expected_sha256=BINARY_SHA256,
            expected_bytes=BINARY_BYTES, floor_bytes=FLOOR_BYTES,
            reserve_bytes=RESERVE_BYTES, disk_free=None):
    """Optional disk_free callable is an offline test seam; actual caller omits it."""
    source=Path(source).absolute();destination=Path(destination).absolute()
    if expected_bytes<=0 or expected_bytes>BINARY_BYTES or floor_bytes<FLOOR_BYTES or reserve_bytes<RESERVE_BYTES:
        raise ValueError('FIXED_MAX_ARTIFACT_AND_MINIMUM_FLOOR_REQUIRED')
    src_parent=_directory_fd(source.parent)
    source_fd=dest_parent=dest_fd=None
    parent_created=False
    try:
        source_fd=os.open(source.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=src_parent)
        before=os.fstat(source_fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size!=expected_bytes or stat.S_IMODE(before.st_mode)!=0o644:
            raise ValueError('EXACT_SOURCE_REGULAR_SIZE_MODE0644_REQUIRED')
        if _hash_fd(source_fd)!=expected_sha256:
            raise ValueError('EXACT_SOURCE_SHA_REQUIRED')
        os.lseek(source_fd,0,os.SEEK_SET);header=os.read(source_fd,64)
        if len(header)<64 or header[:6]!=b'\x7fELF\x02\x01' or int.from_bytes(header[18:20],'little')!=183:
            raise ValueError('ELF64_LE_AARCH64_REQUIRED')
        # Source and all existing parents checked before creating any directory.
        grand=_directory_fd(destination.parent.parent)
        try:
            if disk_free is None:
                def free():
                    v=os.fstatvfs(grand);return v.f_bavail*v.f_frsize
            else:free=disk_free
            free_before=free()
            if free_before<floor_bytes+expected_bytes+reserve_bytes:
                raise ValueError('DISK_FLOOR_PLUS_COPY_RESERVE_REQUIRED')
            try:
                dest_parent=os.open(destination.parent.name,os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,dir_fd=grand)
            except FileNotFoundError:
                os.mkdir(destination.parent.name,mode=0o700,dir_fd=grand)
                os.fsync(grand);parent_created=True
                dest_parent=os.open(destination.parent.name,os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,dir_fd=grand)
            # Exclusive nofollow means an existing regular file OR symlink fails.
            dest_fd=os.open(destination.name,os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,0o600,dir_fd=dest_parent)
            os.lseek(source_fd,0,os.SEEK_SET);copied=0
            while copied<expected_bytes:
                if free()<floor_bytes+reserve_bytes:
                    raise ValueError('DISK_FLOOR_LOST_PARTIAL_ARTIFACT_RETAINED')
                block=os.read(source_fd,min(CHUNK_BYTES,expected_bytes-copied))
                if not block:raise ValueError('SOURCE_SHRANK_PARTIAL_ARTIFACT_RETAINED')
                view=memoryview(block)
                while view:
                    count=os.write(dest_fd,view)
                    if count<=0:raise OSError('COPY_WRITE_INCOMPLETE')
                    view=view[count:]
                copied+=len(block)
            if os.read(source_fd,1) or _identity(before)!=_identity(os.fstat(source_fd)):
                raise ValueError('SOURCE_DRIFT_PARTIAL_ARTIFACT_RETAINED')
            os.fsync(dest_fd)
            os.fchmod(dest_fd,0o755);os.fsync(dest_fd);os.fsync(dest_parent)
            after=os.fstat(source_fd);dest_stat=os.fstat(dest_fd)
            source_sha=_hash_fd(source_fd);dest_sha=_hash_fd(dest_fd)
            if _identity(before)!=_identity(after) or source_sha!=expected_sha256 or dest_sha!=expected_sha256 or dest_stat.st_size!=expected_bytes or stat.S_IMODE(dest_stat.st_mode)!=0o755:
                raise ValueError('POSTCOPY_IDENTITY_OR_SHA_FAILED_ARTIFACT_RETAINED')
            if _identity(before)!=_identity(os.fstat(source_fd)) or _identity(before)!=_identity(os.stat(source.name,dir_fd=src_parent,follow_symlinks=False)) or _identity(dest_stat)!=_identity(os.stat(destination.name,dir_fd=dest_parent,follow_symlinks=False)):
                raise ValueError('FINAL_PATH_IDENTITY_DRIFT_ARTIFACT_RETAINED')
            free_after=free()
            if free_after<floor_bytes+reserve_bytes:
                raise ValueError('POSTCOPY_DISK_FLOOR_LOST_ARTIFACT_RETAINED')
            return {'source':{'path':str(source),'sha256':source_sha,'bytes':after.st_size,'mode':'0644','identityUnchanged':True},
                    'destination':{'path':str(destination),'sha256':dest_sha,'bytes':dest_stat.st_size,'mode':'0755','exclusiveCreated':True},
                    'disk':{'freeBeforeBytes':free_before,'freeAfterBytes':free_after,'floorBytes':floor_bytes,'metadataReserveBytes':reserve_bytes},
                    'fsync':{'fileAfterCopy':True,'fileAfterMode':True,'destinationParent':True,'newParentParent':parent_created},
                    'copiedBytes':copied,'chunkMaximumBytes':CHUNK_BYTES,'sourceExecuted':False,'destinationExecuted':False,
                    'dockerOrGuestStarted':False,'existingPathsOverwritten':False,'engineeringPreparationOnly':True}
        finally:os.close(grand)
    finally:
        for fd in [dest_fd,dest_parent,source_fd,src_parent]:
            if fd is not None:os.close(fd)
