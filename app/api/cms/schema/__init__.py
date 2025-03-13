from typing import List, Optional

from pydantic import EmailStr, Field, validator

from app.lin import BaseModel, ParameterError


class EmailSchema(BaseModel):
    email: Optional[str] = Field(description="用户邮箱")

    @validator("email")
    def check_email(cls, v, values, **kwargs):
        return EmailStr.validate(v) if v else ""


class ResetPasswordSchema(BaseModel):
    new_password: str = Field(description="新密码", min_length=6, max_length=22)
    confirm_password: str = Field(description="确认密码", min_length=6, max_length=22)

    @validator("confirm_password")
    def passwords_match(cls, v, values, **kwargs):
        if v != values["new_password"]:
            raise ParameterError("两次输入的密码不一致，请输入相同的密码")
        return v


class GroupIdListSchema(BaseModel):
    group_ids: List[int] = Field(description="用户组ID列表")

    @validator("group_ids", each_item=True)
    def check_group_id(cls, v, values, **kwargs):
        if v <= 0:
            raise ParameterError("用户组ID必须大于0")
        return v
