"""Authored tiny archives verify integrity refusal; never touch private payloads."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'verify_h10_supplement.py'
spec = importlib.util.spec_from_file_location('verify_h10_supplement', MODULE)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class H10Supplement(unittest.TestCase):
    def temporary(self):
        return tempfile.TemporaryDirectory(prefix='h10-supplement-', dir=MODULE.parent / 'tests')

    def fixture(self, root, members=None):
        root = Path(root)
        archive = root / 'fixture.tar.gz'
        members = members or [('aeris/code.py', b'print("synthetic")\n', 'file', None)]
        rows = []
        with tarfile.open(archive, 'w:gz', format=tarfile.USTAR_FORMAT) as tar:
            for name, data, kind, target in members:
                info = tarfile.TarInfo(name)
                info.mode = 0o644
                info.size = len(data) if kind == 'file' else 0
                if kind == 'hardlink':
                    info.type = tarfile.LNKTYPE
                    info.linkname = target
                elif kind == 'symlink':
                    info.type = tarfile.SYMTYPE
                    info.linkname = target
                tar.addfile(info, io.BytesIO(data) if kind == 'file' else None)
                row = {'path': name, 'kind': kind, 'bytes': len(data),
                       'sha256': hashlib.sha256(data).hexdigest(), 'mode': info.mode}
                if target:
                    row['target'] = target
                rows.append(row)
        sha = hashlib.sha256(archive.read_bytes()).hexdigest()
        manifest = root / 'fixture.manifest.json'
        manifest.write_text(json.dumps({'format': 'uav-project-h10-private-supplement',
            'version': 1, 'archiveSHA256': sha, 'archiveBytes': archive.stat().st_size, 'files': rows}))
        return archive, sha, manifest

    def test_positive_regular_hardlink_and_relative_symlink_no_extract(self):
        with self.temporary() as root:
            data = b'synthetic-source'
            a, sha, m = self.fixture(root, [('aeris/a.py', data, 'file', None),
                ('aeris/b.py', data, 'hardlink', 'aeris/a.py'),
                ('aeris/c.py', b'a.py', 'symlink', 'a.py')])
            result = v.verify(a, sha, m)
            self.assertEqual(result['files'], 3)
            self.assertFalse(result['extracted'])
            self.assertFalse((Path(root) / 'aeris').exists())

    def test_bad_external_sha_and_manifest_content_refused(self):
        with self.temporary() as root:
            a, sha, m = self.fixture(root)
            with self.assertRaisesRegex(ValueError, 'EXTERNAL_ARCHIVE_SHA_MISMATCH'):
                v.verify(a, '0' * 64, m)
            value = json.loads(m.read_text())
            value['files'][0]['sha256'] = '0' * 64
            m.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'FILE_SHA_OR_SIZE'):
                v.verify(a, sha, m)

    def test_escape_duplicate_and_forward_hardlink_refused(self):
        cases = [([('../escape', b'x', 'file', None)], 'NONCANONICAL_PATH'),
            ([('aeris/a', b'x', 'file', None), ('aeris/A', b'x', 'file', None)], 'MANIFEST_DUPLICATE_PATH'),
            ([('aeris/b', b'x', 'hardlink', 'aeris/a')], 'HARDLINK_REQUIRES_PRIOR_REGULAR'),
            ([('aeris/link', b'../../escape', 'symlink', '../../escape')], 'SYMLINK_ESCAPE')]
        for members, error in cases:
            with self.subTest(error=error), self.temporary() as root:
                a, sha, m = self.fixture(root, members)
                with self.assertRaisesRegex(ValueError, error):
                    v.verify(a, sha, m)

    def test_truncated_gzip_and_expansion_limit_refused(self):
        with self.temporary() as root:
            a, sha, m = self.fixture(root)
            held = a.read_bytes()
            a.write_bytes(held[:-5])
            new_sha = hashlib.sha256(a.read_bytes()).hexdigest()
            value = json.loads(m.read_text())
            value.update(archiveSHA256=new_sha, archiveBytes=a.stat().st_size)
            m.write_text(json.dumps(value))
            with self.assertRaises((EOFError, OSError, tarfile.TarError)):
                v.verify(a, new_sha, m)
            a.write_bytes(held)
            value.update(archiveSHA256=sha, archiveBytes=len(held))
            m.write_text(json.dumps(value))
            old = v.MAX_EXPANDED
            try:
                v.MAX_EXPANDED = 512
                with self.assertRaisesRegex(ValueError, 'EXPANDED_LIMIT'):
                    v.verify(a, sha, m)
            finally:
                v.MAX_EXPANDED = old

    def test_non_directory_ancestor_conflicts_both_orders(self):
        cases = [([('aeris/a', b'x', 'file', None), ('aeris/a/b', b'x', 'file', None)],
                  'NON_DIRECTORY_ANCESTOR'),
                 ([('aeris/a/b', b'x', 'file', None), ('aeris/d/b', b'x', 'file', None),
                   ('aeris/a', b'd', 'symlink', 'd')], 'NON_DIRECTORY_REPLACES_ANCESTOR')]
        for members, error in cases:
            with self.subTest(error=error), self.temporary() as root:
                a, sha, m = self.fixture(root, members)
                with self.assertRaisesRegex(ValueError, error):
                    v.verify(a, sha, m)

    def test_hardlink_conflicting_inode_mode_refused(self):
        with self.temporary() as root:
            a, sha, m = self.fixture(root, [('aeris/a', b'x', 'file', None),
                ('aeris/b', b'x', 'hardlink', 'aeris/a')])
            # Keep the archive and manifest mutually consistent; the contradiction
            # is that two names for one inode declare different permission modes.
            data = a.read_bytes()
            with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as source:
                members = source.getmembers()
                members[0].mode = 0o444
                with tarfile.open(a, 'w:gz', format=tarfile.USTAR_FORMAT) as target:
                    target.addfile(members[0], io.BytesIO(b'x'))
                    target.addfile(members[1])
            value = json.loads(m.read_text())
            sha = hashlib.sha256(a.read_bytes()).hexdigest()
            value.update(archiveSHA256=sha, archiveBytes=a.stat().st_size)
            value['files'][0]['mode'] = 0o444
            m.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, 'HARDLINK_INODE_MODE_MISMATCH'):
                v.verify(a, sha, m)


if __name__ == '__main__':
    unittest.main()
