import unittest
import runtime


class Lifecycle(unittest.TestCase):
    def test_disk_boundary(self):
        self.assertFalse(runtime.admitted(22*2**30-1,0))
        self.assertTrue(runtime.admitted(22*2**30,0))

    def test_quota_boundary(self):
        self.assertFalse(runtime.admitted(30*2**30,256*2**20))

    def test_absent_lowercase(self):
        self.assertTrue(runtime.missing_object(1,'error: no such object: aeris-simsitl76\n'))

    def test_absent_uppercase(self):
        self.assertTrue(runtime.missing_object(1,'Error: No such object: aeris-simsitl76'))

    def test_permission_not_absent(self):
        self.assertFalse(runtime.missing_object(1,'permission denied for aeris-simsitl76'))

    def test_daemon_not_absent(self):
        self.assertFalse(runtime.missing_object(1,'Cannot connect to Docker daemon'))

    def test_existing_or_wrong_name(self):
        self.assertFalse(runtime.missing_object(0,''))
        self.assertFalse(runtime.missing_object(1,'no such object: another-container'))

    def test_kernel_listen_socket(self):
        self.assertTrue(runtime.serial_listening(' 0: 00000000:1680 00000000:0000 0A 0:0'))
        self.assertTrue(runtime.serial_listening(' 0: 00000000000000000000000000000000:1680 00000000:0000 0A 0:0'))
        self.assertFalse(runtime.serial_listening(' 0: 00000000:1680 00000000:0000 01 0:0'))
        self.assertFalse(runtime.serial_listening(' 0: 00000000:1681 00000000:0000 0A 0:0'))


if __name__=='__main__':unittest.main(verbosity=2)
