"""
Logger of Lin
~~~~~~~~~

logger模块，用户行为日志记录器

:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import re
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

from flask import Response, request
from flask_jwt_extended import get_current_user
from sqlalchemy import Column, Integer, String, func

from .db import db
from .interface import InfoCrud
from .manager import manager

F = TypeVar("F", bound=Callable[..., Any])


class Log(InfoCrud):
    __tablename__ = "lin_log"

    id = Column(Integer(), primary_key=True)
    message = Column(String(450), comment="日志信息")
    user_id = Column(Integer(), nullable=False, comment="用户id")
    username = Column(String(24), comment="用户当时的昵称")
    status_code = Column(Integer(), comment="请求的http返回码")
    method = Column(String(20), comment="请求方法")
    path = Column(String(50), comment="请求路径")
    permission = Column(String(100), comment="访问哪个权限")

    @property
    def time(self) -> int:
        return int(round(self.create_time.timestamp() * 1000))

    @classmethod
    def select_by_conditions(cls, **kwargs: Any) -> List["Log"]:
        """
        根据条件筛选日志，条件的可以是所有表内字段，以及start, end 时间段，keyword模糊匹配message字段
        """
        conditions: Dict[str, Any] = dict()
        # 过滤 传入参数
        avaliable_keys = [c for c in vars(Log).keys() if not c.startswith("_")] + [
            "start",
            "end",
            "keyword",
        ]
        for key, value in kwargs.items():
            if key in avaliable_keys:
                conditions[key] = value
        query = cls.query.filter_by(soft=True)
        # 搜索特殊字段
        if conditions.get("start"):
            query = query.filter(cls.create_time > conditions.get("start"))
            del conditions["start"]
        if conditions.get("end"):
            query = query.filter(cls.create_time < conditions.get("end"))
            del conditions["end"]
        if conditions.get("keyword"):
            query = query.filter(cls.message.like("%{keyword}%".format(keyword=conditions.get("keyword"))))
            del conditions["keyword"]
        # 搜索表内字段
        query = query.filter_by(**conditions).group_by(cls.create_time).order_by(cls.create_time.desc())
        logs = query.all()
        return logs

    @classmethod
    def get_usernames(cls) -> List[str]:
        result = (
            db.session.query(cls.username)
            .filter(cls.is_deleted == False)
            .group_by(cls.username)
            .having(func.count(cls.username) > 0)
        )
        # [(‘张三',),('李四',),...] -> ['张三','李四',...]
        usernames = [x[0] for x in result.all()]
        return usernames

    @staticmethod
    def create_log(**kwargs: Any) -> "Log":
        log = Log()
        for key in kwargs.keys():
            if hasattr(log, key):
                setattr(log, key, kwargs[key])
        db.session.add(log)
        if kwargs.get("commit") is True:
            db.session.commit()
        return log


REG_XP = r"[{](.*?)[}]"
OBJECTS = ["user", "response", "request"]


class Logger(object):
    """
    用户行为日志记录器
    """

    # message template
    template: Optional[str] = None

    def __init__(self, template: Optional[str] = None):
        if template:
            self.template: str = template
        elif self.template is None:
            raise Exception("template must not be None!")
        self.message: str = ""
        self.response: Optional[Response] = None
        self.user: Optional[Any] = None

    def __call__(self, func: F) -> F:
        @wraps(func)
        def wrap(*args: Any, **kwargs: Any) -> Any:
            response: Response = func(*args, **kwargs)
            self.response = response
            self.user = get_current_user()
            if not self.user:
                raise Exception("Logger must be used in the login state")
            self.message = self._parse_template()
            self.write_log()
            return response

        return cast(F, wrap)

    def write_log(self) -> None:
        info = manager.find_info_by_ep(request.endpoint)
        permission = info.name if info is not None else ""
        status_code = getattr(self.response, "status_code", None)
        if status_code is None:
            status_code = getattr(self.response, "code", None)
        if status_code is None:
            status_code = 0
        Log.create_log(
            message=self.message,
            user_id=self.user.id,
            username=self.user.username,
            status_code=status_code,
            method=request.method,
            path=request.path,
            permission=permission,
            commit=True,
        )

    # 解析自定义模板
    def _parse_template(self) -> str:
        message = self.template
        total = re.findall(REG_XP, message)
        for it in total:
            assert "." in it, "%s中必须包含 . ,且为一个" % it
            i = it.rindex(".")
            obj = it[:i]
            assert obj in OBJECTS, "%s只能为user,response,request中的一个" % obj
            prop = it[i + 1 :]
            if obj == "user":
                item = getattr(self.user, prop, "")
            elif obj == "response":
                item = getattr(self.response, prop, "")
            else:
                item = getattr(request, prop, "")
            message = message.replace("{%s}" % it, str(item))
        return message
