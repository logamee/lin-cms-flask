import os
from typing import Optional

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
    def count_by_id(cls, id: int) -> int:
        result = db.session.query(func.count(cls.id)).filter(cls.id == id, cls.is_deleted == False)
        count = result.scalar()
        return count


class GroupPermission(GroupPermissionInterface):
    pass


class Permission(PermissionInterface):
    def __hash__(self) -> int:
        return hash(self.name + self.module)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Permission):
            return NotImplemented
        if self.name == other.name and self.module == other.module:
            # 如果出现了复用同名权限，则要保证mount=True的权限生效
            self.mount = self.mount or other.mount
            return True
        else:
            return False


class User(UserInterface):
    @property
    def avatar(self) -> Optional[str]:
        site_domain = current_app.config.get(
            "SITE_DOMAIN",
            "http://{host}:{port}".format(
                host=current_app.config.get("FLASK_RUN_HOST", "127.0.0.1"),
                port=current_app.config.get("FLASK_RUN_PORT", "5000"),
            ),
        )

        if self._avatar is not None:
            return site_domain + os.path.join(current_app.static_url_path or "", self._avatar)
        return None

    @classmethod
    def count_by_id(cls, uid: int) -> int:
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
    def password(self) -> str:
        user_identity = manager.identity_model.get(user_id=self.id)
        if user_identity:
            return user_identity.credential
        return ""  # 如果没有认证记录，返回空字符串

    @password.setter
    def password(self, raw: str) -> None:
        # 验证密码输入
        if not raw or len(raw.strip()) == 0:
            raise ParameterError("密码不能为空")
        if len(raw) < 6:
            raise ParameterError("密码长度不能少于6位")

        try:
            # 查找用户的身份认证记录
            user_identity = manager.identity_model.get(user_id=self.id)

            if user_identity:
                # 更新现有的认证记录
                user_identity.credential = generate_password_hash(raw)
                user_identity.update(synchronize_session=False)

            else:
                # 创建新的认证记录
                user_identity = manager.identity_model()
                user_identity.user_id = self.id
                user_identity.identity_type = "USERNAME_PASSWORD"  # 默认类型，可根据需要调整
                user_identity.identifier = self.username  # 使用用户的实际用户名
                user_identity.credential = generate_password_hash(raw)
                db.session.add(user_identity)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ParameterError(f"密码设置失败: {str(e)}")

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password, raw)

    @classmethod
    def verify(cls, username: str, password: str) -> "User":
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
