import unittest

from msp import MspApiVersionCommand, MspVtxConfigCommand, VtxConfig, MspVtxTableBandCommand, MspSetVtxConfigCommand
from msp_request import MspPackage, MspResult, MspCommand, MspError


class MyTestCase(unittest.TestCase):
    def test_api_version_request(self):
        package = MspPackage()
        # API_VERSION is a single packet request.
        buffer = b"\x30\x00\x01\x01"
        result = package.handle_frame(buffer)
        self.assertIsNone(result.error)
        self.assertEqual(MspCommand.API_VERSION, result.command)
        self.assertIsNone(result.payload)

    def test_bad_checksum(self):
        package = MspPackage()
        buffer = b"\x30\x00\x01\x02"
        result = package.handle_frame(buffer)
        self.assertEqual(MspError.CHECKSUM, result.error)

    def test_bad_version(self):
        package = MspPackage()
        buffer = b"\x50\x00\x01\x01"
        result = package.handle_frame(buffer)
        self.assertEqual(MspError.VERSION_MISMATCH, result.error)

    def test_non_start_packet(self):
        package = MspPackage()
        # If it sees a non-start packet without having seen the corresponding start
        # packet it ignores it and starts waiting (searching) for a start packet.
        buffer = b"\x20\x00\x01\x01"
        result = package.handle_frame(buffer)
        self.assertIsNone(result)

    def test_api_version_response(self):
        command = MspApiVersionCommand()
        response = command.get_response(None)
        # TODO: make 6 a constant (see `msp_response` logic).
        frame_buf = bytearray(6)
        finished = response.write(0, frame_buf)
        self.assertTrue(finished)
        expected = bytes([0x10, 0x03, command._PROTOCOL_VERSION, command._VERSION_MAJOR, command._VERSION_MINOR, 0x28])
        self.assertEqual(expected, frame_buf)

    def test_vtx_config_response(self):
        config = VtxConfig()
        command = MspVtxConfigCommand(config)
        response = command.get_response(None)

        # TODO: make 6 a constant (see `msp_response` logic).
        frame_buf = bytearray(6)

        seq = 0
        finished = response.write(seq, frame_buf)
        self.assertFalse(finished)
        expected = bytes([0x10, 0x0f, 0x03, 0x00, 0x00, 0x00])
        self.assertEqual(expected, frame_buf)

        seq += 1
        finished = response.write(seq, frame_buf)
        self.assertFalse(finished)
        expected = bytes([seq, 0x01, 0x00, 0x00, 0x01, 0x00])
        self.assertEqual(expected, frame_buf)

        seq += 1
        finished = response.write(seq, frame_buf)
        self.assertFalse(finished)
        expected = bytes([seq, 0xFD, 0x7F, 0x01, 0x02, 0x03])
        self.assertEqual(expected, frame_buf)

        seq += 1
        finished = response.write(seq, frame_buf)
        self.assertTrue(finished)
        expected = bytes([seq, 0x04, 0xD2, 0x00, 0x00, 0x00])
        self.assertEqual(expected, frame_buf)

    def test_vtx_table_band(self):
        config = VtxConfig()
        command = MspVtxTableBandCommand(config)
        response = command.get_response(b'\x01')

        # TODO: make 6 a constant (see `msp_response` logic).
        frame_buf = bytearray(6)

        seq = 0
        finished = response.write(seq, frame_buf)
        self.assertFalse(finished)
        expected = bytes([0x10, 0x1d, 0x01, 0x08, ord("B"), ord("O")])
        self.assertEqual(expected, frame_buf)

        seq += 1
        finished = response.write(seq, frame_buf)
        self.assertFalse(finished)
        expected = bytes([seq, ord("S"), ord("C"), ord("A"), ord("M"), ord("_")])
        self.assertEqual(expected, frame_buf)

        seq += 1
        finished = response.write(seq, frame_buf)
        self.assertFalse(finished)
        expected = bytes([seq, ord("A"), ord("A"), 0x01, 0x08, 0xE9])
        self.assertEqual(expected, frame_buf)

        seq += 1
        finished = response.write(seq, frame_buf)
        self.assertFalse(finished)
        expected = bytes([seq, 0x16, 0xD5, 0x16, 0xC1, 0x16])
        self.assertEqual(expected, frame_buf)

        seq += 1
        finished = response.write(seq, frame_buf)
        self.assertFalse(finished)
        expected = bytes([seq, 0xAD, 0x16, 0x99, 0x16, 0x85])
        self.assertEqual(expected, frame_buf)

        seq += 1
        finished = response.write(seq, frame_buf)
        self.assertFalse(finished)
        expected = bytes([seq, 0x16, 0x71, 0x16, 0x00, 0x00])
        self.assertEqual(expected, frame_buf)

        seq += 1
        finished = response.write(seq, frame_buf)
        self.assertTrue(finished)
        expected = bytes([seq, 0xF1, 0x00, 0x00, 0x00, 0x00])
        self.assertEqual(expected, frame_buf)

    def test_set_vtx_config(self):
        config = VtxConfig()
        command = MspSetVtxConfigCommand(config)
        response = command.get_response(b'\x00\x00\x01\x00')

        # TODO: make 6 a constant (see `msp_response` logic).
        frame_buf = bytearray(6)
        finished = response.write(0, frame_buf)
        self.assertTrue(finished)
        expected = bytes([0x10, 0x00, 0x59, 0x00, 0x00, 0x00])
        self.assertEqual(expected, frame_buf)


if __name__ == '__main__':
    unittest.main()
