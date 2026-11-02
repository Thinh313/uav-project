#!/usr/bin/env python3
"""Read-only bounded private supplement verification. Integrity is not identity or flight acceptance."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tarfile

MAX_ARCHIVE = 2 * 2**30
MAX_EXPANDED = 4 * 2**30
MAX_MEMBER = 256 * 2**20
MAX_COUNT = 30000


def require(value, reason):
    if not value:
        raise ValueError(reason)


def safe_path(value):
    require(isinstance(value, str) and value and '\\' not in value and '\x00' not in value,
            'UNSAFE_PATH')
    p = PurePosixPath(value)
    require(not p.is_absolute() and all(x not in ('', '.', '..') for x in value.split('/'))
            and str(p) == value, 'NONCANONICAL_PATH')
    return value


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'DUPLICATE_JSON_KEY')
        result[key] = value
    return result


class BoundedReader:
    def __init__(self, stream):
        self.stream = stream
        self.total = 0

    def read(self, size=-1):
        require(size >= 0, 'UNBOUNDED_READ')
        value = self.stream.read(size)
        self.total += len(value)
        require(self.total <= MAX_EXPANDED, 'EXPANDED_LIMIT')
        return value


class HashReader:
    def __init__(self, stream):
        self.stream = stream
        self.digest = hashlib.sha256()
        self.total = 0

    def read(self, size=-1):
        require(size >= 0, 'UNBOUNDED_COMPRESSED_READ')
        value = self.stream.read(size)
        self.digest.update(value)
        self.total += len(value)
        require(self.total <= MAX_ARCHIVE, 'ARCHIVE_LIMIT')
        return value


class BoundedTarInfo(tarfile.TarInfo):
    headers = 0

    def _proc_member(self, tar):
        type(self).headers += 1
        require(type(self).headers <= MAX_COUNT * 2, 'HEADER_COUNT')
        if self.type in (tarfile.XHDTYPE, tarfile.XGLTYPE, tarfile.GNUTYPE_LONGNAME, tarfile.GNUTYPE_LONGLINK):
            require(0 <= self.size <= 1024 * 1024, 'EXTENSION_HEADER_LIMIT')
        require(self.type != tarfile.GNUTYPE_SPARSE, 'SPARSE_UNSUPPORTED')
        return super()._proc_member(tar)


def verify(archive, expected_sha, manifest_file):
    require(re.fullmatch('[0-9a-fA-F]{64}', expected_sha or '') is not None, 'EXPECTED_SHA_REQUIRED')
    require(archive.is_file() and not archive.is_symlink(), 'ARCHIVE_REGULAR_FILE_REQUIRED')
    require(archive.stat().st_size <= MAX_ARCHIVE, 'ARCHIVE_LIMIT')
    digest = hashlib.sha256()
    with archive.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    require(digest.hexdigest() == expected_sha.lower(), 'EXTERNAL_ARCHIVE_SHA_MISMATCH')
    require(manifest_file.stat().st_size <= 32 * 2**20, 'MANIFEST_LIMIT')
    manifest = json.loads(manifest_file.read_bytes(), object_pairs_hook=strict_object)
    require(manifest.get('format') == 'uav-project-h10-private-supplement'
            and type(manifest.get('version')) is int and manifest['version'] == 1, 'MANIFEST_FORMAT')
    require(manifest.get('archiveSHA256') == digest.hexdigest()
            and type(manifest.get('archiveBytes')) is int
            and manifest['archiveBytes'] == archive.stat().st_size, 'MANIFEST_ARCHIVE_BINDING')
    rows = manifest.get('files')
    require(isinstance(rows, list) and len(rows) <= MAX_COUNT, 'MANIFEST_COUNT')
    expected, folded = {}, set()
    for row in rows:
        require(isinstance(row, dict), 'MANIFEST_ROW')
        name = safe_path(row.get('path'))
        require(name not in expected and name.casefold() not in folded, 'MANIFEST_DUPLICATE_PATH')
        require(row.get('kind') in ('file', 'hardlink', 'symlink'), 'MANIFEST_KIND')
        require(type(row.get('bytes')) is int and 0 <= row['bytes'] <= MAX_MEMBER, 'MANIFEST_MEMBER_SIZE')
        require(type(row.get('mode')) is int and 0 <= row['mode'] <= 0o7777, 'MANIFEST_MODE')
        require(re.fullmatch('[0-9a-f]{64}', row.get('sha256', '')) is not None, 'MANIFEST_SHA')
        expected[name] = row
        folded.add(name.casefold())
    seen, seen_folded, regular, symlinks = {}, set(), {}, set()
    node_kinds = {}
    count = 0
    BoundedTarInfo.headers = 0
    with archive.open('rb') as compressed:
      hashed_compressed = HashReader(compressed)
      with gzip.GzipFile(fileobj=hashed_compressed, mode='rb') as gz:
        bounded = BoundedReader(gz)
        # 512-byte buffering makes the remainder check include the second zero block.
        with tarfile.open(fileobj=bounded, mode='r|', bufsize=512, tarinfo=BoundedTarInfo) as tar:
            for member in tar:
                count += 1
                require(count <= MAX_COUNT, 'MEMBER_COUNT')
                name = safe_path(member.name.rstrip('/') if member.isdir() else member.name)
                require(name not in seen and name.casefold() not in seen_folded, 'ARCHIVE_DUPLICATE_PATH')
                for parent in PurePosixPath(name).parents:
                    parent_kind = node_kinds.get(str(parent).casefold())
                    require(parent_kind is None or parent_kind == 'directory', 'NON_DIRECTORY_ANCESTOR')
                require(member.isdir() or not any(previous.startswith(name.casefold() + '/')
                        for previous in node_kinds), 'NON_DIRECTORY_REPLACES_ANCESTOR')
                seen_folded.add(name.casefold())
                seen[name] = 'directory' if member.isdir() else 'member'
                node_kinds[name.casefold()] = 'directory' if member.isdir() else 'member'
                if member.isdir():
                    require(member.size == 0, 'DIRECTORY_PAYLOAD')
                    continue
                require(not member.sparse, 'PAX_SPARSE_UNSUPPORTED')
                require(name in expected, 'UNLISTED_MEMBER')
                row = expected[name]
                require((member.mode & 0o7777) == row['mode'], 'MODE_MISMATCH')
                require(0 <= member.size <= MAX_MEMBER, 'MEMBER_LIMIT')
                if member.isfile():
                    require(row['kind'] == 'file' and member.size == row['bytes'], 'FILE_KIND_OR_SIZE')
                    hashed = hashlib.sha256()
                    payload = tar.extractfile(member)
                    size = 0
                    while True:
                        chunk = payload.read(1024 * 1024)
                        if not chunk:
                            break
                        size += len(chunk)
                        hashed.update(chunk)
                    require(size == row['bytes'] and hashed.hexdigest() == row['sha256'], 'FILE_SHA_OR_SIZE')
                    regular[name] = row
                elif member.islnk():
                    target = safe_path(member.linkname)
                    require(row['kind'] == 'hardlink' and row.get('target') == target and member.size == 0,
                            'HARDLINK_DESCRIPTOR')
                    require(target in regular, 'HARDLINK_REQUIRES_PRIOR_REGULAR')
                    require((row['bytes'], row['sha256']) == (regular[target]['bytes'], regular[target]['sha256']),
                            'HARDLINK_CONTENT_MISMATCH')
                    require(row['mode'] == regular[target]['mode'], 'HARDLINK_INODE_MODE_MISMATCH')
                elif member.issym():
                    target = member.linkname
                    require(isinstance(target, str) and target and '\\' not in target
                            and not target.startswith('/') and '\x00' not in target, 'SYMLINK_TARGET')
                    parts = list(PurePosixPath(name).parent.parts)
                    for part in target.split('/'):
                        if part == '..':
                            require(parts, 'SYMLINK_ESCAPE')
                            parts.pop()
                        elif part not in ('', '.'):
                            parts.append(part)
                    value = target.encode('utf8')
                    require(row['kind'] == 'symlink' and row.get('target') == target and member.size == 0
                            and row['bytes'] == len(value) and row['sha256'] == hashlib.sha256(value).hexdigest(),
                            'SYMLINK_DESCRIPTOR')
                    symlinks.add(name)
                else:
                    raise ValueError('UNSUPPORTED_TAR_KIND')
        # Verify tar end padding and consume gzip footer/CRC; reject appended nonzero bytes.
        tail = 0
        while True:
            chunk = bounded.read(1024 * 1024)
            if not chunk:
                break
            require(not any(chunk), 'NONZERO_TAR_TRAILER')
            tail += len(chunk)
        require(tail >= 512 and bounded.total % 512 == 0, 'MISSING_TAR_END_BLOCKS')
      require(hashed_compressed.digest.hexdigest() == expected_sha.lower()
              and hashed_compressed.total == manifest['archiveBytes'], 'ARCHIVE_CHANGED_DURING_VERIFICATION')
    actual = {name for name, kind in seen.items() if kind == 'member'}
    require(actual == set(expected), 'MISSING_MANIFEST_MEMBERS')
    return {'status': 'PASS_INTEGRITY_ONLY', 'archiveSHA256': digest.hexdigest(),
            'archiveBytes': archive.stat().st_size, 'expandedBytes': bounded.total,
            'files': len(actual), 'members': count, 'extracted': False,
            'identityAuthenticated': False, 'flightAcceptance': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--sha256', required=True, help='Expected archive SHA from an independent channel')
    parser.add_argument('--manifest', required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.archive, args.sha256, args.manifest), indent=2))
    except (ValueError, OSError, EOFError, tarfile.TarError, json.JSONDecodeError) as error:
        parser.exit(1, 'FAIL_INTEGRITY: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
