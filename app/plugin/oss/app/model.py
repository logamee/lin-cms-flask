from sqlalchemy import Column, Integer, String

from app.lin import BaseCrud


class OSS(BaseCrud):
    __tablename__ = "oss"

    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False)
