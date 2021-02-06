import unittest

from sbus_frame import SBusFrame


# The test frames here were randomly generated and then parsed with parsing logic copied from
# https://github.com/zendes/SBUS/blob/5cf196c/SBUS.cpp#L33
# See sbus-frame-gen.c elsewhere in this repo for the actual code.
# While random, the frames here were chosen because they demonstrate all possible combinations
# for the two binary channels and separately the lost_frame and failsafe bits.
class SBusFrameTests(unittest.TestCase):
    def test_data_1(self):
        frame = "0F:1A:28:A2:95:7C:07:EA:05:F6:CE:BF:61:AD:79:3F:2D:B7:CA:FA:62:87:0D:85:00"
        expected = "01A:445:256:3BE:6A0:40B:3BD:5FE:561:735:4FD:396:4AB:5F5:1D8:06C:7FF:000"
        lost = True
        safe = False
        self._test(frame, expected, lost, safe)

    def test_data_2(self):
        frame = "0F:7A:F6:E1:E7:0B:54:07:78:4F:39:75:19:05:40:27:91:28:2E:B5:CC:A7:61:6B:00"
        expected = "67A:43E:79F:205:075:6F0:653:3A9:519:000:49D:448:2E2:16A:1F3:30D:7FF:7FF"
        lost = False
        safe = True
        self._test(frame, expected, lost, safe)

    def test_data_3(self):
        frame = "0F:A3:9A:E1:15:24:C1:56:CC:C6:A5:9B:29:8D:B2:B4:5D:3B:77:48:B0:CC:82:6E:00"
        expected = "2A3:433:057:092:56C:598:171:4DD:529:651:6D2:5AE:773:090:32C:416:000:7FF"
        lost = True
        safe = True
        self._test(frame, expected, lost, safe)

    def test_data_4(self):
        frame = "0F:F0:F1:72:56:36:7C:02:A7:2A:D1:0B:DE:94:9B:59:86:E1:BD:EE:E7:9A:E1:A0:00"
        expected = "1F0:65E:159:61B:027:54E:44A:05E:4DE:372:166:0C3:3DE:7DD:6B9:70C:000:000"
        lost = False
        safe = False
        self._test(frame, expected, lost, safe)

    def _test(self, frame, expected, lost, safe):
        test_data = bytearray.fromhex(frame.replace(":", ""))

        parser = SBusFrame()
        parser.parse(test_data)

        actual = ":".join("{:03X}".format(ch) for ch in parser.channels)

        self.assertEqual(expected, actual)
        self.assertEqual(parser.lost_frame, lost)
        self.assertEqual(parser.failsafe, safe)


if __name__ == '__main__':
    unittest.main()
