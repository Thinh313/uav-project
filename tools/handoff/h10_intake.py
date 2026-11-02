#!/usr/bin/env python3
"""Portable, public-derived H10 mocks; not original HOLD or Android acceptance.

Execute unchanged assertions from selected H10 tests. Only two test literals are
adapted: the Node executable and the private-media fixture selector. Production
source is never rewritten. Synthetic fixtures exercise real fsync and local IPC.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'planning/betarc01/runtime-h10'
SCOPE = 'PUBLIC_DERIVED_SYNTHETIC_H10_MOCK_NOT_ORIGINAL_34_OR_ANDROID_ACCEPTANCE'


def main():
    if sys.version_info < (3, 12):
        raise SystemExit('Python 3.12 or newer is required')
    node = shutil.which('node')
    if not node:
        raise SystemExit('Node 24 or newer must be on PATH')
    version = subprocess.check_output([node, '--version'], text=True).strip()
    if int(version.lstrip('v').split('.')[0]) < 24:
        raise SystemExit('Node 24 or newer is required for the H10 module hooks')
    if os.environ.get('NODE_OPTIONS') or os.environ.get('NODE_PATH'):
        raise SystemExit('Run without NODE_OPTIONS or NODE_PATH injections')
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    sys.dont_write_bytecode = True
    suite = unittest.TestSuite()
    fingerprints = {}
    selection = {
        'test-command-h10.py': ('CommandsH10', None),
        'test-managed-close-h10.py': ('ManagedCloseH10', None),
        'test-native-close-h10.py': ('NativeCloseH10', None),
        'test-caps03.py': ('Caps03', [
            'test_actual_artifact_strict_typed_boundary_all_original_pools',
            'test_actual_metadata_admit_boundary_owner_limits_not_relaxed',
            'test_case_and_campaign_real_reserve_delta_and_no_other_policy_delta']),
    }

    class TestLiteralAdapter(ast.NodeTransformer):
        def visit_Constant(self, value):
            if value.value == '/usr/local/bin/node':
                return ast.copy_location(ast.Constant(node), value)
            if value.value == 'test-command-fixture.mjs':
                return ast.copy_location(ast.Constant('test-command-fixture-public-handoff.mjs'), value)
            return value

    for name, (class_name, methods) in selection.items():
        file = BASE / name
        raw = file.read_bytes()
        fingerprints[str(file.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
        module = types.ModuleType('public_derived_h10_' + name.replace('-', '_').replace('.', '_'))
        module.__file__ = str(file)
        sys.modules[module.__name__] = module
        tree = ast.fix_missing_locations(TestLiteralAdapter().visit(ast.parse(raw)))
        exec(compile(tree, str(file), 'exec'), module.__dict__)
        case = getattr(module, class_name)
        if methods is None:
            methods = unittest.defaultTestLoader.getTestCaseNames(case)
        for method in methods:
            suite.addTest(case(method))
    fixture = BASE / 'test-command-fixture-public-handoff.mjs'
    fingerprints[str(fixture.relative_to(ROOT))] = hashlib.sha256(fixture.read_bytes()).hexdigest()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'scope': SCOPE, 'status': 'PASS' if result.wasSuccessful() else 'FAIL',
        'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
        'python': sys.version.split()[0], 'node': version, 'sourceSHA256': fingerprints,
        'privateOriginal34Reproduced': False, 'androidSITLAcceptance': False,
        'hardwareAcceptance': False, 'betaReady': False}, indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
