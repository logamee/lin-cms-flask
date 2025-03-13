# coding: utf-8
"""
Some model interfaces of Lin
~~~~~~~~~

interface means you must implement the necessary methods and inherit properties.

:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, SmallInteger, String, func, text

from .db import MixinJSONSerializer, db
from .enums import GroupLevelEnum
from .utils import camel2line


# 基础的crud model
class BaseCrud(db.Model, MixinJSONSerializer):
    __abstract__ = True

    def __init__(self):
        name: str = self.__class__.__name__
        if not hasattr(self, "__tablename__"):
            self.__tablename__ = camel2line(name)

    def _set_fields(self):
        self._exclude = []

    def set_attrs(self, attrs_dict):
        for key, value in attrs_dict.items():
            if hasattr(self, key) and key != "id":
                setattr(self, key, value)

    # 硬删除
    def delete(self, commit=False):
        db.session.delete(self)
        if commit:
            db.session.commit()

    # 查
    @classmethod
    def get(cls, start=None, count=None, one=True, **kwargs):
        if one:
            return cls.query.filter().filter_by(**kwargs).first()
        return cls.query.filter().filter_by(**kwargs).offset(start).limit(count).all()

    # 增
    @classmethod
    def create(cls, **kwargs):
        one = cls()
        for key in kwargs.keys():
            if hasattr(one, key):
                setattr(one, key, kwargs[key])
        db.session.add(one)
        if kwargs.get("commit") is True:
            db.session.commit()
        return one

    def update(self, **kwargs):
        for key in kwargs.keys():
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
        db.session.add(self)
        if kwargs.get("commit") is True:
            db.session.commit()
        return self


# 提供软删除，及创建时间，更新时间信息的crud model


class InfoCrud(db.Model, MixinJSONSerializer):
    __abstract__ = True
    create_time = Column(DateTime(timezone=True), server_default=func.now())
    update_time = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    delete_time = Column(DateTime(timezone=True))
    is_deleted = Column(Boolean, nullable=False, default=False)

    def _set_fields(self):
        self._exclude = ["delete_time", "is_deleted"]

    def set_attrs(self, attrs_dict):
        for key, value in attrs_dict.items():
            if hasattr(self, key) and key != "id":
                setattr(self, key, value)

    # 软删除
    def delete(self, commit=False):
        self.delete_time = datetime.now()
        self.is_deleted = True
        db.session.add(self)
        # 提交会话
        if commit:
            db.session.commit()

    # 硬删除
    def hard_delete(self, commit=False):
        db.session.delete(self)
        if commit:
            db.session.commit()

    # 查
    @classmethod
    def get(cls, start=None, count=None, one=True, **kwargs):
        # 应用软删除，必须带有delete_time
        if kwargs.get("is_deleted") is None:
            kwargs["is_deleted"] = False
        if one:
            return cls.query.filter().filter_by(**kwargs).first()
        return cls.query.filter().filter_by(**kwargs).offset(start).limit(count).all()

    # 增
    @classmethod
    def create(cls, **kwargs):
        one = cls()
        for key in kwargs.keys():
            # if key == 'from':
            #     setattr(one, '_from', kwargs[key])
            # if key == 'parts':
            #     setattr(one, '_parts', kwargs[key])
            if hasattr(one, key):
                setattr(one, key, kwargs[key])
        db.session.add(one)
        if kwargs.get("commit") is True:
            db.session.commit()
        return one

    def update(self, **kwargs):
        for key in kwargs.keys():
            # if key == 'from':
            #     setattr(self, '_from', kwargs[key])
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
        db.session.add(self)
        if kwargs.get("commit") is True:
            db.session.commit()
        return self


class GroupInterface(InfoCrud):
    __tablename__ = "lin_group"
    __table_args__ = (Index("name_del", "name", "is_deleted", unique=True),)

    id = Column(Integer(), primary_key=True)
    name = Column(String(60), nullable=False, comment="分组名称，例如：搬砖者")
    info = Column(String(255), comment="分组信息：例如：搬砖的人")
    level = Column(
        SmallInteger(),
        nullable=False,
        server_default=text(str(GroupLevelEnum.USER.value)),
        comment="分组级别 1：ROOT 2：GUEST 3：USER （ROOT、GUEST Level 对应分组均唯一存在)",
    )

    @classmethod
    def count_by_id(cls, id) -> int:
        raise NotImplementedError()


class GroupPermissionInterface(BaseCrud):
    __tablename__ = "lin_group_permission"
    __table_args__ = (Index("group_id_permission_id", "group_id", "permission_id"),)

    id = Column(Integer(), primary_key=True)
    group_id = Column(Integer(), nullable=False, comment="分组id")
    permission_id = Column(Integer(), nullable=False, comment="权限id")


class PermissionInterface(InfoCrud):
    __tablename__ = "lin_permission"
    __table_args__ = (Index("name_module", "name", "module", unique=True),)

    id = Column(Integer(), primary_key=True)
    name = Column(String(60), nullable=False, comment="权限名称，例如：访问首页")
    module = Column(String(50), nullable=False, comment="权限所属模块，例如：人员管理")
    mount = Column(Boolean, nullable=False, comment="是否为挂载权限")

    def __hash__(self):
        raise NotImplementedError()

    def __eq__(self, other):
        raise NotImplementedError()


class UserInterface(InfoCrud):
    __tablename__ = "lin_user"
    __table_args__ = (
        Index("username_del", "username", "is_deleted", unique=True),
        Index("email_del", "email", "is_deleted", unique=True),
    )

    id = Column(Integer(), primary_key=True)
    username = Column(String(24), nullable=False, comment="用户名，唯一")
    nickname = Column(String(24), comment="用户昵称")
    _avatar = Column("avatar", String(500), comment="头像url")
    email = Column(String(100), comment="邮箱")

    @property
    def avatar(self) -> str:
        raise NotImplementedError()

    @classmethod
    def count_by_id(cls, uid) -> int:
        raise NotImplementedError()

    @staticmethod
    def count_by_id_and_group_name(user_id, group_name) -> int:
        raise NotImplementedError()

    @property
    def is_admin(self) -> bool:
        raise NotImplementedError()

    @property
    def is_active(self) -> bool:
        raise NotImplementedError()

    @property
    def password(self) -> str:
        raise NotImplementedError()

    @password.setter
    def password(self, raw) -> None:
        raise NotImplementedError()

    def check_password(self, raw):
        raise NotImplementedError()

    @classmethod
    def verify(cls, username, password) -> InfoCrud:
        raise NotImplementedError()


class UserGroupInterface(BaseCrud):
    __tablename__ = "lin_user_group"
    __table_args__ = (Index("user_id_group_id", "user_id", "group_id"),)

    id = Column(Integer(), primary_key=True)
    user_id = Column(Integer(), nullable=False, comment="用户id")
    group_id = Column(Integer(), nullable=False, comment="分组id")


class UserIdentityInterface(InfoCrud):
    __tablename__ = "lin_user_identity"

    id = Column(Integer(), primary_key=True)
    user_id = Column(Integer(), nullable=False, comment="用户id")
    identity_type = Column(String(100), nullable=False, comment="认证类型")
    identifier = Column(String(100), comment="标识")
    credential = Column(String(255), comment="凭证")


class LinViewModel:
    # 提供自动序列化功能
    def keys(self):
        return self.__dict__.keys()

    def __getitem__(self, key):
        return getattr(self, key)
