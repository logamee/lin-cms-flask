from typing import List, Optional

from pydantic import Field, RootModel, field_validator

from app.lin import BaseModel, ParameterError
from app.schema import BasePageSchema, QueryPageSchema

from . import EmailSchema, GroupIdListSchema


class AdminGroupSchema(BaseModel):
    id: int = Field(description="用户组ID")
    info: str = Field(description="用户组信息")
    name: str = Field(description="用户组名称")


class AdminGroupListSchema(RootModel[List[AdminGroupSchema]]):
    pass


class AdminUserSchema(EmailSchema):
    id: int = Field(description="用户ID")
    username: str = Field(description="用户名")
    groups: List[AdminGroupSchema] = Field(description="用户组列表")


class QueryPageWithGroupIdSchema(QueryPageSchema):
    group_id: Optional[int] = Field(None, description="用户ID")


class AdminUserPageSchema(BasePageSchema):
    items: List[AdminUserSchema]


class UpdateUserInfoSchema(GroupIdListSchema, EmailSchema):
    pass


class PermissionSchema(BaseModel):
    id: int = Field(description="权限ID")
    name: str = Field(description="权限名称")
    module: str = Field(description="权限所属模块")
    mount: bool = Field(description="是否为挂载权限")


class AdminGroupPermissionSchema(AdminGroupSchema):
    permissions: List[PermissionSchema]


class AdminGroupPermissionPageSchema(BasePageSchema):
    items: List[AdminGroupPermissionSchema]


class GroupBaseSchema(BaseModel):
    name: str = Field(description="用户组名称")
    info: Optional[str] = Field(None, description="用户组信息")


class CreateGroupSchema(GroupBaseSchema):
    permission_ids: List[int] = Field(description="权限ID列表")

    @field_validator("permission_ids")
    @classmethod
    def check_permission_id(cls, value: List[int]) -> List[int]:
        if any(permission_id <= 0 for permission_id in value):
            raise ParameterError("权限ID必须大于0")
        return value


class GroupIdWithPermissionIdListSchema(BaseModel):
    group_id: int = Field(description="用户组ID")
    permission_ids: List[int] = Field(description="权限ID列表")

    @field_validator("permission_ids")
    @classmethod
    def check_permission_id(cls, value: List[int]) -> List[int]:
        if any(permission_id <= 0 for permission_id in value):
            raise ParameterError("权限ID必须大于0")
        return value
