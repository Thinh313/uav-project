import os, sys, fcntl, json
fd = None
try:
    fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    st = os.fstat(fd)
    if st.st_nlink != 1 or st.st_uid != os.getuid():
        raise RuntimeError('LOCK_INODE_OWNER')
    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    print(json.dumps({'ready': True, 'pid': os.getpid()}), flush=True)
    # The parent owns this pipe; SIGKILL/exit closes it without deleting the inode.
    sys.stdin.buffer.read()
except BlockingIOError:
    print(json.dumps({'error': 'WRITER_LOCK_BUSY'}), flush=True)
    sys.exit(73)
except Exception as e:
    print(json.dumps({'error': 'LOCK_FAILED', 'kind': type(e).__name__}), flush=True)
    sys.exit(74)
finally:
    if fd is not None:
        os.close(fd)
