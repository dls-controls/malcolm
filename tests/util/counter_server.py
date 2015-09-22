# Module import
from pkg_resources import require
require("cothread==2.14b1")
require("pyzmq")
import sys
import os
import logging
logging.basicConfig()
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from malcolm.core.directoryService import DirectoryService
from malcolm.core.loop import TimerLoop
from malcolm.core import Device, wrap_method


class Counter(Device):

    def __init__(self, name, timeout=None):
        super(Counter, self).__init__(name, timeout)
        self.counter = 0
        self.add_loop(TimerLoop("timer", self.do_count, 0.01))

    def do_count(self):
        self.counter += 1

    @wrap_method()
    def getCount(self):
        return self.counter

    @wrap_method()
    def hello(self):
        self.cothread.Sleep(0.1)
        return "world"

    @wrap_method()
    def longHello(self):
        self.cothread.Sleep(0.5)
        return "long world"

    def exit(self):
        pass

ds = DirectoryService(["zmq://ipc:///tmp/sock.ipc"])
ds.create_device(Counter, "The Counter")
ds.run()
