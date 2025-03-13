"""
admin apis
~~~~~~~~~
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import math

from flask import Blueprint, g
from sqlalchemy import func

from app.api import AuthorizationBearerSecurity, api
from app.api.cms.schema import ResetPasswordSchema
from app.api.cms.schema.admin import (
    AdminGroupListSchema,
    AdminGroupPermissionSchema,
    AdminUserPageSchema,
    AdminUserSchema,
    CreateGroupSchema,
    GroupBaseSchema,
    GroupIdWithPermissionIdListSchema,
    QueryPageWithGroupIdSchema,
    UpdateUserInfoSchema,
)
from app.lin import (
    DocResponse,
    Forbidden,
    GroupLevelEnum,
    Logger,
    NotFound,
    ParameterError,
    Success,
    admin_required,
    db,
    manager,
    permission_meta,
)

admin_api = Blueprint("admin", __name__)


@admin_api.route("/permission")
@permission_meta(name="查询所有可分配的权限", module="管理员", mount=False)
@admin_required
@api.validate(
    tags=["管理员"],
    security=[AuthorizationBearerSecurity],
)
def permissions():
    """
    查询所有可分配的权限
    """
    return manager.get_ep_infos()


@admin_api.route("/users")
@permission_meta(name="查询所有用户", module="管理员", mount=False)
@admin_required
@api.validate(
    tags=["管理员"],
    security=[AuthorizationBearerSecurity],
    resp=DocResponse(r=AdminUserPageSchema),
    before=QueryPageWithGroupIdSchema.offset_handler,
)
def get_admin_users(query: QueryPageWithGroupIdSchema):
    """
    查询所有用户及其所属组信息
    """
    # 获取 符合查询 条件的 分组id
    query_group_id = db.session.query(manager.group_model.id).filter(
        manager.group_model.level != GroupLevelEnum.ROOT.value
    )
    if g.group_id:
        query_group_id = query_group_id.filter(manager.group_model.id == g.group_id)
    # 获取符合条件的用户总量
    total = (
        db.session.query(func.count(func.distinct(manager.user_group_model.user_id)))
        .filter(manager.user_group_model.group_id.in_(query_group_id))
        .scalar()
    )
    # 获取当前分页条件下查询到的非Root组的用户id
    query_current_page_user_ids = (
        db.session.query(manager.user_group_model.user_id)
        .filter(manager.user_group_model.group_id.in_(query_group_id))
        .group_by(manager.user_group_model.user_id)
        .offset(g.offset)
        .limit(g.count)
    )
    # 部分数据库不支持子语句 in limit
    current_page_user_ids = [user_id[0] for user_id in query_current_page_user_ids.all()]
    # 获取用户的基本信息
    current_page_users = manager.user_model.query.filter(manager.user_model.id.in_(current_page_user_ids)).all()
    # 获取需要填充分组的基本信息
    current_groups = manager.group_model.query.filter(
        manager.group_model.id.in_(
            db.session.query(manager.user_group_model.group_id)
            .filter(manager.user_group_model.user_id.in_(current_page_user_ids))
            .group_by(manager.user_group_model.group_id)
        )
    ).all()
    # 获取这些用户和分组的多对多关联关系
    user_group_relations = (
        db.session.query(manager.user_group_model)
        .filter(manager.user_group_model.user_id.in_(current_page_user_ids))
        .all()
    )
    # 根据关联关系拼装的items数据结构
    items = [
        AdminUserSchema(email=user.email, groups=list(), id=user.id, username=user.username)
        for user in current_page_users
    ]
    # 填充分组信息
    for item in items:
        for ug in user_group_relations:
            if ug.user_id == item.id:
                for group in current_groups:
                    if ug.group_id == group.id:
                        item.groups.append(group)

    return {
        "items": items,
        "count": g.count,
        "page": g.page,
        "total": total,
        "total_page": math.ceil(total / g.count),
    }


@admin_api.route("/user/<int:uid>/password", methods=["PUT"])
@permission_meta(name="修改用户密码", module="管理员", mount=False)
@admin_required
@api.validate(
    tags=["管理员"],
    resp=DocResponse(NotFound("用户不存在"), Success("密码修改成功")),
    security=[AuthorizationBearerSecurity],
)
def change_user_password(uid: int, json: ResetPasswordSchema):
    """
    修改用户密码
    """

    user = manager.find_user(id=uid)
    if not user:
        raise NotFound("用户不存在")

    with db.auto_commit():
        user.reset_password(g.new_password)

    raise Success("密码修改成功")


@admin_api.route("/user/<int:uid>", methods=["DELETE"])
@permission_meta(name="删除用户", module="管理员", mount=False)
@Logger(template="管理员删除了一个用户")
@admin_required
@api.validate(
    tags=["管理员"],
    security=[AuthorizationBearerSecurity],
    resp=DocResponse(NotFound("用户不存在"), Success("删除成功"), Forbidden("用户不能删除")),
)
def delete_user(uid):
    """
    删除用户
    """
    user = manager.user_model.get(id=uid)
    if user is None:
        raise NotFound("用户不存在")
    groups = manager.group_model.select_by_user_id(uid)
    # 超级管理员分组的用户仅有一个分组
    if groups[0].level == GroupLevelEnum.ROOT.value:
        raise Forbidden("无法删除此用户")
    with db.auto_commit():
        manager.user_group_model.query.filter_by(user_id=uid).delete(synchronize_session=False)
        user.hard_delete()
    raise Success("操作成功")


@admin_api.route("/user/<int:uid>", methods=["PUT"])
@permission_meta(name="管理员更新用户信息", module="管理员", mount=False)
@admin_required
@api.validate(
    tags=["管理员"],
    security=[AuthorizationBearerSecurity],
    resp=DocResponse(
        NotFound("用户不存在"),
        Success("更新成功"),
        ParameterError("邮箱已被注册，请重新输入邮箱"),
    ),
)
def update_user(uid: int, json: UpdateUserInfoSchema):
    """
    更新用户信息
    """
    user = manager.user_model.get(id=uid)
    if user is None:
        raise NotFound("用户不存在")
    if user.email != g.email:
        exists = manager.user_model.get(email=g.email)
        if exists:
            raise ParameterError("邮箱已被注册，请重新输入邮箱")
    with db.auto_commit():
        user.email = g.email
        group_ids = g.group_ids
        # 清空原来的所有关联关系
        manager.user_group_model.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        # 根据传入分组ids 新增关联记录
        user_group_list = list()
        # 如果没传分组数据，则将其设定为 guest 分组
        if not group_ids:
            group_ids = [manager.group_model.get(level=GroupLevelEnum.GUEST.value).id]
        for group_id in group_ids:
            user_group = manager.user_group_model()
            user_group.user_id = user.id
            user_group.group_id = group_id
            user_group_list.append(user_group)
        db.session.add_all(user_group_list)
    raise Success("操作成功")


@admin_api.route("/group/all")
@permission_meta(name="查询所有分组", module="管理员", mount=False)
@admin_required
@api.validate(
    tags=["管理员"],
    security=[AuthorizationBearerSecurity],
    resp=DocResponse(NotFound("不存在任何分组"), r=AdminGroupListSchema),
)
def get_all_group():
    """
    获取所有分组
    """
    groups = manager.group_model.query.filter(
        manager.group_model.is_deleted == False,
        manager.group_model.level != GroupLevelEnum.ROOT.value,
    ).all()
    if groups is None:
        raise NotFound("不存在任何分组")
    return groups


@admin_api.route("/group/<int:gid>")
@permission_meta(name="查询一个分组及其权限", module="管理员", mount=False)
@admin_required
@api.validate(
    tags=["管理员"],
    security=[AuthorizationBearerSecurity],
    resp=DocResponse(NotFound("分组不存在"), r=AdminGroupPermissionSchema),
)
def get_group(gid):
    """
    获取一个分组及其权限
    """
    group = manager.group_model.get(id=gid, one=True, soft=False)
    if group is None:
        raise NotFound("分组不存在")
    permissions = manager.permission_model.select_by_group_id(gid)
    setattr(group, "permissions", permissions)
    group._fields.append("permissions")
    return group


@admin_api.route("/group", methods=["POST"])
@permission_meta(name="新建分组", module="管理员", mount=False)
@Logger(template="管理员新建了一个分组")  # 记录日志
@admin_required
@api.validate(
    tags=["管理员"],
    security=[AuthorizationBearerSecurity],
    resp=DocResponse(
        ParameterError("用户组已存在, 不可创建同名分组"),
        Success("新建用户组成功"),
    ),
)
def create_group(json: CreateGroupSchema):
    """
    新建分组
    """
    exists = manager.group_model.get(name=g.name)
    if exists:
        raise Forbidden("分组已存在，不可创建同名分组")
    with db.auto_commit():
        group = manager.group_model.create(
            name=g.name,
            info=g.info,
        )
        db.session.flush()
        group_permission_list = list()
        for permission_id in g.permission_ids:
            gp = manager.group_permission_model()
            gp.group_id = group.id
            gp.permission_id = permission_id
            group_permission_list.append(gp)
        db.session.add_all(group_permission_list)
    raise Success("新建分组成功")


@admin_api.route("/group/<int:gid>", methods=["PUT"])
@permission_meta(name="更新一个分组", module="管理员", mount=False)
@admin_required
@api.validate(
    tags=["管理员"],
    security=[AuthorizationBearerSecurity],
    resp=DocResponse(
        ParameterError("分组不存在,更新失败"),
        Success("更新分组成功"),
    ),
)
def update_group(gid, json: GroupBaseSchema):
    """
    更新一个分组基本信息
    """
    exists = manager.group_model.get(id=gid)
    if not exists:
        raise NotFound("分组不存在，更新失败")
    exists.update(name=g.name, info=g.info, commit=True)
    raise Success("更新成功")


@admin_api.route("/group/<int:gid>", methods=["DELETE"])
@permission_meta(name="删除一个分组", module="管理员", mount=False)
@Logger(template="管理员删除一个分组")  # 记录日志
@admin_required
@api.validate(
    tags=["管理员"],
    security=[AuthorizationBearerSecurity],
    resp=DocResponse(NotFound("分组不存在，删除失败"), Forbidden("分组不可删除"), Success("删除分组成功")),
)
def delete_group(gid):
    """
    删除一个分组
    """
    exist = manager.group_model.get(id=gid)
    if not exist:
        raise NotFound("分组不存在，删除失败")
    guest_group = manager.group_model.get(level=GroupLevelEnum.GUEST.value)
    root_group = manager.group_model.get(level=GroupLevelEnum.ROOT.value)
    if gid in (guest_group.id, root_group.id):
        raise Forbidden("不可删除此分组")
    if manager.user_model.select_page_by_group_id(gid, root_group.id):
        raise Forbidden("分组下存在用户，不可删除")
    with db.auto_commit():
        # 删除group id 对应的关联记录
        manager.group_permission_model.query.filter_by(group_id=gid).delete(synchronize_session=False)
        # 删除group
        exist.delete()
    raise Success("删除分组成功")


@admin_api.route("/permission/dispatch/batch", methods=["POST"])
@permission_meta(name="分配多个权限", module="管理员", mount=False)
@admin_required
@api.validate(
    tags=["管理员"],
    security=[AuthorizationBearerSecurity],
    resp=DocResponse(
        Success("添加权限成功"),
    ),
)
def dispatch_auths(json: GroupIdWithPermissionIdListSchema):
    """
    分配多个权限
    """
    with db.auto_commit():
        for permission_id in g.permission_ids:
            one = manager.group_permission_model.get(group_id=g.group_id, permission_id=permission_id)
            if not one:
                manager.group_permission_model.create(
                    group_id=g.group_id,
                    permission_id=permission_id,
                )
    raise Success("添加权限成功")


@admin_api.route("/permission/remove", methods=["POST"])
@permission_meta(name="删除多个权限", module="管理员", mount=False)
@admin_required
@api.validate(
    tags=["管理员"],
    resp=DocResponse(Success("删除权限成功")),
    security=[AuthorizationBearerSecurity],
)
def remove_auths(json: GroupIdWithPermissionIdListSchema):
    """
    删除多个权限
    """

    with db.auto_commit():
        db.session.query(manager.group_permission_model).filter(
            manager.group_permission_model.permission_id.in_(g.permission_ids),
            manager.group_permission_model.group_id == g.group_id,
        ).delete(synchronize_session=False)

    raise Success("删除权限成功")
