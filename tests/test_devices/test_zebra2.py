#!/bin/env dls-python
from pkg_resources import require
from malcolm.core.runnabledevice import DState
import time
require("mock")
require("pyzmq")
import unittest
import sys
import os
import cothread

import logging
logging.basicConfig()
# logging.basicConfig(level=logging.DEBUG)#, format='%(asctime)s
# %(name)-12s %(levelname)-8s %(message)s')
from mock import MagicMock, patch
# Module import
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from malcolm.devices.zebra2.zebra2comms import Zebra2Comms


class Zebra2CommsTest(unittest.TestCase):

    @patch("malcolm.devices.zebra2.zebra2comms.socket")
    def setUp(self, mock_socket):
        self.c = Zebra2Comms("h", "p")
        self.s = mock_socket

    def test_init(self):
        self.s.assert_called_once_with()
        self.c.sock.connect.assert_called_once_with(("h", "p"))

    def test_multiline_response_good(self):
        messages = ["!TTLIN 6\n", "!OUTENC 4\n!CAL", "C 2\n.\nblah"]
        self.c.sock.recv.side_effect = messages
        resp = list(self.c.get_response())
        expected = ["TTLIN 6", "OUTENC 4", "CALC 2"]
        self.assertEqual(resp, expected)

    def test_two_resp(self):
        messages = ["OK =mm\n", "OK =232\n"]
        self.c.sock.recv.side_effect = messages
        self.assertEqual(self.c.get_response(), "OK =mm")
        self.assertEqual(self.c.get_response(), "OK =232")

    def test_num_blocks(self):
        self.c.sock.recv.return_value = """!TTLIN 6
!OUTENC 4
!CALC 2
!SRGATE 4
!PCOMP 4
!LUT 8
!TTLOUT 10
!LVDSOUT 2
!ADC 8
!DIV 4
!INENC 4
!COUNTER 8
!ADDER 1
!PCAP 1
!POSENC 4
!LVDSIN 2
!PGEN 2
!QDEC 4
!SEQ 4
!PULSE 4
.
"""
        blocks = self.c.get_num_blocks()
        self.c.sock.send.assert_called_once_with("*BLOCKS?\n")
        pretty = ",".join("{}={}".format(k, v) for k, v in blocks.items())
        expected = "TTLIN=6,OUTENC=4,CALC=2,SRGATE=4,PCOMP=4,LUT=8,TTLOUT=10,LVDSOUT=2,ADC=8,DIV=4,INENC=4,COUNTER=8,ADDER=1,PCAP=1,POSENC=4,LVDSIN=2,PGEN=2,QDEC=4,SEQ=4,PULSE=4"
        self.assertEqual(pretty, expected)

    def test_field_data(self):
        self.c.sock.recv.return_value = """!FUNC 0 param lut
!INPA 1 bit_in 
!INPB 2 bit_in 
!INPC 3 bit_in 
!INPD 4 bit_in 
!INPE 5 bit_in 
!VAL 6 bit_out bit
.
"""
        field_data = self.c.get_field_data("LUT")
        self.c.sock.send.assert_called_once_with("LUT.*?\n")
        pretty = ",".join("{}={}:{}".format(k, c, t)
                          for k, (c, t) in field_data.items())
        expected = "FUNC=param:lut,INPA=bit_in:,INPB=bit_in:,INPC=bit_in:,INPD=bit_in:,INPE=bit_in:,VAL=bit_out:bit"
        self.assertEqual(pretty, expected)

    def test_changes(self):
        self.c.sock.recv.return_value = """!PULSE0.WIDTH=1.43166e+09
!PULSE1.WIDTH=1.43166e+09
!PULSE2.WIDTH=1.43166e+09
!PULSE3.WIDTH=1.43166e+09
!PULSE0.INP (error)
!PULSE1.INP (error)
!PULSE2.INP (error)
!PULSE3.INP (error)
.
"""
        changes = self.c.get_changes()
        self.c.sock.send.assert_called_once_with("*CHANGES?\n")
        pretty = ",".join("{}={}".format(k, v)
                          for k, v in changes.items())
        expected = "PULSE0.WIDTH=1.43166e+09,PULSE1.WIDTH=1.43166e+09,PULSE2.WIDTH=1.43166e+09,PULSE3.WIDTH=1.43166e+09,PULSE0.INP=<type 'exceptions.Exception'>,PULSE1.INP=<type 'exceptions.Exception'>,PULSE2.INP=<type 'exceptions.Exception'>,PULSE3.INP=<type 'exceptions.Exception'>"
        self.assertEqual(pretty, expected)


class Zebra2BlockTest(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main(verbosity=2)
