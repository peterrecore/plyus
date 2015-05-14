import json

from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.types import TypeDecorator, VARCHAR

import util


class MutableList(Mutable, list):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain lists to MutableLists."

        if not isinstance(value, MutableList):
            if isinstance(value, list):
                return MutableList(value)

            # this call will raise ValueError
            raise ValueError("tried to coerce a non list into mutable list")
        else:
            return value

    def __setitem__(self, idx, value):
        list.__setitem__(self, idx, value)
        self.changed()

    def __setslice__(self, start, stop, values):
        list.__setslice__(self, start, stop, values)
        self.changed()

    def __delitem__(self, idx):
        list.__delitem__(self, idx)
        self.changed()

    def __delslice__(self, start, stop):
        list.__delslice__(self, start, stop)
        self.changed()

    def append(self, value):
        list.append(self, value)
        self.changed()

    def insert(self, idx, value):
        list.insert(self, idx, value)
        self.changed()

    def extend(self, values):
        list.extend(self, values)
        self.changed()

    def pop(self, *args, **kw):
        value = list.pop(self, *args, **kw)
        self.changed()
        return value

    def remove(self, value):
        list.remove(self, value)
        self.changed()

class JSONEncoded(TypeDecorator):
    "Represents an immutable structure as a json-encoded string."

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value, default=util.convert_to_builtin_type)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value, object_hook=util.dict_to_object)
        return value