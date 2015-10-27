#!/bin/env dls-python
from pkg_resources import require
from collections import OrderedDict
require("mock")
require("pyzmq")
import unittest
import sys
import os
import cothread

import logging
# logging.basicConfig()
# logging.basicConfig(level=logging.DEBUG)
from mock import MagicMock, patch
# Module import
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from malcolm.core.transport import ClientSocket, SType


class InqSock(cothread.EventQueue):

    def __init__(self, address):
        super(InqSock, self).__init__()
        self.connect = MagicMock()
        self.send = MagicMock()
        self.settimeout = MagicMock()
        self.address = address

    def once(self):
        self.received_message(self.Wait(1))


class WsClientSocketTest(unittest.TestCase):

    @patch("malcolm.wstransport.wsclientsocket.WebSocketBaseClient", InqSock)
    def setUp(self):
        self.cs = ClientSocket.make_socket("ws://192.168.0.1:8888")
        self.cs.loop_run()

    def test_request(self):
        response = MagicMock()
        typ = SType.Call
        kwargs = OrderedDict()
        kwargs.update(endpoint="zebra1.run")
        self.cs.request(response, typ, kwargs)
        self.cs.sock.send.assert_called_once_with(
            '{"type": "Call", "id": 0, "endpoint": "zebra1.run"}')
        self.assertEqual(response.call_count, 0)

    def test_response(self):
        response = MagicMock()
        self.cs.sock.Signal('{"type": "Return", "id": 0, "value": 32}')
        self.cs.request(response, SType.Call, dict(endpoint="zebra1.run"))
        cothread.Yield()
        response.assert_called_once_with(SType.Return, value=32)

    def test_creation(self):
        self.assertEqual(self.cs.name, "ws://192.168.0.1:8888")
        self.assertEqual(self.cs.address, "ws://192.168.0.1:8888")

    def tearDown(self):
        msgs = []

        def log_debug(msg):
            msgs.append(msg)

        self.cs.log_debug = log_debug
        self.cs = None
        self.assertEqual(msgs, ['Garbage collecting loop', 'Stopping loop',
                                'Waiting for loop to finish', 'Loop finished',
                                'Loop garbage collected'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
