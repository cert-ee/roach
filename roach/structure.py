# Copyright (C) 2018 Jurriaan Bremer.
# This file is part of Roach - https://github.com/jbremer/roach.
# See the file 'docs/LICENSE.txt' for copying permission.

from builtins import int
import ctypes

from roach.string.bin import (
    IntWorker, Int8, UInt8, Int16, UInt16, Int32, UInt32, Int64, UInt64
)

mapping = {
    Int8: ctypes.c_byte,
    UInt8: ctypes.c_ubyte,
    Int16: ctypes.c_short,
    UInt16: ctypes.c_ushort,
    Int32: ctypes.c_int,
    UInt32: ctypes.c_uint,
    Int64: ctypes.c_longlong,
    UInt64: ctypes.c_ulonglong,
}

class Structure(object):
    # TODO Default value in Python, should we change this to 1?
    _pack_ = 0
    _fields_ = []

    def __init__(self):
        self.subfields, fields = {}, []
        for field, type_ in self._fields_:
            if isinstance(type_, IntWorker):
                if type_.mul:
                    type_ = mapping[type_.__class__] * type_.mul
                else:
                    type_ = mapping[type_.__class__]
            elif isinstance(type_, (int, int)):
                type_ = ctypes.c_char * type_
            elif issubclass(type_, Structure):
                # Keep track, likely for Python GC purposes.
                self.subfields[field] = type_()
                type_ = self.subfields[field].Klass
            fields.append((field, type_))

        class Klass(ctypes.Structure):
            _pack_ = self._pack_
            _fields_ = fields

            def as_dict(self):
                return self._parent_.as_dict()

        self.Klass = Klass
        self.Klass._parent_ = self

    def __getattr__(self, item):
        ret = getattr(self._values_, item)
        if isinstance(ret, ctypes.Structure):
            ret._parent_._values_ = ret

        # Allow caller to omit the [:] part.
        if hasattr(ret, "__getitem__"):
            return ret[:]
        return ret

    def as_dict(self, values=None):
        ret = {}
        for field, type_ in self._fields_:
            value = getattr(values or self._values_, field)
            if isinstance(type_, type) and issubclass(type_, Structure):
                ret[field] = value._parent_.as_dict(value)
            elif hasattr(value, "__getitem__"):
                ret[field] = value[:]
            else:
                ret[field] = value
        return ret

    @classmethod
    def sizeof(cls):
        return ctypes.sizeof(cls().Klass)

    @classmethod
    def from_buffer_copy(cls, buf):
        obj = cls()
        if isinstance(buf, str):
            try:
                buf = buf.encode("utf-8")
            except UnicodeDecodeError as e:
                print("Warning, a string can't be decoded as UTF-8 using bigint() function")
        obj._values_ = obj.Klass.from_buffer_copy(buf)
        return obj

    parse = from_buffer_copy
