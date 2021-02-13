import unittest

from msp import MspApiVersionCommand
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
        self.assertEqual(MspError.CRC_ERROR, result.error)

    def test_bad_version(self):
        package = MspPackage()
        buffer = b"\x50\x00\x01\x01"
        result = package.handle_frame(buffer)
        self.assertEqual(MspError.VER_MISMATCH, result.error)

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
        expected = bytes([0x10, 0x03, command.PROTOCOL_VERSION, command.VERSION_MAJOR, command.VERSION_MINOR, 0x28])
        self.assertEqual(expected, frame_buf)


if __name__ == '__main__':
    unittest.main()
