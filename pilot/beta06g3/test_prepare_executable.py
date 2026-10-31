"""Bounded fixture-only tests. No synthetic executable is executed."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from prepare_executable import prepare, FLOOR_BYTES, BINARY_BYTES, RESERVE_BYTES

class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='.mock-prepare-',dir='pilot/beta06g3')
        self.base=Path(self.tmp.name).absolute();self.src=self.base/'source'
        b=bytearray(64);b[:6]=b'\x7fELF\x02\x01';b[18:20]=(183).to_bytes(2,'little')
        self.src.write_bytes(b);self.src.chmod(0o644)
        self.sha=hashlib.sha256(b).hexdigest();self.dest=self.base/'owned'/'artifact'
    def tearDown(self):self.tmp.cleanup()
    def prep(self,**kwargs):
        return prepare(self.src,self.dest,expected_bytes=64,expected_sha256=self.sha,disk_free=lambda:40*2**30,**kwargs)
    def test_success_exactbytes_mode_only_and_source_unchanged(self):
        before=self.src.stat();r=self.prep()
        self.assertEqual(self.src.read_bytes(),self.dest.read_bytes())
        self.assertEqual(self.src.stat().st_mode&0o777,0o644)
        self.assertEqual(self.src.stat().st_mtime_ns,before.st_mtime_ns)
        self.assertEqual(self.dest.stat().st_mode&0o777,0o755)
        self.assertEqual(r['copiedBytes'],64);self.assertFalse(r['destinationExecuted'])
        self.assertTrue(all(r['fsync'].values()))
    def test_existing_destination_rejected_without_mutation(self):
        self.dest.parent.mkdir();self.dest.write_bytes(b'prior')
        with self.assertRaises(FileExistsError):self.prep()
        self.assertEqual(self.dest.read_bytes(),b'prior')
    def test_existing_destination_symlink_rejected(self):
        self.dest.parent.mkdir();self.dest.symlink_to(self.src)
        with self.assertRaises(FileExistsError):self.prep()
        self.assertEqual(self.src.stat().st_mode&0o777,0o644)
    def test_source_symlink_rejected(self):
        link=self.base/'source-link';link.symlink_to(self.src);self.src=link
        with self.assertRaises(OSError):self.prep()
        self.assertFalse(self.dest.parent.exists())
    def test_symlink_destination_parent_rejected(self):
        elsewhere=self.base/'elsewhere';elsewhere.mkdir();self.dest.parent.symlink_to(elsewhere,target_is_directory=True)
        with self.assertRaises(OSError):self.prep()
        self.assertEqual(list(elsewhere.iterdir()),[])
    def test_wrongsha_before_allocation(self):
        self.sha='0'*64
        with self.assertRaisesRegex(ValueError,'EXACT_SOURCE_SHA'):self.prep()
        self.assertFalse(self.dest.parent.exists())
    def test_wrongarchitecture_before_allocation(self):
        b=bytearray(self.src.read_bytes());b[18:20]=(62).to_bytes(2,'little');self.src.write_bytes(b);self.sha=hashlib.sha256(b).hexdigest()
        with self.assertRaisesRegex(ValueError,'ELF64_LE_AARCH64'):self.prep()
        self.assertFalse(self.dest.parent.exists())
    def test_disk_shortage_before_allocation(self):
        with self.assertRaisesRegex(ValueError,'DISK_FLOOR_PLUS_COPY'):
            prepare(self.src,self.dest,expected_bytes=64,expected_sha256=self.sha,disk_free=lambda:FLOOR_BYTES+RESERVE_BYTES+63)
        self.assertFalse(self.dest.parent.exists())
    def test_disk_loss_retains_partial_and_never_overwrites(self):
        values=iter([40*2**30,FLOOR_BYTES-1])
        with self.assertRaisesRegex(ValueError,'DISK_FLOOR_LOST_PARTIAL'):
            prepare(self.src,self.dest,expected_bytes=64,expected_sha256=self.sha,disk_free=lambda:next(values))
        self.assertTrue(self.dest.exists());self.assertEqual(self.dest.stat().st_mode&0o777,0o600)
        with self.assertRaises(FileExistsError):self.prep()
    def test_source_mode_and_fixed_budget_guard(self):
        self.src.chmod(0o755)
        with self.assertRaisesRegex(ValueError,'EXACT_SOURCE_REGULAR_SIZE_MODE'):self.prep()
        with self.assertRaisesRegex(ValueError,'FIXED_MAX_ARTIFACT'):
            prepare(self.src,self.dest,expected_bytes=BINARY_BYTES+1)

if __name__=='__main__':unittest.main()
