import re
from typing import List, Optional

from pydantic import Field, ValidationInfo, field_validator

from app.lin import BaseModel, ParameterError

from . import EmailSchema, GroupIdListSchema, ResetPasswordSchema


class LoginSchema(BaseModel):
    username: str = Field(description="用户名")
    password: str = Field(description="密码")
    captcha: Optional[str] = Field(None, description="验证码")


class LoginTokenSchema(BaseModel):
    access_token: str = Field(description="access_token")
    refresh_token: str = Field(description="refresh_token")


class CaptchaSchema(BaseModel):
    image: str = Field("", description="验证码图片base64编码")
    tag: str = Field("", description="验证码标记码")


class PermissionNameSchema(BaseModel):
    name: str = Field(description="权限名称")


class PermissionModuleSchema(BaseModel):
    module: List[PermissionNameSchema] = Field(description="权限模块")


class UserBaseInfoSchema(EmailSchema):
    nickname: Optional[str] = Field(None, description="用户昵称", min_length=2, max_length=10)
    avatar: Optional[str] = Field(None, description="头像url")


class UserSchema(UserBaseInfoSchema):
    id: int = Field(description="用户id")
    username: str = Field(description="用户名")


class UserPermissionSchema(UserSchema):
    admin: bool = Field(description="是否是管理员")
    permissions: List[PermissionModuleSchema] = Field(description="用户权限")


class ChangePasswordSchema(ResetPasswordSchema):
    old_password: str = Field(description="旧密码")


class UserRegisterSchema(GroupIdListSchema, EmailSchema):
    username: str = Field(description="用户名", min_length=2, max_length=10)
    password: str = Field(description="密码", min_length=6, max_length=22)
    confirm_password: str = Field(description="确认密码", min_length=6, max_length=22)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data["password"]:
            raise ParameterError("两次输入的密码不一致，请输入相同的密码")
        return value

    @field_validator("username")
    @classmethod
    def check_username(cls, value: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{2,10}$", value):
            raise ParameterError("用户名只能由字母、数字、下划线组成，且长度为2-10位")
        return value
