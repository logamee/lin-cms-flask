from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Iterable

from flask import json, jsonify
from flask.json.provider import DefaultJSONProvider
from flask.wrappers import Response

from .apidoc import BaseModel
from .db import Record, RecordCollection
from .exception import APIException


class JSONEncoder(DefaultJSONProvider):
    ensure_ascii = False

    def default(self, o):
        if isinstance(o, BaseModel):
            if hasattr(o, "__root__") and o.__root__.__class__.__name__ in (
                "list",
                "int",
                "set",
                "tuple",
            ):
                return o.__root__
            return o.dict()
        if isinstance(o, (int, float, list, set, tuple)):
            return json.dumps(o, cls=JSONEncoder)
        if isinstance(o, bytes):
            return o.decode("utf8")
        if isinstance(o, datetime):
            return o.strftime("%Y-%m-%dT%H:%M:%SZ")
        if isinstance(o, date):
            return o.strftime("%Y-%m-%d")
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, (RecordCollection, Record)):
            return o.as_dict()
        if isinstance(o, Decimal):
            return json.dumps(o, use_decimal=True)
        if isinstance(o, Iterable):
            return list(o)
        if isinstance(o, complex):
            return f"{o.real}+{o.imag}j"
        if hasattr(o, "keys") and hasattr(o, "__getitem__"):
            return dict(o)
        return JSONEncoder.default(self, o)


def auto_response(func):
    def make_lin_response(o):
        if not isinstance(o, str) and (
            isinstance(o, (RecordCollection, Record, BaseModel, Iterable))
            or (hasattr(o, "keys") and hasattr(o, "__getitem__"))
            or isinstance(o, (int, float, list, set, complex, Decimal, Enum))
        ):
            o = jsonify(o)
        elif isinstance(o, tuple) and not isinstance(o[0], (Response, str)):
            oc = list(o)
            oc[0] = json.dumps(o[0])
            o = tuple(oc)

        return func(o)

    return make_lin_response
