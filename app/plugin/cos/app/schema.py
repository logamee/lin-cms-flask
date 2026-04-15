from typing import List

from pydantic import RootModel

from app.lin import BaseModel


class CosOutSchema(BaseModel):
    id: int
    file_name: str
    file_key: str
    url: str


class CosOutSchemaList(RootModel[List[CosOutSchema]]):
    pass
