#!/usr/bin/env python3
"""Finite receiver layout preparation. Never launches a runtime, SDK or actor."""
import argparse
import hashlib
import io
import json
import os
import platform
from pathlib import Path, PurePosixPath
import shutil
import stat
import struct
import subprocess
import sys

GIB = 1 << 30
FLOOR, RESERVE, PREP_CAP, ARTIFACT_CAP = 10*GIB, 256*(1 << 20), 64*(1 << 20), 8*(1 << 20)
SELECTED = 'afe0878d1b98751f66c657c8eed6653d28d59778c46de012b2a16e8a8ef43395'
SPEC_SHA = '047fa4fa91f4e33bf8ea453ef419044e472bde31b7d8c541b17da9fd5a435172'
R08_SHA = '90d42c8165eec20365495d71bbff92857e4a8a443e3dc7bfd80114e148f81ce8'
IMAGE = 'sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84'
ARTIFACTS = tuple('evidence/'+x+'/candidates' for x in ('runtime-transport15', 'runtime-transport15-atomic-prep', 'betasim-integrated01', 'hosthealth-ipc10', 'hostdiag11', 'vidlife12'))
SOURCE_ROOTS = ('aeris_runtime', 'native/mission-runtime', 'native/betasim-integrated01', 'native/betasim-application09')
SPEC = 'evidence/runtime-observe04/emulator-spec.json'
ALIAS = 'planning/vidlife12/receiver-spec03.json'
HOST = 'planning/vidlife12/receiver-host-profile03.json'
LAYOUT = 'planning/vidlife12/receiver-layout03.json'
RECEIPT = 'evidence/vidlife12/reports/PREPARATION-RECEIPT03.json'
R08 = 'evidence/betasim-integrated01/r08/avd-baseline.json'
TASK = Path(__file__).resolve().parents[1]
CONFIG_TEMPLATE = TASK/'reference/AVD-config-original.ini'


def need(ok, code):
    if not ok:
        raise ValueError(code)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def relative(name):
    need(isinstance(name, str) and name and str(PurePosixPath(name)) == name and not PurePosixPath(name).is_absolute() and all(z not in ('', '.', '..') for z in name.split('/')), 'UNSAFE_RELATIVE_PATH')
    return name


def no_alias(path):
    path = Path(path).absolute()
    need(not any(p.is_symlink() for p in (path, *path.parents)), 'SYMLINK_REFUSED')
    return path


def stamp(st):
    return [st.st_dev, st.st_ino, st.st_nlink, st.st_mtime_ns, st.st_ctime_ns, st.st_blocks*512]


def file_row(path, name, limit=64 << 20):
    no_alias(path)
    need(stat.S_ISREG(path.lstat().st_mode), 'NOT_REGULAR')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode), 'NOT_REGULAR')
        need(0 <= before.st_size <= limit, 'INPUT_SIZE_CAP')
        digest = hashlib.sha256()
        total = 0
        while chunk := stream.read(1 << 20):
            total += len(chunk)
            need(total <= before.st_size and total <= limit, 'INPUT_GREW_DURING_READ')
            digest.update(chunk)
        need(total == before.st_size, 'INPUT_TRUNCATED_DURING_READ')
        need(stamp(before) == stamp(os.fstat(stream.fileno())), 'INPUT_CHANGED_DURING_READ')
    return {'path': relative(name), 'sha256': digest.hexdigest(), 'bytes': before.st_size, 'mode': stat.S_IMODE(before.st_mode), 'origin': stamp(before)}


def walk(root, rel):
    start = no_alias(root/relative(rel))
    need(start.is_dir(), 'MISSING_REQUIRED_DIRECTORY')
    files, dirs = [], []
    entries = logical = 0
    for parent, dn, fn in os.walk(start, followlinks=False):
        p = Path(parent)
        no_alias(p)
        dirs.append({'path': p.relative_to(root).as_posix(), 'mode': stat.S_IMODE(p.stat().st_mode)})
        entries += len(dn)+len(fn)
        need(entries <= 4096, 'FIXED_ROOT_ENTRY_CAP')
        for name in sorted(dn+fn):
            no_alias(p/name)
        for name in sorted(fn):
            logical += (p/name).lstat().st_size
            need(logical <= 128 << 20, 'FIXED_ROOT_LOGICAL_CAP')
            files.append(file_row(p/name, (p/name).relative_to(root).as_posix()))
    return files, dirs


def derive(root, contractor):
    """Independent closure derivation; contractor rows are a second exact witness."""
    root = no_alias(root)
    candidate = root/ARTIFACTS[-1]/SELECTED
    data = json_read(candidate/'candidate.json')
    need(sha(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()) == SELECTED, 'CANDIDATE_DIGEST')
    pins = {}
    for key in ('productSourceSHA256', 'externalFrozenSHA256'):
        for name, digest in data[key].items():
            need(name not in pins or pins[name] == digest, 'CONFLICTING_INPUT_PIN')
            pins[relative(name)] = digest
    for name, digest in data['native']['sourcePins'].items():
        need(name not in pins or pins[name] == digest, 'CONFLICTING_NATIVE_PIN')
        pins[relative(name)] = digest
    roles = json_read(candidate/'source/aeris_runtime/assets/input-roles10.json')['rows']
    need(len(roles) == 152, 'ROLE_COUNT')
    for row in roles:
        need(row['path'] not in pins or pins[row['path']] == row['sha256'], 'ROLE_PIN_CONFLICT')
        pins[relative(row['path'])] = row['sha256']
    rows, dirs = {}, {}
    for rel in ARTIFACTS+SOURCE_ROOTS:
        fs, ds = walk(root, rel)
        rows.update((r['path'], r) for r in fs)
        dirs.update((r['path'], r) for r in ds)
    for name, digest in pins.items():
        row = rows.get(name) or file_row(root/name, name)
        need(row['sha256'] == digest, 'PIN_MISMATCH:'+name)
        rows[name] = row
    wanted = {z['path']: {k: z[k] for k in ('path', 'bytes', 'mode', 'sha256')} for z in contractor['requirements']}
    actual = {k: {f: v[f] for f in ('path', 'bytes', 'mode', 'sha256')} for k, v in rows.items()}
    need(len(wanted) == contractor['fileCount'] == 2628 and actual == wanted, 'CONTRACTOR_FILE_SET_OR_CONTENT')
    # Parent directories omitted by closure tables are also finite declared directories.
    for name in rows:
        for parent in PurePosixPath(name).parents:
            if str(parent) != '.':
                rel = str(parent)
                no_alias(root/rel)
                dirs.setdefault(rel, {'path': rel, 'mode': stat.S_IMODE((root/rel).stat().st_mode)})
    return sorted(rows.values(), key=lambda z: z['path']), sorted(dirs.values(), key=lambda z: z['path'])


def host_profile(root, sdk, avd, adb, android_user_home, image_id):
    spec_bytes = read_bounded(no_alias(root)/SPEC, 65536)
    need(sha(spec_bytes) == SPEC_SHA, 'ORIGINAL_SPEC_HASH')
    spec = json.loads(spec_bytes)
    need(all(Path(p).is_absolute() for p in (sdk, avd, adb, android_user_home)), 'PROFILE_ABSOLUTE_PATH_REQUIRED')
    sdk, avd, adb, android_user_home = map(no_alias, (sdk, avd, adb, android_user_home))
    need(all(p.is_absolute() for p in (sdk, avd, adb, android_user_home)), 'PROFILE_ABSOLUTE_PATH_REQUIRED')
    need(sdk.is_dir() and avd.is_dir() and android_user_home.is_dir(), 'PROFILE_DIRECTORY_REQUIRED')
    effective = json.loads(spec_bytes)
    effective.update(SDK=str(sdk), AVD=str(avd), ADB=str(adb), ANDROID_USER_HOME=str(android_user_home))
    effective['argv'][0] = str(sdk/'emulator/emulator')
    for key, row in effective['prerequisites'].items():
        row['path'] = str(adb) if key == 'adb' else str(sdk/Path(spec['prerequisites'][key]['path']).relative_to(spec['SDK']))
    need(platform.system() == 'Darwin' and platform.machine() == 'arm64' and sys.implementation.name == 'cpython' and sys.version_info[:2] == (3, 14), 'HOST_ABI_UNSUPPORTED')
    need(image_id == IMAGE, 'IMAGE_ID_MISMATCH')
    prereqs = {}
    for key, row in effective['prerequisites'].items():
        got = file_row(Path(row['path']), key, 8*GIB if key == 'systemImage' else 64 << 20)
        need(got['sha256'] == row['sha256'], 'HOST_PREREQUISITE_HASH:'+key)
        prereqs[key] = {'path': row['path'], 'sha256': got['sha256'], 'bytes': got['bytes']}
    config_path = avd/'config.ini'
    config = file_row(config_path, 'config.ini', 4096)
    template = read_bounded(no_alias(CONFIG_TEMPLATE), 4096)
    need(sha(template) == spec['AVDConfigSHA256'], 'BASELINE_AVD_CONFIG_HASH')
    old = ('image.sysdir.1 = '+spec['SDK']+'/system-images/android-33/default/arm64-v8a').encode()
    new = ('image.sysdir.1 = '+str(sdk)+'/system-images/android-33/default/arm64-v8a').encode()
    need(template.count(old) == 1, 'BASELINE_SINGLE_IMAGE_PATH_REQUIRED')
    expected_config = template.replace(old, new, 1)
    need(read_bounded(config_path, 4096) == expected_config, 'AVD_CONFIG_NOT_EXACT_PATH_RELOCATION')
    effective['AVDConfigSHA256'] = config['sha256']
    need(avd.parent == android_user_home/'avd' and avd.name == 'aeris-beta-m1.avd', 'AVD_DISCOVERY_ROOT_MISMATCH')
    index_path = avd.parent/'aeris-beta-m1.ini'
    index_row = file_row(index_path, 'aeris-beta-m1.ini', 4096)
    need(index_row['bytes'] <= 4096, 'AVD_INDEX_BOUNDED')
    entries = {}
    for line in index_path.read_text(encoding='utf-8').splitlines():
        if not line:
            continue
        need('=' in line, 'AVD_INDEX_FORMAT')
        key, value = line.split('=', 1)
        need(key not in entries, 'AVD_INDEX_DUPLICATE')
        entries[key] = value
    need(entries == {'avd.ini.encoding': 'UTF-8', 'path': str(avd), 'target': 'android-33'}, 'AVD_INDEX_ROUTE_OR_KEYS')
    effective['prerequisites']['avdIndex'] = {'path': str(index_path), 'sha256': index_row['sha256']}
    prereqs['avdIndex'] = {'path': str(index_path), 'sha256': index_row['sha256'], 'bytes': index_row['bytes']}
    kernel = root/'pilot/betaintegrated01/runtime/_sim32_kernel.cpython-314-darwin.so'
    no_alias(kernel)
    need(stat.S_ISREG(kernel.lstat().st_mode), 'NATIVE_KERNEL_REGULAR')
    with kernel.open('rb') as stream:
        header = stream.read(8)
    need(len(header) == 8 and struct.unpack('<II', header) == (0xfeedfacf, 0x100000c), 'NATIVE_KERNEL_ABI')
    node = shutil.which('node')
    need(node is not None, 'NODE_REQUIRED')
    version = subprocess.run([node, '--version'], check=True, capture_output=True, text=True, timeout=5).stdout.strip()
    need(version.startswith('v24.'), 'NODE_ABI_UNSUPPORTED')
    return {'format': 'receiver-runtime03-host-profile', 'baselineSpecSHA256': SPEC_SHA, 'effectiveSpec': effective, 'effectiveSpecSHA256': sha(encoded(effective)), 'SDK': str(sdk), 'AVD': str(avd), 'ADB': str(adb), 'ANDROID_USER_HOME': str(android_user_home), 'prerequisites': prereqs, 'baselineConfigSHA256': spec['AVDConfigSHA256'], 'actualConfigSHA256': config['sha256'], 'configPolicy': 'PATH_RELOCATION_ONLY_NO_DEVICE_POLICY_CHANGE', 'python': str(Path(sys.executable).resolve()), 'pythonVersion': platform.python_version(), 'pythonABI': 'cpython-314-darwin-arm64', 'node': str(Path(node).resolve()), 'nodeVersion': version, 'cachedImageDeclaredID': image_id, 'cachedImageLiveVerification': 'NOT_CHECKED_BY_PREPARATION_OR_PROFILE; ORIGINAL_ADMISSION_REQUIRED', 'SDKOwnership': 'EXPLICIT_SHARED_READ_ONLY_HOST_CACHE', 'AVDOwnership': 'RETAINED_ORIGINAL_STATE; EXCLUSIVE_ORIGINAL_RUNTIME_OWNER_REQUIRED; NO_COPY_OR_RESET', 'profileSourceWorkspace': str(root)}


def history(root):
    fs, ds = walk(root, 'evidence/vidlife12')
    return [r for r in fs if not r['path'].startswith(ARTIFACTS[-1]+'/')], [r for r in ds if not r['path'].startswith(ARTIFACTS[-1])]


def artifact_group(row):
    return tuple(row['origin'][:2]) if any(row['path'].startswith(p+'/') for p in ARTIFACTS) else ('source', row['path'])


def allocation(rows, dirs, extra_bytes):
    seen = set()
    total = 0
    for r in rows:
        key = artifact_group(r)
        if key not in seen:
            total += ((r['bytes']+4095)//4096)*4096
            seen.add(key)
    # Fileceil plus directory allocation envelope and bounded generated records.
    return total + (len(dirs)+32)*4096 + extra_bytes


def disk_gate(parent, forecast, free=None):
    need(0 < forecast <= PREP_CAP, 'PREPARATION_FORECAST_CAP')
    available = shutil.disk_usage(parent).free if free is None else free
    need(available >= FLOOR+RESERVE+forecast, 'PREPARATION_DISK_ADMISSION')
    return available


def make_plan(contract, contractor, profile):
    root, dst = no_alias(contract['sourceWorkspace']), no_alias(contract['managedRuntimeDestination'])
    need(not dst.exists() and root != dst and root not in dst.parents and dst not in root.parents, 'DESTINATION_EXISTS_OR_OVERLAPS')
    need(not any((p/'.git').exists() for p in (dst, *dst.parents)), 'DESTINATION_IN_GIT')
    need(contract['selectedCandidate'] == SELECTED and contract['futureNewCampaignSlot'] == 's02' and contract['maxActualSeconds'] == 180, 'CONTRACT_POLICY')
    rows, dirs = derive(root, contractor)
    artifact_allocations = {tuple(r['origin'][:2]): r['origin'][-1] for r in rows if any(r['path'].startswith(a+'/') for a in ARTIFACTS)}
    for d in dirs:
        if any(d['path'] == a or d['path'].startswith(a+'/') for a in ARTIFACTS):
            st = (root/d['path']).stat()
            artifact_allocations[(st.st_dev, st.st_ino)] = st.st_blocks*512
    need(sum(artifact_allocations.values()) <= ARTIFACT_CAP, 'ORIGINAL_ARTIFACT_UNION_CAP')
    need(profile['profileSourceWorkspace'] == str(root) and profile['baselineSpecSHA256'] == SPEC_SHA and profile['effectiveSpecSHA256'] == sha(encoded(profile['effectiveSpec'])) and profile['cachedImageDeclaredID'] == IMAGE, 'PROFILE_BINDING')
    spec = file_row(root/SPEC, SPEC)
    need(spec['sha256'] == SPEC_SHA, 'SPEC_DRIFT')
    r08 = file_row(Path(contract['historyR08Supplement']), R08)
    need(r08['sha256'] == R08_SHA and r08['bytes'] == 2082, 'HISTORICAL_R08_PROVENANCE')
    retained, history_dirs = history(root)
    plan = {'format': 'receiver-runtime03-layout-v1', 'source': str(root), 'destination': str(dst), 'selectedCandidate': SELECTED, 'sourceArtifactAllocatedBytes': sum(artifact_allocations.values()), 'contractSHA256': sha(encoded(contract)), 'requirementsSHA256': sha(encoded(contractor)), 'profile': profile, 'files': rows, 'directories': dirs, 'specOrigin': spec, 'r08Source': contract['historyR08Supplement'], 'r08': r08, 'retainedHistory': retained, 'retainedHistoryAllocatedFileBytes': sum({tuple(r['origin'][:2]): r['origin'][-1] for r in retained}.values()), 'retainedHistoryDirectories': history_dirs, 'historyDisposition': 'SEALED_AT_ORIGINAL_PATHS_NOT_A_BACKUP_OR_AN_ACTIVE_CAMPAIGN', 'originalGuardPolicy': 'UNCHANGED; PREPARE_IS_NOT_FULL_ADMISSION', 'runtimeEnvironment': {'AERIS_REPOSITORY_ROOT': str(dst), 'AERIS_CANDIDATE_DIR': str(dst/ARTIFACTS[-1]/SELECTED)}, 'newSlot': 'evidence/vidlife12/s02', 'copiedSDKOrAVD': False}
    # 2 MiB bounded envelope covers this manifest/profile/receipt and additions, all charged.
    plan['forecastBytes'] = allocation(rows, dirs, (2 << 20)+r08['bytes']+spec['bytes'])
    need(len(encoded(plan))+len(encoded(profile))+65536 <= 2 << 20, 'GENERATED_METADATA_ENVELOPE')
    disk_gate(dst.parent, plan['forecastBytes'])
    return plan


def verify_origins(plan):
    root = no_alias(plan['source'])
    rows = plan['files']+[plan['specOrigin']]
    for row in rows:
        need(file_row(root/row['path'], row['path']) == row, 'ORIGIN_MUTATION:'+row['path'])
    need(history(root) == (plan['retainedHistory'], plan['retainedHistoryDirectories']), 'RETAINED_HISTORY_MUTATION')
    need(file_row(Path(plan['r08Source']), R08) == plan['r08'], 'R08_ORIGIN_MUTATION')
    for d in plan['directories']:
        p = no_alias(root/d['path'])
        need(p.is_dir() and stat.S_IMODE(p.stat().st_mode) == d['mode'], 'ORIGIN_DIRECTORY_MUTATION')


def recipe(plan):
    return {'format': 'receiver-runtime03-preparation-receipt', 'status': 'PREPARED_NOT_RUNTIME_ADMITTED', 'layoutSHA256': sha(encoded(plan)), 'selectedCandidate': SELECTED, 'sourceFiles': len(plan['files']), 'historyR08SHA256': R08_SHA, 'profileSHA256': sha(encoded(plan['profile'])), 'baselineSpecSHA256': SPEC_SHA, 'effectiveSpecSHA256': plan['profile']['effectiveSpecSHA256'], 'profileAlias': ALIAS, 'specGuardianPath': SPEC, 'historyRetainedAt': plan['source'], 'campaignSlotCreated': False, 'sourceCodeChanged': False, 'actorsStarted': False, 'freshBaselineOrCounterReset': False, 'artifactAndMetadataCapsChanged': False}


def generated(plan):
    spec = encoded(plan['profile']['effectiveSpec'])
    return {LAYOUT: (encoded(plan), 0o444), HOST: (encoded(plan['profile']), 0o444), SPEC: (spec, 0o444), ALIAS: (spec, 0o444), R08: (Path(plan['r08Source']).read_bytes(), 0o444), RECEIPT: (encoded(recipe(plan)), 0o444)}


def destination_contract(plan):
    files = {r['path']: {'sha256': r['sha256'], 'bytes': r['bytes'], 'mode': r['mode']} for r in plan['files']}
    need(not set(files).intersection(generated(plan)), 'GENERATED_PATH_COLLISION')
    for path, (data, mode) in generated(plan).items():
        files[path] = {'sha256': sha(data), 'bytes': len(data), 'mode': mode}
    dirs = {d['path']: d['mode'] for d in plan['directories']}
    for path in files:
        for parent in PurePosixPath(path).parents:
            if str(parent) != '.':
                dirs.setdefault(str(parent), 0o755)
    return files, dirs


def check(plan, spec_arg, pending_receipt=False):
    dst = no_alias(plan['destination'])
    need(Path(spec_arg).absolute() == dst/SPEC, 'SUPPLIED_SPEC_MUST_EQUAL_FIXED_GUARDIAN_PATH')
    expected, dirs = destination_contract(plan)
    if pending_receipt:
        expected.pop(RECEIPT)
    actual_files, actual_dirs = {}, {}
    for parent, dn, fn in os.walk(dst, followlinks=False):
        p = Path(parent)
        for n in dn+fn:
            no_alias(p/n)
        if p != dst:
            actual_dirs[p.relative_to(dst).as_posix()] = stat.S_IMODE(p.stat().st_mode)
        for n in fn:
            r = file_row(p/n, (p/n).relative_to(dst).as_posix())
            actual_files[r['path']] = {k: r[k] for k in ('sha256', 'bytes', 'mode')}
    need(actual_files == expected and actual_dirs == dirs, 'DESTINATION_FILE_SET_KIND_MODE_OR_CONTENT')
    group_targets, origins = {}, set()
    for row in plan['files']:
        st = (dst/row['path']).stat()
        inode = (st.st_dev, st.st_ino)
        need(inode != tuple(row['origin'][:2]), 'ORIGIN_INODE_ALIAS')
        key = artifact_group(row)
        if key in group_targets:
            need(group_targets[key] == inode, 'LOST_ARTIFACT_HARDLINK_GROUP')
        else:
            need(inode not in origins, 'UNDECLARED_HARDLINK_GROUP')
            group_targets[key] = inode
            origins.add(inode)
    need(os.path.samefile(dst/SPEC, dst/ALIAS), 'PROFILE_NOT_CHARGED_SAME_NEW_INODE')
    artifact_inodes = set()
    allocated = 0
    for base in ARTIFACTS:
        for p in [dst/base, *(dst/base).rglob('*')]:
            st = p.stat()
            key = (st.st_dev, st.st_ino)
            if key not in artifact_inodes:
                artifact_inodes.add(key)
                allocated += st.st_blocks*512
    need(allocated <= ARTIFACT_CAP, 'ORIGINAL_ARTIFACT_UNION_CAP')
    need(not (dst/plan['newSlot']).exists(), 'CAMPAIGN_SLOT_ALREADY_EXISTS')
    verify_origins(plan)
    return {'status': 'PREPARED_COMPONENT_CHECK_ONLY_NOT_FULL_ADMISSION', 'files': len(expected), 'artifactAllocatedBytes': allocated, 'artifactCapBytes': ARTIFACT_CAP, 'sameNewProfileInode': [(dst/SPEC).stat().st_dev, (dst/SPEC).stat().st_ino], 'sourcePreserved': True}


def durable_copy(source, target, mode, limit):
    total = 0
    with target.open('xb') as out:
        while chunk := source.read(1 << 20):
            total += len(chunk)
            need(total <= limit, 'COPY_INPUT_GREW')
            disk_gate(target.parent, ((len(chunk)+4095)//4096)*4096)
            out.write(chunk)
        need(total == limit, 'COPY_INPUT_TRUNCATED')
        os.fchmod(out.fileno(), mode)
        out.flush()
        os.fsync(out.fileno())


def prepare(plan, contract, contractor):
    # Re-derive before any mkdir: supplied plan cannot widen the exact closure.
    fresh = make_plan(contract, contractor, plan['profile'])
    need(fresh == plan, 'PLAN_OR_INPUT_MUTATION')
    verify_origins(plan)
    dst = no_alias(plan['destination'])
    disk_gate(dst.parent, plan['forecastBytes'])
    expected, dirs = destination_contract(plan)
    dst.mkdir(mode=0o755)
    for name in sorted(dirs, key=lambda z: (len(PurePosixPath(z).parts), z)):
        (dst/name).mkdir(mode=0o755)
    groups = {}
    for row in plan['files']:
        target = dst/row['path']
        key = artifact_group(row)
        if key in groups:
            disk_gate(dst.parent, 4096)
            os.link(groups[key], target)
        else:
            with (Path(plan['source'])/row['path']).open('rb') as src:
                durable_copy(src, target, row['mode'], row['bytes'])
            groups[key] = target
    for name, (data, mode) in generated(plan).items():
        if name == RECEIPT:
            continue
        if name == ALIAS:
            disk_gate(dst.parent, 4096)
            os.link(dst/SPEC, dst/ALIAS)
        else:
            durable_copy(io.BytesIO(data), dst/name, mode, len(data))
    for name in sorted(dirs, key=lambda z: -len(PurePosixPath(z).parts)):
        os.chmod(dst/name, dirs[name])
    check(plan, dst/SPEC, pending_receipt=True)
    # Commit marker is absent on any earlier copy/check/fsync failure. Partial
    # layout is retained, never automatically erased, retried or admitted.
    data = encoded(recipe(plan))
    pending = dst/(RECEIPT+'.pending')
    durable_copy(io.BytesIO(data), pending, 0o444, len(data))
    os.link(pending, dst/RECEIPT)  # No overwrite even if another writer raced.
    pending.unlink()             # Only our own committed temporary marker.
    return check(plan, dst/SPEC)


def read_bounded(path, limit):
    path = no_alias(path)
    need(stat.S_ISREG(path.lstat().st_mode) and path.stat().st_size <= limit, 'BOUNDED_REGULAR_INPUT')
    with path.open('rb') as stream:
        data = stream.read(limit+1)
    need(len(data) <= limit, 'INPUT_SIZE_CAP')
    return data


def json_read(path):
    return json.loads(read_bounded(Path(path), 2 << 20))


def save_new(path, value):
    with no_alias(path).open('xb') as stream:
        stream.write(encoded(value))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('profile')
    for name in ('root', 'sdk', 'avd', 'adb', 'android-user-home', 'image-id', 'out'):
        p.add_argument('--'+name, required=True)
    for command in ('plan', 'prepare', 'check'):
        p = sub.add_parser(command)
        p.add_argument('--contract', default=str(TASK/'CONTRACT.json'))
        p.add_argument('--requirements', default=str(TASK/'CONTRACTOR-REQUIREMENTS01.json'))
        p.add_argument('--profile' if command == 'plan' else '--plan', required=True)
        if command != 'check':
            p.add_argument('--out', required=True)
        else:
            p.add_argument('--spec', required=True)
    args = ap.parse_args()
    if args.command == 'profile':
        result = host_profile(Path(args.root), args.sdk, args.avd, args.adb, args.android_user_home, args.image_id)
    elif args.command == 'plan':
        result = make_plan(json_read(args.contract), json_read(args.requirements), json_read(args.profile))
    else:
        plan = json_read(args.plan)
        # Recheck real host pins/ABI on every prepare/check, never trust profile metadata alone.
        h = plan['profile']
        need(host_profile(Path(plan['source']), h['SDK'], h['AVD'], h['ADB'], h['ANDROID_USER_HOME'], h['cachedImageDeclaredID']) == h, 'CURRENT_HOST_PROFILE_DRIFT')
        result = prepare(plan, json_read(args.contract), json_read(args.requirements)) if args.command == 'prepare' else check(plan, args.spec)
    if hasattr(args, 'out'):
        save_new(args.out, result)
    count = result.get('files', 0)
    print(json.dumps({'command': args.command, 'status': result.get('status', 'PREPARATION_METADATA_CREATED_NOT_ADMITTED'), 'files': len(count) if isinstance(count, list) else count, 'forecastBytes': result.get('forecastBytes')}, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps({'status': 'REFUSED', 'error': str(error)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(1)
