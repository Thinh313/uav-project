"""Offline unit/fault tests; no Docker, AP, emulator or network."""
import hashlib
import unittest
import tempfile
import os
from pathlib import Path
from launch_contract import LaunchEvidenceContract, require_executable_artifact, require_durable_create_command, retain_prefix

class ContractTests(unittest.TestCase):
    def test_archive_execute_bit_blocker(self):
        p = Path('evidence/sim32-instrument01/direct-uncorrected-source/arducopter')
        self.assertEqual(p.stat().st_mode & 0o777, 0o644)
        with self.assertRaisesRegex(ValueError, 'EXECUTABLE_MODE_0755_REQUIRED'):
            require_executable_artifact(p)

    def test_hash_rejected_before_mode(self):
        with self.assertRaisesRegex(ValueError, 'EXACT_BINARY_SHA_REQUIRED'):
            require_executable_artifact('pilot/beta06g3/launch_contract.py', '0' * 64)

    def test_mode_only_counterexample_real_files(self):
        # Tiny synthetic ELF header, structural fixture only, never executed.
        data = bytearray(64)
        data[:6] = b'\x7fELF\x02\x01'
        data[18:20] = (183).to_bytes(2, 'little')
        with tempfile.TemporaryDirectory(prefix='.mock-mode-', dir='pilot/beta06g3') as d:
            p=Path(d)/'synthetic-arm64'
            p.write_bytes(data)
            digest=hashlib.sha256(data).hexdigest()
            p.chmod(0o644)
            with self.assertRaisesRegex(ValueError, 'EXECUTABLE_MODE_0755_REQUIRED'):
                require_executable_artifact(p, digest)
            p.chmod(0o755)
            got=require_executable_artifact(p, digest)
            self.assertEqual(got['sha256'], digest)
            self.assertEqual(p.read_bytes(), data)
            self.assertFalse(got['allocationOrExecutionPerformed'])

    def test_wrong_arch_and_symlink_real_files(self):
        with tempfile.TemporaryDirectory(prefix='.mock-arch-', dir='pilot/beta06g3') as d:
            p=Path(d)/'synthetic-x86'
            data=bytearray(64);data[:6]=b'\x7fELF\x02\x01';data[18:20]=(62).to_bytes(2,'little')
            p.write_bytes(data);p.chmod(0o755)
            with self.assertRaisesRegex(ValueError, 'ELF64_LE_AARCH64_REQUIRED'):
                require_executable_artifact(p, hashlib.sha256(data).hexdigest())
            link=Path(d)/'link';link.symlink_to(p.resolve())
            with self.assertRaisesRegex(ValueError, 'REGULAR_NONLINK_BINARY_REQUIRED'):
                require_executable_artifact(link)

    def test_autoremove_rejected(self):
        for flag in ['--rm', '--rm=true', '--rm=false']:
            with self.assertRaisesRegex(ValueError, 'NO_AUTOREMOVE'):
                require_durable_create_command(['docker', 'create', flag])

    def test_run_and_privilege_rejected(self):
        for argv in [['docker', 'run'], ['docker', 'create', '--privileged']]:
            with self.assertRaises(ValueError):
                require_durable_create_command(argv)
        self.assertTrue(require_durable_create_command(['docker', 'create', '--cap-drop', 'ALL']))

    def test_prestart_receipt_missing(self):
        c=LaunchEvidenceContract()
        with self.assertRaisesRegex(ValueError, 'PRESTART_DURABLE'):
            c.created('a' * 64, intent_fsynced=True, result_fsynced=False, inspect_fsynced=True)
        self.assertEqual(c.phase, 'NEW')

    def test_capture_and_double_start_rejected(self):
        c=LaunchEvidenceContract()
        c.created('a'*64, intent_fsynced=True, result_fsynced=True, inspect_fsynced=True)
        with self.assertRaisesRegex(ValueError, 'PRESTART_CAPTURE'):
            c.permit_single_start(event_capture_ready=False, attached_output_ready=True)
        self.assertEqual(c.permit_single_start(event_capture_ready=True, attached_output_ready=True), 'a'*64)
        with self.assertRaises(ValueError):
            c.permit_single_start(event_capture_ready=True, attached_output_ready=True)

    def test_early_exit_terminal_and_no_retry(self):
        c=LaunchEvidenceContract()
        c.created('a'*64, intent_fsynced=True, result_fsynced=True, inspect_fsynced=True)
        c.permit_single_start(event_capture_ready=True, attached_output_ready=True)
        with self.assertRaisesRegex(ValueError, 'TERMINAL_CAPTURE_INCOMPLETE'):
            c.terminal(inspect_fsynced=False, output_fsynced=True, wait_fsynced=True, events_fsynced=True)
        c.terminal(inspect_fsynced=True, output_fsynced=True, wait_fsynced=True, events_fsynced=True)
        self.assertEqual(c.phase, 'CLOSED_RETAIN_CONTAINER_NO_AUTORETRY')
        with self.assertRaises(ValueError):
            c.permit_single_start(event_capture_ready=True, attached_output_ready=True)

    def test_stream_overflow_visible_not_pass(self):
        r=retain_prefix(b'12345',4)
        self.assertEqual(r['retained'], b'1234')
        self.assertTrue(r['truncated'])
        self.assertFalse(r['acceptanceEligible'])
        self.assertEqual(r['observedBytes'],5)

if __name__ == '__main__':
    unittest.main()
