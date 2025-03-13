from typing import Any, List

from flask import g
from pydantic import Field

from app.lin import BaseModel

datetime_regex = "^((([1-9][0-9][0-9][0-9]-(0[13578]|1[02])-(0[1-9]|[12][0-9]|3[01]))|(20[0-3][0-9]-(0[2469]|11)-(0[1-9]|[12][0-9]|30))) (20|21|22|23|[0-1][0-9]):[0-5][0-9]:[0-5][0-9])$"


class BasePageSchema(BaseModel):
    page: int
    count: int
    total: int
    total_page: int
    items: List[Any]


class QueryPageSchema(BaseModel):
    count: int = Field(5, gt=0, lt=16, description="0 < count < 16")
    page: int = 0

    @staticmethod
    def offset_handler(req, resp, req_validation_error, instance):
        g.offset = req.context.query.count * req.context.query.page
