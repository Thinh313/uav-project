"""Tiny generated fixtures only; mocks replace host/closure inputs, never production guards."""
import copy
import contextlib
import io
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1]/'tools/runtime_layout.py'
spec = importlib.util.spec_from_file_location('runtime_layout03', MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class LayoutTests(unittest.TestCase):
    def setUp(self):
        parent = os.environ.get('HANDOFF_TEST_ROOT')
        self.tmp = Path(tempfile.mkdtemp(prefix='codex-tmp-receiver-runtime03-20261031-', dir=parent)).resolve()
        self.addCleanup(self.cleanup)
        self.src, self.dst = self.tmp/'origin', self.tmp/'managed'
        self.src.mkdir()
        self.rows, self.dirs = [], {}
        for i, base in enumerate(m.ARTIFACTS):
            self.put(self.src/base/'held.bin', b'held-'+str(i).encode(), 0o444)
        os.link(self.src/m.ARTIFACTS[0]/'held.bin', self.src/m.ARTIFACTS[1]/'alias.bin')
        for base in m.SOURCE_ROOTS:
            self.put(self.src/base/'source.py', b'# source\n', 0o644)
        self.put(self.src/'evidence/vidlife12/git/history.json', b'{"history":true}', 0o444)
        self.put(self.src/m.SPEC, b'{"fixture":"spec"}', 0o644)
        self.r08 = self.tmp/'historical.json'
        self.put(self.r08, b'R08 historical', 0o444)
        for rel in m.ARTIFACTS+m.SOURCE_ROOTS:
            fs, ds = m.walk(self.src, rel)
            self.rows.extend(fs)
            self.dirs.update((d['path'], d) for d in ds)
        for r in self.rows:
            for p in Path(r['path']).parents:
                if str(p) != '.':
                    self.dirs.setdefault(str(p), {'path': str(p), 'mode': 0o755})
        self.plan = {'format': 'fixture', 'source': str(self.src), 'destination': str(self.dst), 'selectedCandidate': m.SELECTED, 'files': sorted(self.rows, key=lambda r:r['path']), 'directories': sorted(self.dirs.values(), key=lambda r:r['path']), 'specOrigin': m.file_row(self.src/m.SPEC,m.SPEC), 'r08Source': str(self.r08), 'r08': m.file_row(self.r08,m.R08), 'retainedHistory':m.history(self.src)[0], 'retainedHistoryDirectories':m.history(self.src)[1], 'profile': {'fixture': True, 'effectiveSpec': {'fixture':'effective'}, 'effectiveSpecSHA256': m.sha(m.encoded({'fixture':'effective'}))}, 'newSlot': 'evidence/vidlife12/s02', 'forecastBytes': 4 << 20}

    def cleanup(self):
        # Registered before setUp work, including failed setUp paths.
        if not self.tmp.exists():
            return
        # Readonly fixtures are intentionally retained until test completion only.
        for p, ds, fs in os.walk(self.tmp):
            os.chmod(p, 0o755)
        shutil.rmtree(self.tmp)

    @staticmethod
    def put(path, data, mode=0o644):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(mode)

    def materialize(self):
        with patch.object(m, 'make_plan', return_value=self.plan), patch.object(m.shutil, 'disk_usage', return_value=type('D',(),{'free':100*m.GIB})()):
            return m.prepare(self.plan, {}, {})

    def test_prepare_preserves_independent_origin_and_internal_links(self):
        before = [m.file_row(self.src/r['path'],r['path']) for r in self.rows]
        result = self.materialize()
        self.assertTrue(result['sourcePreserved'])
        self.assertLessEqual(result['artifactAllocatedBytes'], m.ARTIFACT_CAP)
        a, b = self.dst/m.ARTIFACTS[0]/'held.bin', self.dst/m.ARTIFACTS[1]/'alias.bin'
        self.assertTrue(os.path.samefile(a,b))
        self.assertFalse(os.path.samefile(a,self.src/m.ARTIFACTS[0]/'held.bin'))
        self.assertTrue(os.path.samefile(self.dst/m.SPEC,self.dst/m.ALIAS))
        self.assertFalse((self.dst/'evidence/vidlife12/git').exists())
        self.assertFalse((self.dst/self.plan['newSlot']).exists())
        self.assertEqual(before,[m.file_row(self.src/r['path'],r['path']) for r in self.rows])

    def test_unknown_missing_mutation_mode_and_symlink_refused(self):
        self.materialize()
        source = self.dst/'aeris_runtime/source.py'
        cases = [lambda:self.put(self.dst/'unknown',b'x'), lambda:source.unlink(), lambda:source.write_bytes(b'changed'), lambda:source.chmod(0o600), lambda:(source.unlink(),source.symlink_to(self.src/'aeris_runtime/source.py'))]
        for mutate in cases:
            with self.subTest(mutate=mutate):
                # Restore via fixture expected bytes/modes; never an actual runtime.
                extra=self.dst/'unknown'
                if extra.exists():extra.unlink()
                if source.exists() or source.is_symlink():source.unlink()
                self.put(source,b'# source\n',0o644)
                mutate()
                with self.assertRaises((ValueError,FileNotFoundError)):
                    m.check(self.plan,self.dst/m.SPEC)

    def test_profile_argument_alias_refused(self):
        self.materialize()
        with self.assertRaisesRegex(ValueError,'FIXED_GUARDIAN'):
            m.check(self.plan,self.dst/m.ALIAS)

    def test_profile_must_share_new_inode(self):
        self.materialize()
        alias=self.dst/m.ALIAS
        alias.unlink();self.put(alias,(self.dst/m.SPEC).read_bytes(),0o444)
        with self.assertRaisesRegex(ValueError,'SAME_NEW_INODE'):
            m.check(self.plan,self.dst/m.SPEC)

    def test_after_plan_source_and_history_changes_refused_before_copy(self):
        for target in [self.src/'aeris_runtime/source.py',self.src/'evidence/vidlife12/git/history.json',self.r08]:
            with self.subTest(target=target):
                data=target.read_bytes(); mode=stat.S_IMODE(target.stat().st_mode)
                target.chmod(0o644);target.write_bytes(b'mutation')
                with self.assertRaises(ValueError):self.materialize()
                self.assertFalse(self.dst.exists())
                target.write_bytes(data);target.chmod(mode)
                # Only fixture snapshot can be refreshed for the next independent case.
                for row in self.plan['files']:
                    row.update(m.file_row(self.src/row['path'],row['path']))
                self.plan['retainedHistory'],self.plan['retainedHistoryDirectories']=m.history(self.src)
                self.plan['r08']=m.file_row(self.r08,m.R08)

    def test_disk_floor_reserve_positive_forecast_and_cap(self):
        for forecast, free in [(0,100*m.GIB), (m.PREP_CAP+1,100*m.GIB), (1,m.FLOOR+m.RESERVE), (m.PREP_CAP,m.FLOOR+m.RESERVE+m.PREP_CAP-1)]:
            with self.subTest(forecast=forecast,free=free),self.assertRaises(ValueError):m.disk_gate(self.tmp,forecast,free)
        self.assertEqual(m.disk_gate(self.tmp,m.PREP_CAP,m.FLOOR+m.RESERVE+m.PREP_CAP),m.FLOOR+m.RESERVE+m.PREP_CAP)

    def test_artifact_cap_not_reset(self):
        self.materialize()
        with patch.object(m,'ARTIFACT_CAP',1),self.assertRaisesRegex(ValueError,'ARTIFACT_UNION_CAP'):
            m.check(self.plan,self.dst/m.SPEC)

    def test_existing_slot_refused_and_existing_destination_not_overwritten(self):
        self.materialize()
        (self.dst/self.plan['newSlot']).mkdir()
        with self.assertRaises(ValueError):m.check(self.plan,self.dst/m.SPEC)
        before=(self.dst/m.LAYOUT).read_bytes()
        with self.assertRaises(FileExistsError):self.materialize()
        self.assertEqual(before,(self.dst/m.LAYOUT).read_bytes())

    def test_unsafe_paths_and_fifo_and_parent_symlink(self):
        for name in ('../x','/x','a/../x','a//x','./x',''):
            with self.assertRaises(ValueError):m.relative(name)
        fifo=self.tmp/'fifo';os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError,'NOT_REGULAR'):m.file_row(fifo,'fifo')
        alias=self.tmp/'outside';alias.symlink_to(self.src,target_is_directory=True)
        with self.assertRaises(ValueError):m.file_row(alias/'aeris_runtime/source.py','x')

    def test_unexpected_shared_source_inode_refused(self):
        self.materialize()
        a=self.dst/'aeris_runtime/source.py';b=self.dst/'native/mission-runtime/source.py'
        b.unlink();os.link(a,b)
        with self.assertRaisesRegex(ValueError,'UNDECLARED_HARDLINK'):
            m.check(self.plan,self.dst/m.SPEC)

    def test_directory_mode_mutation(self):
        self.materialize();(self.dst/'aeris_runtime').chmod(0o700)
        with self.assertRaisesRegex(ValueError,'KIND_MODE_OR_CONTENT'):m.check(self.plan,self.dst/m.SPEC)

    def test_copy_fsync_and_check_faults_never_commit_receipt(self):
        for boundary in ('fsync', 'check', 'disk'):
            with self.subTest(boundary=boundary):
                if self.dst.exists():
                    for p, ds, fs in os.walk(self.dst):os.chmod(p,0o755)
                    shutil.rmtree(self.dst)
                if boundary == 'fsync':
                    context=patch.object(m.os,'fsync',side_effect=OSError('injected fsync'))
                elif boundary == 'check':
                    context=patch.object(m,'check',side_effect=ValueError('injected exact check'))
                else:
                    original=m.disk_gate; calls=[0]
                    def dropping(parent,forecast,free=None):
                        calls[0]+=1
                        if calls[0]>1:raise ValueError('injected low disk before chunk')
                        return original(parent,forecast,100*m.GIB)
                    context=patch.object(m,'disk_gate',side_effect=dropping)
                with context,self.assertRaises((OSError,ValueError)):self.materialize()
                self.assertTrue(self.dst.exists())
                self.assertFalse((self.dst/m.RECEIPT).exists())
                m.verify_origins(self.plan)

    def test_pre_hash_and_json_and_walk_bounds(self):
        large=self.tmp/'sparse'
        with large.open('wb') as f:f.truncate((64 << 20)+1)
        with self.assertRaisesRegex(ValueError,'SIZE_CAP'):m.file_row(large,'sparse')
        with self.assertRaisesRegex(ValueError,'BOUNDED_REGULAR'):m.json_read(large)
        with patch.object(m.os,'walk',return_value=[(str(self.src/'aeris_runtime'),[],['entry']*4097)]):
            with self.assertRaisesRegex(ValueError,'ENTRY_CAP'):m.walk(self.src,'aeris_runtime')

    def test_cli_prepare_and_check_integer_file_count(self):
        h={'SDK':'/sdk','AVD':'/avd','ADB':'/adb','ANDROID_USER_HOME':'/user','cachedImageDeclaredID':m.IMAGE}
        plan=dict(self.plan,profile=h)
        result={'status':'PREPARED_COMPONENT_CHECK_ONLY_NOT_FULL_ADMISSION','files':2634}
        for command in ('prepare','check'):
            argv=['runtime_layout.py',command,'--plan',str(self.tmp/'plan.json')]
            argv += ['--out',str(self.tmp/'result.json')] if command=='prepare' else ['--spec',str(self.dst/m.SPEC)]
            output=io.StringIO()
            with patch.object(m.sys,'argv',argv),patch.object(m,'json_read',return_value=plan),patch.object(m,'host_profile',return_value=h),patch.object(m,'prepare',return_value=result),patch.object(m,'check',return_value=result),contextlib.redirect_stdout(output):
                m.main()
            self.assertEqual(json.loads(output.getvalue())['files'],2634)

    def profile_fixture(self):
        sdk=self.tmp/'sdk';avd=self.tmp/'userhome/avd/aeris-beta-m1.avd';adb=self.tmp/'adb'
        (self.tmp/'userhome').mkdir()
        files={'emulator':sdk/'emulator/emulator','systemImage':sdk/'system-images/android-33/default/arm64-v8a/system.img','systemImageProperties':sdk/'system-images/android-33/default/arm64-v8a/source.properties','adb':adb}
        for k,p in files.items():self.put(p,k.encode())
        config=('hw.cpu.ncore = 4\nimage.sysdir.1 = '+str(sdk)+'/system-images/android-33/default/arm64-v8a\n').encode()
        self.put(avd/'config.ini',config)
        self.put(avd.parent/'aeris-beta-m1.ini',('avd.ini.encoding=UTF-8\npath='+str(avd)+'\ntarget=android-33\n').encode())
        self.put(self.tmp/'baseline-config.ini',config)
        data={'argv':[str(sdk/'emulator/emulator'),'-avd','aeris-beta-m1','-port','5582'], 'SDK':str(sdk),'AVD':str(avd),'ADB':str(adb),'ANDROID_USER_HOME':str(self.tmp/'userhome'),'AVDConfigSHA256':m.sha(config),'prerequisites':{k:{'path':str(p),'sha256':m.sha(k.encode())}for k,p in files.items()}}
        self.put(self.src/m.SPEC,m.encoded(data))
        self.put(self.src/'pilot/betaintegrated01/runtime/_sim32_kernel.cpython-314-darwin.so',struct.pack('<II',0xfeedfacf,0x100000c))
        return sdk,avd,adb,data

    def test_profile_abi_image_prerequisite_and_paths(self):
        sdk,avd,adb,data=self.profile_fixture()
        with patch.object(m,'CONFIG_TEMPLATE',self.tmp/'baseline-config.ini'),patch.object(m,'SPEC_SHA',m.sha(m.encoded(data))),patch.object(m.platform,'system',return_value='Darwin'),patch.object(m.platform,'machine',return_value='arm64'),patch.object(m.sys,'version_info',(3,14)),patch.object(m.shutil,'which',return_value=str(adb)),patch.object(m.subprocess,'run',return_value=type('R',(),{'stdout':'v24.14.1\n'})()):
            profile=m.host_profile(self.src,sdk,avd,adb,self.tmp/'userhome',m.IMAGE)
            self.assertIn('NOT_CHECKED',profile['cachedImageLiveVerification'])
            with self.assertRaisesRegex(ValueError,'IMAGE_ID'):m.host_profile(self.src,sdk,avd,adb,self.tmp/'userhome','wrong')
            with self.assertRaises((ValueError,FileNotFoundError)):m.host_profile(self.src,sdk,avd,self.tmp/'wrong',self.tmp/'userhome',m.IMAGE)
            with patch.object(m.platform,'machine',return_value='x86_64'),self.assertRaisesRegex(ValueError,'ABI'):m.host_profile(self.src,sdk,avd,adb,self.tmp/'userhome',m.IMAGE)
            relocated=self.tmp/'receiver-sdk'
            shutil.copytree(sdk,relocated)
            original_config=(avd/'config.ini').read_bytes()
            relocated_config=original_config.replace(str(sdk).encode(),str(relocated).encode())
            self.put(avd/'config.ini',relocated_config)
            moved=m.host_profile(self.src,relocated,avd,adb,self.tmp/'userhome',m.IMAGE)
            self.assertEqual(moved['effectiveSpec']['argv'][0],str(relocated/'emulator/emulator'))
            self.assertNotEqual(moved['effectiveSpecSHA256'],moved['baselineSpecSHA256'])
            self.assertEqual(moved['effectiveSpec']['AVDConfigSHA256'],m.sha(relocated_config))
            self.assertEqual((self.tmp/'baseline-config.ini').read_bytes(),original_config)
            for bad in (relocated_config.replace(b'ncore = 4',b'ncore = 8'),relocated_config.replace(b'arm64-v8a',b'x86_64'),relocated_config+b'unknown=true\n'):
                self.put(avd/'config.ini',bad)
                with self.assertRaisesRegex(ValueError,'EXACT_PATH_RELOCATION'):m.host_profile(self.src,relocated,avd,adb,self.tmp/'userhome',m.IMAGE)
            self.put(avd/'config.ini',original_config)
            index=avd.parent/'aeris-beta-m1.ini'
            original_index=index.read_bytes()
            for bad in (original_index.replace(str(avd).encode(),b'/foreign/author.avd'),original_index.replace(b'android-33',b'android-34'),original_index+b'path=/duplicate\n'):
                self.put(index,bad)
                with self.assertRaisesRegex(ValueError,'AVD_INDEX'):m.host_profile(self.src,sdk,avd,adb,self.tmp/'userhome',m.IMAGE)
            self.put(index,original_index)
            self.put(adb,b'tampered')
            with self.assertRaisesRegex(ValueError,'PREREQUISITE_HASH'):m.host_profile(self.src,sdk,avd,adb,self.tmp/'userhome',m.IMAGE)


if __name__=='__main__':unittest.main()
