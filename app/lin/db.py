"""
db of Lin
~~~~~~~~~
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from contextlib import contextmanager
from typing import Any, Optional

from flask import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, inspect, orm
from sqlalchemy.orm import Query as BaseQuery
from sqlalchemy.orm import declarative_base, declared_attr, has_inherited_table

from .exception import NotFound
from .utils import camel2line

Base = declarative_base()


class MixinJSONSerializer:

    @declared_attr.directive
    def __tablename__(cls) -> Optional[str]:
        name: Optional[str] = None
        if not has_inherited_table(cls):
            name = camel2line(cls.__name__)
        return name

    @orm.reconstructor
    def init_on_load(self) -> None:
        self._fields: list[str] = []
        self._exclude: list[str] = []
        self._set_fields()
        self.__prune_fields()

    def _set_fields(self) -> None:
        pass

    def __prune_fields(self) -> None:
        mapper = inspect(self.__class__)
        columns = mapper.columns if mapper is not None else []
        if not self._fields:
            all_columns = {column.name for column in columns}
            self._fields = list(all_columns - set(self._exclude))

    def hide(self, *args: str) -> "MixinJSONSerializer":
        for key in args:
            if key in self._fields:
                self._fields.remove(key)
        return self

    def keys(self) -> list[str]:
        if not hasattr(self, "_fields"):
            self.init_on_load()
        return self._fields

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class Database(SQLAlchemy):
    @contextmanager
    def auto_commit(self):
        try:
            yield
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e


class Query(BaseQuery):
    def __init__(self, entities, session=None) -> None:
        super().__init__(entities, session=session)

    def filter_by(self, soft: bool = False, **kwargs: Any) -> "Query":
        """增强filter_by支持软删除"""
        if soft:
            kwargs["is_deleted"] = False
        return super().filter_by(**kwargs)

    def get_or_404(self, ident: Any) -> Any:
        """根据ID获取记录或抛出404"""
        rv = self.get(ident)
        if not rv:
            raise NotFound()
        return rv

    def first_or_404(self) -> Any:
        """获取第一条记录或抛出404"""
        rv = self.first()
        if not rv:
            raise NotFound()
        return rv


class Model(Base):
    __abstract__ = True

    def __repr__(self):
        detail = json.dumps({k: v for k, v in self.__dict__.items() if not k.startswith("_")})
        identity: Any = inspect(self).identity
        if identity is None:
            pk = "\n(transient {0} {1})\n".format(id(self), detail)
        else:
            pk = ",".join(to_str(value) for value in identity)
        return "\n<{0} {1} {2}>\n".format(type(self).__name__, pk, detail)


def get_total_nums(cls, is_soft=False, **kwargs):
    nums = db.session.query(func.count(cls.id))
    nums = (
        nums.filter(cls.is_deleted == False).filter_by(**kwargs).scalar() if is_soft else nums.filter().scalar()
    )  # noqa: E712
    if nums:
        return nums
    else:
        return 0


def to_str(x, charset="utf8", errors="strict"):
    if x is None or isinstance(x, str):
        return x

    if isinstance(x, bytes):
        return x.decode(charset, errors)

    return str(x)


db = Database(query_class=Query, model_class=Model)
