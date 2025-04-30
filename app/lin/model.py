import os

from flask import current_app
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from . import manager
from .db import db
from .enums import GroupLevelEnum
from .exception import NotFound, ParameterError, UnAuthentication
from .interface import (
    GroupInterface,
    GroupPermissionInterface,
    PermissionInterface,
    UserGroupInterface,
    UserIdentityInterface,
    UserInterface,
)


class Group(GroupInterface):
    @classmethod
    def count_by_id(cls, id) -> int:
        result = db.session.query(func.count(cls.id)).filter(cls.id == id, cls.is_deleted == False)
        count = result.scalar()
        return count


class GroupPermission(GroupPermissionInterface):
    pass


class Permission(PermissionInterface):
    def __hash__(self):
        return hash(self.name + self.module)

    def __eq__(self, other):
        if self.name == other.name and self.module == other.module:
            # 如果出现了复用同名权限，则要保证mount=True的权限生效
            self.mount = self.mount or other.mount
            return True
        else:
            return False


class User(UserInterface):
    @property
    def avatar(self):
        site_domain = current_app.config.get(
            "SITE_DOMAIN",
            "http://{host}:{port}".format(
                host=current_app.config.get("FLASK_RUN_HOST", "127.0.0.1"),
                port=current_app.config.get("FLASK_RUN_PORT", "5000"),
            ),
        )

        if self._avatar is not None:
            return site_domain + os.path.join(current_app.static_url_path, self._avatar)

    @classmethod
    def count_by_id(cls, uid) -> int:
        result = db.session.query(func.count(cls.id)).filter(cls.id == uid, cls.is_deleted == False)
        count = result.scalar()
        return count

    @staticmethod
    def count_by_id_and_group_name(user_id: int, group_name: str) -> int:
        stmt = (
            db.session.query(manager.group_model.id.label("group_id")).filter_by(soft=True, name=group_name).subquery()
        )
        result = db.session.query(func.count(manager.user_group_model.id)).filter(
            manager.user_group_model.user_id == user_id,
            manager.user_group_model.group_id == stmt.c.group_id,
        )
        count = result.scalar()
        return count

    @property
    def is_admin(self) -> bool:
        return manager.user_group_model.get(user_id=self.id).group_id == GroupLevelEnum.ROOT.value

    @property
    def is_active(self) -> bool:
        return True

    @property
    def password(self):
        return manager.identity_model.get(user_id=self.id).credential

    @password.setter
    def password(self, raw):
        user_identity = manager.identity_model.get(user_id=self.id)
        if user_identity:
            user_identity.credential = generate_password_hash(raw)
            user_identity.update(synchronize_session=False)
        else:
            user_identity = manager.identity_model()
            user_identity.user_id = self.id
            user_identity.identity_type = "USERNAME_PASSWORD"
            user_identity.identity = "root"
            user_identity.credential = generate_password_hash(raw)
            db.session.add(user_identity)

    def check_password(self, raw):
        return check_password_hash(self.password, raw)

    @classmethod
    def verify(cls, username, password):
        user = cls.query.filter_by(username=username).first()
        if user is None or user.is_deleted:
            raise NotFound("用户不存在")
        if not user.check_password(password):
            raise ParameterError("密码错误，请输入正确密码")
        if not user.is_active:
            raise UnAuthentication("您目前处于未激活状态，请联系超级管理员")
        return user


class UserGroup(UserGroupInterface):
    pass


class UserIdentity(UserIdentityInterface):
    pass
