"""
user apis
~~~~~~~~~
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import json
from typing import Any

import jwt
from flask import Blueprint, current_app, request
from flask_jwt_extended import get_current_user, get_jwt_identity, verify_jwt_in_request
from flask_jwt_extended.exceptions import JWTExtendedException

from app.api import AuthorizationBearerSecurity, api, limiter
from app.api.cms.exception import RefreshFailed
from app.api.cms.schema.user import (
    CaptchaSchema,
    ChangePasswordSchema,
    LoginSchema,
    LoginTokenSchema,
    UserBaseInfoSchema,
    UserRegisterSchema,
    UserSchema,
)
from app.lin import (
    DocResponse,
    Duplicated,
    Failed,
    Log,
    Logger,
    NotFound,
    ParameterError,
    Success,
    admin_required,
    db,
    get_tokens,
    login_required,
    manager,
    permission_meta,
)
from app.util.captcha import CaptchaTool
from app.util.common import split_group

user_api = Blueprint("user", __name__)


@user_api.route("/register", methods=["POST"])
@limiter.limit("10 per hour")
@permission_meta(name="注册", module="用户", mount=False)
@Logger(template="管理员新建了一个用户")  # 记录日志
@admin_required
@api.validate(
    tags=["用户"],
    security=[AuthorizationBearerSecurity],
    resp=DocResponse(Success("用户创建成功"), Duplicated("字段重复，请重新输入")),
)
def register(json: UserRegisterSchema):
    """
    注册新用户
    """
    if manager.user_model.count_by_username(json.username) > 0:
        raise Duplicated("用户名重复，请重新输入")  # type: ignore
    if json.email and json.email.strip() != "":
        if manager.user_model.count_by_email(json.email) > 0:
            raise Duplicated("注册邮箱重复，请重新输入")  # type: ignore
    # create a user
    with db.auto_commit():
        user = manager.user_model()
        user.username = json.username
        if json.email and json.email.strip() != "":
            user.email = json.email
        db.session.add(user)
        db.session.flush()
        user.password = json.password
        # 未传分组时默认落入 Guest 分组（按级别解析 ID，而非硬编码）
        manager.replace_user_groups(user.id, json.group_ids)
    raise Success("用户创建成功")  # type: ignore


@user_api.route("/login", methods=["POST"])
@limiter.limit("20 per minute")
@api.validate(resp=DocResponse(Failed("验证码校验失败"), r=LoginTokenSchema), tags=["用户"])
def login(json: LoginSchema):
    """
    用户登录
    """
    # 校对验证码
    if current_app.config.get("LOGIN_CAPTCHA"):
        tag = request.headers.get("tag", "")
        secret_key = current_app.config.get("SECRET_KEY", "")
        try:
            code = jwt.decode(tag, secret_key, algorithms=["HS256"]).get("code")
        except jwt.PyJWTError:
            raise Failed("验证码校验失败")  # type: ignore
        if json.captcha != code:
            raise Failed("验证码校验失败")  # type: ignore

    user = manager.user_model.verify(json.username, json.password)
    # 用户未登录，此处不能用装饰器记录日志
    Log.create_log(
        message=f"{user.username}登录成功获取了令牌",
        user_id=user.id,
        username=user.username,
        status_code=200,
        method="post",
        path="/cms/user/login",
        permission="",
        commit=True,
    )
    access_token, refresh_token = get_tokens(user)
    return LoginTokenSchema(access_token=access_token, refresh_token=refresh_token)


@user_api.route("", methods=["PUT"])
@permission_meta(name="用户更新信息", module="用户", mount=False)
@login_required
@api.validate(
    tags=["用户"],
    security=[AuthorizationBearerSecurity],
    resp=DocResponse(Success("用户信息更新成功"), ParameterError("邮箱已被注册，请重新输入邮箱")),
)
def update(json: UserBaseInfoSchema):
    """
    更新用户信息
    """
    user = get_current_user()

    if json.email and user.email != json.email:
        exists = manager.user_model.get(email=json.email)
        if exists:
            raise ParameterError("邮箱已被注册，请重新输入邮箱")
    with db.auto_commit():
        if json.email:
            user.email = json.email
        if json.nickname:
            user.nickname = json.nickname
        if json.avatar:
            user._avatar = json.avatar
    raise Success("用户信息更新成功")


@user_api.route("/change_password", methods=["PUT"])
@permission_meta(name="修改密码", module="用户", mount=False)
@Logger(template="{user.username}修改了自己的密码")  # 记录日志
@login_required
@api.validate(
    tags=["用户"],
    security=[AuthorizationBearerSecurity],
    resp=DocResponse(Success("密码修改成功"), Failed("密码修改失败")),
)
def change_password(json: ChangePasswordSchema):
    """
    修改密码
    """
    user = get_current_user()
    ok = user.change_password(json.old_password, json.new_password)
    if ok:
        db.session.commit()
        raise Success("密码修改成功")  # type: ignore
    raise Failed("修改密码失败")  # type: ignore


@user_api.route("/information")
@permission_meta(name="查询自己信息", module="用户", mount=False)
@login_required
@api.validate(
    tags=["用户"],
    security=[AuthorizationBearerSecurity],
    resp=DocResponse(r=UserSchema),
)
def get_information():
    """
    获取用户信息
    """
    current_user = get_current_user()
    return current_user


@user_api.route("/refresh")
@limiter.limit("20 per minute")
@permission_meta(name="刷新令牌", module="用户", mount=False)
@api.validate(
    resp=DocResponse(RefreshFailed, NotFound("refresh_token未被识别"), r=LoginTokenSchema),
    tags=["用户"],
)
def refresh():
    """
    刷新令牌
    """
    try:
        verify_jwt_in_request(refresh=True)
    except (JWTExtendedException, jwt.PyJWTError):
        raise RefreshFailed

    raw_identity = get_jwt_identity()
    try:
        identity: Any = json.loads(raw_identity) if isinstance(raw_identity, str) else raw_identity
    except (TypeError, ValueError):
        raise RefreshFailed
    uid = identity.get("uid") if isinstance(identity, dict) else None
    user = manager.find_user(id=uid) if uid is not None else None
    if user is None or not user.is_active:
        raise RefreshFailed
    # 令牌版本校验：改密后旧 refresh 一并失效
    if identity.get("ver", 0) != getattr(user, "token_version", 0):
        raise RefreshFailed
    access_token, refresh_token = get_tokens(user)
    return LoginTokenSchema(access_token=access_token, refresh_token=refresh_token)


@user_api.route("/logout", methods=["POST"])
@permission_meta(name="退出登录", module="用户", mount=False)
@limiter.limit("20 per minute")
@login_required
@api.validate(
    tags=["用户"],
    security=[AuthorizationBearerSecurity],
    resp=DocResponse(Success("退出成功")),
)
def logout():
    """
    退出登录：吊销当前 access 令牌；请求体可选携带 refresh_token 一并吊销
    """
    from datetime import datetime

    from flask_jwt_extended import get_jwt

    from app.api.cms.model.token_blocklist import TokenBlocklist

    claims = get_jwt()
    uid = claims.get("uid") or 0
    TokenBlocklist.revoke(
        jti=claims["jti"],
        expires_at=datetime.fromtimestamp(claims["exp"]),
        user_id=uid,
    )
    # 可选：请求体携带 refresh_token 时一并吊销（无效令牌直接忽略）
    body = request.get_json(silent=True) or {}
    raw_refresh = body.get("refresh_token") if isinstance(body, dict) else None
    if raw_refresh:
        try:
            rclaims = jwt.decode(raw_refresh, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            TokenBlocklist.revoke(
                jti=rclaims["jti"],
                expires_at=datetime.fromtimestamp(rclaims["exp"]),
                user_id=uid,
            )
        except (jwt.PyJWTError, KeyError, TypeError, ValueError):
            pass
    raise Success("退出成功")  # type: ignore


@user_api.route("/permissions")
@permission_meta(name="查询自己拥有的权限", module="用户", mount=False)
@login_required
@api.validate(
    tags=["用户"],
    security=[AuthorizationBearerSecurity],
    # resp=DocResponse(r=UserPermissionSchema), # 当前数据接口无法使用OpenAPI表示
)
def get_allowed_apis() -> dict:
    """
    获取用户拥有的权限
    """
    user = get_current_user()
    groups = manager.group_model.select_by_user_id(user.id)
    group_ids = [group.id for group in groups]
    _permissions = manager.permission_model.select_by_group_ids(group_ids)
    permission_list = [{"permission": permission.name, "module": permission.module} for permission in _permissions]
    res = split_group(permission_list, "module")
    resp = dict(user)
    resp["admin"] = user.is_admin
    resp["permissions"] = res
    return resp


@user_api.route("/captcha", methods=["GET", "POST"])
@limiter.limit("30 per minute")
@api.validate(
    resp=DocResponse(r=CaptchaSchema),
    tags=["用户"],
)
def get_captcha():
    """
    获取图形验证码
    """
    if not current_app.config.get("LOGIN_CAPTCHA"):
        return CaptchaSchema()  # type: ignore
    image, code = CaptchaTool().get_verify_code()
    secret_key = current_app.config.get("SECRET_KEY")
    tag = jwt.encode({"code": code}, secret_key, algorithm="HS256")
    return {"tag": tag, "image": image}
