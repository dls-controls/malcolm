import abc
import inspect

import numpy
from collections import OrderedDict


class VType(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def validate(self, value):
        """Validate the given value, raising an error if it can't be stored
        in this type without losing information. Return the argument in
        the correct type"""

    def __eq__(self, other):
        return type(self) == type(other)

    @classmethod
    def subclasses(cls):
        """Return list of subclasses"""
        subclasses = OrderedDict()
        for s in cls.__subclasses__():
            for g in s.subclasses().values() + [s]:
                if g.__name__ not in subclasses and not inspect.isabstract(g):
                    subclasses[g.__name__] = g
        return subclasses

    @classmethod
    def to_dict(cls):
        d = OrderedDict(name=cls.__name__)
        d.update(version="2")
        return d


class VTypeArray(object):

    @abc.abstractmethod
    def array_validate(self, value):
        """Validate the given value, raising an error if it can't be stored
        in this type without losing information. Return the argument in
        the correct type"""


class IsArray(VTypeArray):

    def validate(self, value):
        return self.array_validate(value)


class VNumber(VType, VTypeArray):

    @abc.abstractproperty
    def numpy_type(self):
        """Return the numpy type for this subclass"""

    def validate(self, value):
        """Check we match the numpy type"""
        if value is None:
            return value
        # Cast to the numpy datatype
        cast = self.numpy_type()(value)
        # Rely on numpy's equals to tell us if we've lost info
        assert cast == value, \
            "Lost information converting {} to {}".format(value, cast)
        return cast

    def array_validate(self, value):
        """Check we match the numpy type"""
        # If we got a python list, then convert to a numpy array
        if value is None:
            return value
        if type(value) == list:
            cast = numpy.array(value, dtype=self.numpy_type())
        else:
            # Check types match
            assert type(value).__module__ == numpy.__name__, \
                "Expected numpy array, got {}".format(type(value))
            # Check datatypes match
            assert value.dtype == numpy.dtype(self.numpy_type()), \
                "Expected {}, got {}".format(self.numpy_type(), value.dtype)
            # That'll do
            cast = value
        # If correct type, return
        return cast


class VDouble(VNumber):

    def numpy_type(self):
        return numpy.float64


class VDoubleArray(IsArray, VDouble):
    pass


class VFloat(VNumber):

    def numpy_type(self):
        return numpy.float32


class VFloatArray(IsArray, VFloat):
    pass


class VLong(VNumber):

    def numpy_type(self):
        return numpy.int64


class VLongArray(IsArray, VLong):
    pass


class VInt(VNumber):

    def numpy_type(self):
        return numpy.int32


class VIntArray(IsArray, VInt):
    pass


class VShort(VNumber):

    def numpy_type(self):
        return numpy.int16


class VShortArray(IsArray, VShort):
    pass


class VByte(VNumber):

    def numpy_type(self):
        return numpy.int8


class VByteArray(IsArray, VByte):
    pass


class VBool(VNumber):

    def numpy_type(self):
        return numpy.bool_


class VBoolArray(IsArray, VBool):
    pass


class VString(VType, VTypeArray):

    def validate(self, value):
        """Check we match the type"""
        cast = str(value)
        return cast

    def array_validate(self, value):
        """Check we match the type"""
        assert hasattr(value, "__iter__"), \
            "Expected iterable, got {}".format(value)
        cast = [str(x) for x in value]
        return cast


class VStringArray(IsArray, VString):
    pass


class EnumString(str):

    def __eq__(self, other):
        return self.i == other or str.__eq__(self, other)

    def to_dict(self):
        return self.i


class VEnum(VType):

    def __init__(self, labels):
        if type(labels) == str:
            labels = labels.split(",")
        self.labels = []
        for i, label in enumerate(labels):
            assert type(label) == str, \
                "Expected string, got {}".format(repr(label))
            es = EnumString(label)
            es.i = i
            self.labels.append(es)
        self.labels = tuple(self.labels)

    def validate(self, value):
        try:
            return self.labels[value]
        except:
            if value in self.labels:
                return value
            raise AssertionError(
                "Value {} is not an index or value in {}"
                .format(value, self.labels))

    def to_dict(self):
        d = super(VEnum, self).to_dict()
        d.update(labels=self.labels)
        return d

    def __eq__(self, other):
        if type(self) != type(other) or len(self.labels) != len(other.labels):
            return False
        else:
            return min(a == b for a, b in zip(self.labels, other.labels))


class VObject(VEnum):

    def __init__(self, labels=None, get_device=None):
        if labels is not None:
            super(VObject, self).__init__(labels)
        else:
            self.labels = labels
        self.get_device = get_device

    def validate(self, value):
        if self.labels is not None and self.get_device is not None:
            # running under process, if string get instance
            if isinstance(value, basestring):
                value = self.get_device(value)
            super(VObject, self).validate(value.name)
        return value


class VTable(VType):

    def validate(self, value):
        cast = []
        datalengths = set()
        for column in value:
            assert type(column) in (list, tuple), \
                "Expected list or tuple, got {}".format(column)
            assert len(column) == 3, \
                "Expected (name, typ, array_value), got {}".format(column)
            name = column[0]
            assert type(name) == str, \
                "Expected string, got {}".format(repr(name))
            typ = column[1]
            assert issubclass(typ, VType), \
                "Expected VType subclass, got {}".format(typ)
            assert hasattr(typ, "array_validate"), \
                "Expected something with array_validate(), got {}".format(typ)
            data = column[2]
            datalengths.add(len(data))
            try:
                data = typ().array_validate(data)
            except Exception as e:
                raise AssertionError("Cannot validate {}: {}".format(name, e))
            cast.append((name, typ, data))
        assert len(datalengths) == 1, \
            "Got mismatching column lengths: {}".format(datalengths)
        return cast
