import re
from datetime import datetime
from typing import List, Optional

from pydantic import Field, validator

from app.lin import BaseModel
from app.schema import BasePageSchema, QueryPageSchema, datetime_regex


class UsernameListSchema(BaseModel):
    items: List[str]


class LogQuerySearchSchema(QueryPageSchema):
    keyword: Optional[str] = None
    name: Optional[str] = None
    start: Optional[str] = Field(None, description="YY-MM-DD HH:MM:SS")
    end: Optional[str] = Field(None, description="YY-MM-DD HH:MM:SS")

    @validator("start", "end")
    def datetime_match(cls, v):
        if re.match(datetime_regex, v):
            return v
        raise ValueError("时间格式有误")


class LogSchema(BaseModel):
    message: str
    user_id: int
    username: str
    status_code: int
    method: str
    path: str
    permission: str
    time: datetime = Field(alias="create_time")


class LogPageSchema(BasePageSchema):
    items: List[LogSchema]
