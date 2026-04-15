"""core module of Lin.
 ~~~~~~~~~
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from typing import Any, Callable, Dict, List, Optional, Type, Union

from flask import Blueprint, Flask
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import DatabaseError

from .db import db
from .encoder import JSONEncoder, auto_response
from .exception import APIException, HTTPException, InternalServerError, ParameterError
from .jwt import jwt
from .manager import Manager
from .syslogger import SysLogger
from .utils import permission_meta_infos


def _flatten_pydantic_errors(exc: PydanticValidationError) -> str:
    errors = []
    for error in exc.errors():
        loc = error.get("loc", ())
        field = ".".join(str(item) for item in loc) if loc else "value"
        errors.append(f"{field} {error['msg']}")
    return " and ".join(errors)


class Lin(object):
    def __init__(
        self,
        app: Optional[Flask] = None,  # flask app , default None
        group_model: Optional[Any] = None,  # group model, default None
        user_model: Optional[Any] = None,  # user model, default None
        identity_model: Optional[Any] = None,  # user identity model,default None
        permission_model: Optional[Any] = None,  # permission model, default None
        group_permission_model: Optional[Any] = None,  # group permission 多对多关联模型
        user_group_model: Optional[Any] = None,  # user group 多对多关联模型
        jsonencoder: Optional[Type[JSONEncoder]] = None,  # 序列化器
        sync_permissions: bool = True,  # create db table if not exist and sync permissions, default True
        mount: bool = True,  # 是否挂载默认的蓝图, default True
        handle: bool = True,  # 是否使用全局异常处理, default True
        syslogger: bool = True,  # 是否使用自定义系统运行日志，default True
        **kwargs: Any,  # 保留配置项
    ):
        self.app: Optional[Flask] = app
        if app is not None:
            self.init_app(
                app,
                group_model,
                user_model,
                identity_model,
                permission_model,
                group_permission_model,
                user_group_model,
                jsonencoder,
                sync_permissions,
                mount,
                handle,
                syslogger,
            )

    def init_app(
        self,
        app: Flask,
        group_model: Optional[Any] = None,
        user_model: Optional[Any] = None,
        identity_model: Optional[Any] = None,
        permission_model: Optional[Any] = None,
        group_permission_model: Optional[Any] = None,
        user_group_model: Optional[Any] = None,
        jsonencoder: Optional[Type[JSONEncoder]] = None,
        sync_permissions: bool = True,
        mount: bool = True,
        handle: bool = True,
        syslogger: bool = True,
    ) -> None:
        # load default lin db model if None
        if not group_model:
            from .model import Group

            group_model = Group
        if not user_model:
            from .model import User

            self.user_model = User
        if not permission_model:
            from .model import Permission

            permission_model = Permission
        if not group_permission_model:
            from .model import GroupPermission

            group_permission_model = GroupPermission
        if not user_group_model:
            from .model import UserGroup

            user_group_model = UserGroup
        if not identity_model:
            from .model import UserIdentity

            identity_model = UserIdentity
        # 默认蓝图的前缀
        app.config.setdefault("BP_URL_PREFIX", "/plugin")
        # 文件上传配置未指定时的默认值
        app.config.setdefault(
            "FILE",
            {
                "STORE_DIR": "assets",
                "SINGLE_LIMIT": 1024 * 1024 * 2,
                "TOTAL_LIMIT": 1024 * 1024 * 20,
                "NUMS": 10,
                "INCLUDE": set(["jpg", "png", "jpeg"]),
                "EXCLUDE": set([]),
            },
        )
        self.jsonencoder = jsonencoder
        self.enable_auto_jsonify(app)
        self.app = app
        # 初始化 manager
        self.manager: Manager = Manager(
            app.config.get("PLUGIN_PATH", dict()),
            group_model=group_model,
            user_model=user_model,
            identity_model=identity_model,
            permission_model=permission_model,
            group_permission_model=group_permission_model,
            user_group_model=user_group_model,
        )
        self.app.extensions["manager"] = self.manager
        db.init_app(app)
        jwt.init_app(app)
        mount and self.mount(app)
        sync_permissions and self.sync_permissions(app)
        handle and self.handle_error(app)
        syslogger and SysLogger(app)

    def sync_permissions(self, app: Flask) -> None:
        # 挂载后才能获取代码中的权限
        # 多进程/线程下可能同时写入相同数据，由权限表联合唯一约束限制
        try:
            with app.app_context():
                self.manager.sync_permissions()
        except DatabaseError:
            pass

    def mount(self, app: Flask) -> None:
        # 加载默认插件路由
        bp = Blueprint("plugin", __name__)
        # 加载插件的路由
        for plugin in self.manager.plugins.values():
            if len(plugin.controllers.values()) > 1:
                for controller in plugin.controllers.values():
                    controller.register(bp, url_prefix="/" + plugin.name)
            else:
                for controller in plugin.controllers.values():
                    controller.register(bp)
        app.register_blueprint(bp, url_prefix=app.config.get("BP_URL_PREFIX"))
        for ep, func in app.view_functions.items():
            info = permission_meta_infos.get(func.__name__ + str(func.__hash__()), None)
            if info:
                self.manager.ep_meta.setdefault(ep, info)

    def handle_error(self, app: Flask) -> None:
        @app.errorhandler(Exception)
        def handler(e: Exception) -> Any:
            if isinstance(e, APIException):
                return e
            if isinstance(e, PydanticValidationError):
                return ParameterError(_flatten_pydantic_errors(e))
            if isinstance(e, HTTPException):
                code = e.code
                message = e.description
                message_code = 20000
                return APIException(message_code, message).set_code(code)
            else:
                if not app.config["DEBUG"]:
                    import traceback

                    app.logger.error(traceback.format_exc())
                    return InternalServerError()
                else:
                    raise e

    def enable_auto_jsonify(self, app: Flask) -> None:
        # app.json_encoder = self.jsonencoder or JSONEncoder
        app.json = self.jsonencoder(app) if self.jsonencoder else JSONEncoder(app)
        app.make_response = auto_response(app.make_response)
