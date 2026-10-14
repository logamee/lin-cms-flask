from typing import Annotated, List, Optional

from pydantic import EmailStr, Field, TypeAdapter, ValidationInfo, field_validator

from app.lin import BaseModel, ParameterError

# 统一密码策略：6-22 位（保持老用户习惯，无复杂度要求）
PasswordStr = Annotated[str, Field(min_length=6, max_length=22)]

EMAIL_ADAPTER = TypeAdapter(EmailStr)


class EmailSchema(BaseModel):
    email: Optional[str] = Field(None, description="用户邮箱")

    @field_validator("email")
    @classmethod
    def check_email(cls, value: Optional[str]) -> str:
        return str(EMAIL_ADAPTER.validate_python(value)) if value else ""


class ResetPasswordSchema(BaseModel):
    new_password: PasswordStr = Field(description="新密码")
    confirm_password: PasswordStr = Field(description="确认密码")

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, value: str, info: ValidationInfo) -> str:
        if value != info.data["new_password"]:
            raise ParameterError("两次输入的密码不一致，请输入相同的密码")
        return value


class GroupIdListSchema(BaseModel):
    group_ids: List[int] = Field(description="用户组ID列表")

    @field_validator("group_ids")
    @classmethod
    def check_group_id(cls, value: List[int]) -> List[int]:
        if any(group_id <= 0 for group_id in value):
            raise ParameterError("用户组ID必须大于0")
        return value
