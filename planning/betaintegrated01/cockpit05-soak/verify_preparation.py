"""Contractor checks only: no ADB, sockets, runtime, writes into old scope or flight."""
from pathlib import Path
import hashlib, importlib, importlib.util, json, os, subprocess, sys
from unittest.mock import patch

R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R))
sys.dont_write_bytecode = True
P = Path(__file__).parent
E = R / 'evidence/betaintegrated01-cockpit05-soak'
checks = []


def check(name, ok):
    if not ok:
        raise AssertionError(name)
    checks.append(name)


def denied(*args, **kwargs):
    raise AssertionError('EXTERNAL_PROCESS_FORBIDDEN_IN_PREPARATION_CHECK')


def main():
    for path in sorted(P.rglob('*.py')):
        compile(path.read_bytes(), str(path), 'exec')
    check('AllNewPythonParsesWithoutBytecode', True)
    with patch.object(subprocess, 'run', denied), patch.object(subprocess, 'Popen', denied):
        h = 'planning.betaintegrated01.cockpit05-soak.host.'
        modules = {n: importlib.import_module(h + n) for n in (
            'contract', 'workspace', 'receiver05', 'resources', 'actual_controller',
            'android_guardian', 'capture_external', 'make_confirmation')}
        check('ImportNoExternalProcessOrRuntime', True)
        contract = modules['contract'].build_input_contract(R)
        check('Selected05APKAnd37SourcePinsAnd107RuntimePins',
              contract['selectedAPKInputs'] == 37 and contract['originalRuntimeInputs'] == 107)
        check('Physical39TypedParametersBothVariantsUnchanged',
              all(v['parameters'] == 39 and v['parameterTreesExactOriginal']
                  for v in contract['profiles'].values()))
        b = modules['contract'].task_budget
        check('EntryBelow20Refused', b(20*2**30-1)['admitted'] is False)
        check('DeclaredBudgetAt20FitsNotActualAdmission', b(20*2**30)['admitted'] is True)
        check('FiniteHardPeak9172468352', b()['taskHardPeakBytes'] == 9172468352)
        check('Native160Tar168Global192Bounds',
              [b()[k] for k in ('nativeJournalHardQuotaBytes', 'nativeTarAndSingleExportCapBytes',
                               'nativeExportGlobalHardCeilingBytes')] == [160*2**20,168*2**20,192*2**20])
        c = modules['actual_controller']
        check('BatteryUnknownSentinelAndBoolRejected',
              not c.qualified_battery_mv(65535) and not c.qualified_battery_mv(True)
              and not c.qualified_battery_mv(20999) and c.qualified_battery_mv(21000))
        check('BatteryNeverRelabeledAC', c.power_observation("Now drawing from 'Battery Power'\n 41%; discharging")['AC'] is False)
        check('ExactCurrentCaseAndOnlyOneAttempt', "attempt=='01'" in (P/'host/actual_controller.py').read_text()
              and "assert not entries,'ONE_COMBINED_START_ONLY" in (P/'host/actual_controller.py').read_text())
        check('NoLegacySmallTarConfirmation',
              'create_confirmation_descriptor_long' in (P/'host/receiver05.py').read_text()
              and 'receiver.make_confirmation(' in (P/'host/make_confirmation.py').read_text())
        for name in ('actual_controller', 'resources', 'android_guardian'):
            check(name+'UsesNewEvidenceRoot', str(modules[name].E).startswith(str(E)))
        source = (P/'host/actual_controller.py').read_text()
        check('AllAndroidPackageTargets05', 'vn.rtr.aeris.cockpit04' not in source)
        check('Frozen04RuntimeDeliberatelyReused', 'pilot.betaintegrated01.cockpit04.backend' in source)
        check('Fresh20BeforeHostAndAP', all(s in source for s in (
            'HOST_ENTRY20_IMMEDIATELY_BEFORE_POPEN', 'AP_ENTRY20_IMMEDIATELY_BEFORE_POPEN')))
        guardian = (P/'host/android_guardian.py').read_text()
        check('Fresh20BeforeAndAfterEmulatorPrime', all(s in guardian for s in (
            'EMULATOR_ENTRY20_BEFORE_PRIME','EMULATOR_ENTRY20_AFTER_REAL_PRIME')))
        check('EmulatorBound5400AndOwnLogCaps', '5400' in guardian and 'allocated(E)>32*2**20' in guardian
              and 'EMULATOR_CONSOLE16MiB_CAP' in guardian)
    pins = {str(p.relative_to(R)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(P.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    result = {'status':'PASS_CONTRACTOR_PREPARATION_CHECKS_NOT_RUNTIME_ACCEPTANCE',
              'checks':checks,'checkCount':len(checks),'sourcePins':pins,
              'actualADBCalls':0,'newEmulatorStarts':0,'newAPStarts':0,
              'actualThirtyMinuteAccepted':False,'wholeBetaAccepted':False,
              'limits':['Full current controller has not run on Android/SITL.',
                        'New test controller/resources/guardian received Contractor source checks, not completed independent QA.',
                        'Fresh Android UI setup, actual revision6 save and navigation geometry remain pending actual admission.']}
    (E/'contractor-preparation-check01.json').open('x').write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'checks':len(checks)}))


if __name__ == '__main__':
    main()
