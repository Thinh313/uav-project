from pathlib import Path
import hashlib,importlib.util,json,struct,tempfile,unittest,zlib
P=Path(__file__).with_name('diagnostic-raw-nav.py');S=importlib.util.spec_from_file_location('diagnostic_raw_nav',P);M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
from pilot.betaintegrated01.control01.mavlink import crc,FramingError
class RawWireTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='diagnostic-wire-',dir=M.ROOT/'evidence/navfix13');self.addCleanup(self.tmp.cleanup);self.raw=Path(self.tmp.name);(self.raw/'transport-journal').mkdir()
  payload=struct.pack('<IBBBBB',0,2,3,1,3,3);header=bytes([0xfd,len(payload),0,0,1,42,1,0,0,0]);self.packet=header+payload+struct.pack('<H',crc(header[1:]+payload,50))
 def write(self,packet):
  b={'seq':0,'previous':'0'*64,'payload':{'eventKind':'AP_RELAY_RX','data':{'rawHex':packet.hex(),'_observedHostNs':5}}};raw=M.canonical(b);envelope={'body':b,'crc32':format(zlib.crc32(raw),'08x'),'sha256':hashlib.sha256(bytes(32)+raw).hexdigest()};(self.raw/'transport-journal/segment-000000.jsonl').write_bytes(M.canonical(envelope)+b'\n')
 def test_valid_wire_journal_reports_verified(self):
  self.write(self.packet);r=M.read_transport(self.raw);self.assertEqual(r['streams']['AP_RELAY_RX:0']['samples'],1);self.assertTrue(r['MAVLinkCompletePacketCRCVerified']);self.assertEqual(r['MAVLinkFramers']['AP_RELAY_RX']['pendingBytes'],0)
 def test_rechained_wrapper_cannot_hide_corrupt_MAVCRC(self):
  bad=self.packet[:-1]+bytes([self.packet[-1]^1]);self.write(bad)
  with self.assertRaisesRegex(FramingError,'CRC'):M.read_transport(self.raw)
 def test_valid_wrapper_partial_wire_tail_not_complete(self):
  self.write(self.packet[:-1])
  with self.assertRaisesRegex(ValueError,'PARTIAL_TAIL'):M.read_transport(self.raw)
 def test_bad_wrapper_crc_refuses_before_wire(self):
  self.write(self.packet);p=self.raw/'transport-journal/segment-000000.jsonl';x=json.loads(p.read_bytes());x['crc32']='00000000';p.write_bytes(M.canonical(x)+b'\n')
  with self.assertRaisesRegex(ValueError,'CHAIN_OR_CRC'):M.read_transport(self.raw)
 def test_non_MAVLink_wire_not_skipped(self):
  self.write(b'junk'+self.packet)
  with self.assertRaisesRegex(FramingError,'NON_MAVLINK_BYTE'):M.read_transport(self.raw)
if __name__=='__main__':unittest.main(verbosity=2)
