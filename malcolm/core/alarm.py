from enum import Enum

from .base import Base


class AlarmSeverity(Enum):
    noAlarm, minorAlarm, majorAlarm, invalidAlarm, undefinedAlarm = range(5)

    def to_dict(self):
        return self.name


class AlarmStatus(Enum):
    noStatus, Read, Write, HiHi, High, LoLo, Low, State, Cos, Comm, Timeout, \
        HwLimit, Calc, Scan, Link, Soft, BadSub, UDF, Disable, Simm, \
        ReadAccess, WriteAccess = range(22)

    def to_dict(self):
        return self.name


class Alarm(Base):
    _endpoints = "severity,status,message".split(",")

    def __init__(self, severity, status, message):
        super(Alarm, self).__init__("Alarm")
        if type(severity) in (str, unicode):
            severity = AlarmSeverity.__members__[str(severity)]
        assert severity in AlarmSeverity, \
            "severity {} is not an AlarmSeverity".format(severity)
        self.severity = severity
        if type(status) in (str, unicode):
            status = AlarmStatus.__members__[str(status)]
        assert status in AlarmStatus, \
            "status {} is not an AlarmStatus".format(status)
        self.status = status
        assert type(message) in (str, unicode), \
            "message {} is not a string".format(message)
        self.message = str(message)

    @classmethod
    def ok(cls):
        return cls(AlarmSeverity.noAlarm, AlarmStatus.noStatus, "No alarm")

    def __eq__(self, other):
        if isinstance(other, Alarm):
            equal = self.severity == other.severity
            equal &= self.status == other.status
            equal &= self.message == other.message
            return equal
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)
