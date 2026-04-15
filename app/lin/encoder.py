from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Iterable

from flask import json, jsonify
from flask.json.provider import DefaultJSONProvider
from flask.wrappers import Response
from pydantic import BaseModel as PydanticBaseModel

from .db import Record, RecordCollection
from .exception import APIException


class JSONEncoder(DefaultJSONProvider):
    ensure_ascii = False

    def default(self, o):
        if isinstance(o, PydanticBaseModel):
            if hasattr(o, "root") and o.root.__class__.__name__ in ("list", "int", "set", "tuple"):
                return o.root
            if hasattr(o, "__root__") and o.__root__.__class__.__name__ in ("list", "int", "set", "tuple"):
                return o.__root__
            return o.model_dump()
        if isinstance(o, (int, float, list)):
            return o
        if isinstance(o, (set, tuple)):
            return list(o)
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
            return float(o)
        if isinstance(o, Iterable):
            return list(o)
        if isinstance(o, complex):
            return f"{o.real}+{o.imag}j"
        if hasattr(o, "keys") and hasattr(o, "__getitem__"):
            return dict(o)
        return super().default(o)


def auto_response(func):
    def make_lin_response(o):
        if isinstance(o, Response):
            return func(o)
        if isinstance(o, tuple):
            if isinstance(o[0], Response):
                return func(o)
            if not isinstance(o[0], str):
                oc = list(o)
                oc[0] = json.dumps(o[0])
                o = tuple(oc)
            return func(o)
        if not isinstance(o, str) and (
            isinstance(o, (RecordCollection, Record, PydanticBaseModel, Iterable))
            or (hasattr(o, "keys") and hasattr(o, "__getitem__"))
            or isinstance(o, (int, float, list, set, complex, Decimal, Enum))
        ):
            o = jsonify(o)

        return func(o)

    return make_lin_response
