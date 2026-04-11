"""
jwt(Json Web Token) of Lin
~~~~~~~~~

jwt implement for Lin.

:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import json
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Union

from flask import request
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, get_current_user
from flask_jwt_extended.view_decorators import jwt_required

from .exception import NotFound, TokenExpired, TokenInvalid, UnAuthentication
from .manager import manager

__all__ = ["login_required", "admin_required", "group_required"]

SCOPE = "lin"
jwt = JWTManager()


F = TypeVar("F", bound=Callable[..., Any])


def _normalize_identity(raw_identity: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    identity = raw_identity
    for _ in range(2):
        if isinstance(identity, str):
            try:
                identity = json.loads(identity)
            except (json.JSONDecodeError, TypeError):
                raise UnAuthentication()  # type: ignore

    if not isinstance(identity, dict):
        raise UnAuthentication()  # type: ignore
    return identity


def admin_required(fn: F) -> F:
    @wraps(fn)
    @jwt_required()
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        current_user = get_current_user()
        if not current_user.is_admin:
            raise UnAuthentication("只有超级管理员可操作")  # type: ignore
        return fn(*args, **kwargs)

    return wrapper


def group_required(fn: F) -> F:
    @wraps(fn)
    @jwt_required()
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        current_user = get_current_user()
        # check current user is active or not
        # 判断当前用户是否为激活状态
        _check_is_active(current_user)

        # not admin
        if not current_user.is_admin:

            group_ids = manager.find_group_ids_by_user_id(current_user.id)
            if group_ids is None:
                raise UnAuthentication("您还不属于任何分组，请联系超级管理员获得权限")  # type: ignore

            if not manager.is_user_allowed(group_ids):
                raise UnAuthentication("权限不够，请联系超级管理员获得权限")  # type: ignore
            else:
                return fn(*args, **kwargs)
        else:
            return fn(*args, **kwargs)

    return wrapper


def login_required(fn: F) -> F:
    @wraps(fn)
    @jwt_required()
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        _check_is_active(current_user=get_current_user())
        return fn(*args, **kwargs)

    return wrapper


@jwt.user_lookup_loader
def user_loader_callback(jwt_header: Any, jwt_payload: Dict[str, Any]) -> Any:
    raw_identity = jwt_payload.get("sub")
    if not raw_identity:
        raise UnAuthentication()  # type: ignore

    identity = _normalize_identity(raw_identity)
    if identity["scope"] != SCOPE:
        raise UnAuthentication()  # type: ignore
    if identity.get("remote_addr") and identity["remote_addr"] != request.remote_addr:
        raise UnAuthentication()  # type: ignore
    # token is granted , user must be exit
    # 如果token已经被颁发，则该用户一定存在
    user = manager.find_user(id=identity["uid"])
    if user is None:
        raise NotFound("用户不存在")  # type: ignore
    return user


@jwt.user_identity_loader
def user_identity_callback(identity: Union[str, Dict[str, Any]]) -> str:
    """将identity字典转换为字符串作为JWT的subject"""
    return json.dumps(_normalize_identity(identity))


@jwt.expired_token_loader
def expired_loader_callback(t: Any, identity: Dict[str, Any]) -> TokenExpired:
    return TokenExpired(10051)  # type: ignore


@jwt.invalid_token_loader
def invalid_loader_callback(e: str) -> TokenInvalid:
    return TokenInvalid(10041)  # type: ignore


@jwt.unauthorized_loader
def unauthorized_loader_callback(e: str) -> UnAuthentication:
    return UnAuthentication("认证失败，请检查请求头或者重新登录")  # type: ignore


@jwt.additional_claims_loader
def add_claims_to_access_token(identity: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    identity_data = _normalize_identity(identity)
    return {
        "uid": identity_data["uid"],
        "scope": identity_data["scope"],
        "remote_addr": identity_data["remote_addr"] if "remote_addr" in identity_data.keys() else None,
    }


def verify_access_token() -> None:
    __verify_token("access")


def verify_refresh_token() -> None:
    __verify_token("refresh")


def __verify_token(request_type: str) -> None:
    1 / 0
    from flask import request
    from flask_jwt_extended.config import config
    from flask_jwt_extended.utils import verify_token_claims
    from flask_jwt_extended.view_decorators import _decode_jwt_from_cookies as decode

    try:
        from flask import _app_ctx_stack as ctx_stack
    except ImportError:
        from flask import _request_ctx_stack as ctx_stack

    if request.method not in config.exempt_methods:
        jwt_data = decode(request_type=request_type)
        ctx_stack.top.jwt = jwt_data
        verify_token_claims(jwt_data)


def _check_is_active(current_user: Any) -> None:
    if not current_user.is_active:
        raise UnAuthentication("您目前处于未激活状态，请联系超级管理员")


def get_tokens(user: Any, verify_remote_addr: bool = False) -> Tuple[str, str]:
    identity: Dict[str, Union[int, Optional[str]]] = {"uid": user.id, "scope": SCOPE}
    if verify_remote_addr:
        identity["remote_addr"] = request.remote_addr
    access_token = create_access_token(identity)
    refresh_token = create_refresh_token(identity)
    return access_token, refresh_token
