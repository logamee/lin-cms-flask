"""
admin apis
~~~~~~~~~
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import math
from typing import Any, Dict

from flask import Blueprint
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
)
def get_admin_users(query: QueryPageWithGroupIdSchema) -> Dict[str, Any]:
    """
    查询所有用户及其所属组信息
    """
    # 获取 符合查询 条件的 分组id
    query_group_id = db.session.query(manager.group_model.id).filter(
        manager.group_model.level != GroupLevelEnum.ROOT.value
    )
    if query.group_id:
        query_group_id = query_group_id.filter(manager.group_model.id == query.group_id)
    # 获取符合条件的用户总量
    total = (
        db.session.query(func.count(func.distinct(manager.user_group_model.user_id)))
        .filter(manager.user_group_model.group_id.in_(query_group_id))
        .scalar()
    )
    # 获取当前分页条件下查询到的非Root组的用户id
    # 部分数据库不支持子语句 in limit，故先物化为列表
    current_page_user_ids = [
        row[0]
        for row in db.session.query(manager.user_group_model.user_id)
        .filter(manager.user_group_model.group_id.in_(query_group_id))
        .group_by(manager.user_group_model.user_id)
        .offset(query.offset)
        .limit(query.count)
        .all()
    ]
    total_page = math.ceil(total / query.count) if total else 0
    if not current_page_user_ids:
        return {"items": [], "count": query.count, "page": query.page, "total": total, "total_page": total_page}
    # 一次 join 拿到 (用户, 分组) 对，替代原先 3 条查询 + O(users×groups×relations) 三重循环拼装
    user_group_pairs = (
        db.session.query(manager.user_model, manager.group_model)
        .join(manager.user_group_model, manager.user_group_model.user_id == manager.user_model.id)
        .join(manager.group_model, manager.group_model.id == manager.user_group_model.group_id)
        .filter(manager.user_model.id.in_(current_page_user_ids))
        .all()
    )
    users_by_id = {user.id: user for user, _ in user_group_pairs}
    groups_by_user: Dict[int, list] = {uid: [] for uid in current_page_user_ids}
    for user, group in user_group_pairs:
        groups_by_user[user.id].append(group)
    items = [
        AdminUserSchema(
            email=users_by_id[uid].email,
            groups=groups_by_user[uid],
            id=uid,
            username=users_by_id[uid].username,
        )
        for uid in current_page_user_ids
        if uid in users_by_id
    ]

    return {
        "items": items,
        "count": query.count,
        "page": query.page,
        "total": total,
        "total_page": total_page,
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
        user.reset_password(json.new_password)

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
def delete_user(uid: int):
    """
    删除用户
    """
    user = manager.user_model.get(id=uid)
    if user is None:
        raise NotFound("用户不存在")
    groups = manager.group_model.select_by_user_id(uid)
    # 超级管理员分组的用户仅有一个分组；无分组用户不属于 Root，直接放行删除
    if groups and groups[0].level == GroupLevelEnum.ROOT.value:
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
    if user.email != json.email:
        exists = manager.user_model.get(email=json.email)
        if exists:
            raise ParameterError("邮箱已被注册，请重新输入邮箱")
    with db.auto_commit():
        user.email = json.email
        manager.replace_user_groups(user.id, json.group_ids)
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
def get_group(gid: int) -> dict:
    """
    获取一个分组及其权限
    """
    group = manager.group_model.get(id=gid, one=True, soft=False)
    if group is None:
        raise NotFound("分组不存在")
    permissions = manager.permission_model.select_by_group_id(gid)
    resp = dict(group)
    resp["permissions"] = [dict(p) for p in permissions]
    return resp


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
    exists = manager.group_model.get(name=json.name)
    if exists:
        raise Forbidden("分组已存在，不可创建同名分组")
    with db.auto_commit():
        group = manager.group_model.create(
            name=json.name,
            info=json.info,
        )
        db.session.flush()
        group_permission_list = list()
        for permission_id in json.permission_ids:
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
    exists.update(name=json.name, info=json.info, commit=True)
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
        for permission_id in json.permission_ids:
            one = manager.group_permission_model.get(group_id=json.group_id, permission_id=permission_id)
            if not one:
                manager.group_permission_model.create(
                    group_id=json.group_id,
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
            manager.group_permission_model.permission_id.in_(json.permission_ids),
            manager.group_permission_model.group_id == json.group_id,
        ).delete(synchronize_session=False)

    raise Success("删除权限成功")
