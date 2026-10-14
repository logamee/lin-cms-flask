"""
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import logging
import os
from typing import Any

from dotenv import load_dotenv
from flask import Flask

from app.util.common import basedir

VALID_ENVS = ("development", "production", "test")

logger = logging.getLogger(__name__)


def register_blueprints(app: Flask) -> None:
    from app.api.cms import create_cms
    from app.api.v1 import create_v1

    app.register_blueprint(create_v1(), url_prefix="/v1")
    app.register_blueprint(create_cms(), url_prefix="/cms")


def register_cli(app: Flask) -> None:
    from app.cli import plugin_cli

    app.cli.add_command(plugin_cli)


def register_migrate(app: Flask) -> None:
    from flask_migrate import Migrate

    from app.lin import db

    # render_as_batch：SQLite 的 ALTER 支持残缺，批处理模式保证改列/约束可迁移
    Migrate(app, db, render_as_batch=True)


def register_api(app: Flask) -> None:
    from app.api import api

    api.register(app)
    # 生产环境屏蔽 OpenAPI 文档页面与规范导出（校验功能不受影响）
    if os.environ.get("FLASK_ENV") == "production":

        def _doc_not_found() -> Any:
            from werkzeug.exceptions import NotFound

            raise NotFound("API 文档未开放")

        for endpoint in list(app.view_functions):
            if endpoint.startswith("openapi_"):
                app.view_functions[endpoint] = _doc_not_found


def apply_cors(app: Flask) -> None:
    from flask_cors import CORS

    # 仅放行配置白名单内的来源；生产默认收紧为空（同源部署）
    CORS(app, origins=app.config.get("CORS_ORIGINS", []))


def apply_rate_limit(app: Flask) -> None:
    from app.api import limiter

    # flask-limiter 自动读取 RATELIMIT_* 配置（含 RATELIMIT_STORAGE_URI）
    limiter.init_app(app)

    from app.lin.exception import APIException

    @app.errorhandler(429)
    def rate_limit_exceeded(_: Any) -> Any:
        return APIException(10220, "请求过于频繁，请稍后再试").set_code(429)


def apply_proxy_fix(app: Flask) -> None:
    """反向代理场景还原真实客户端 IP（限流 key 依赖），由配置 PROXY_FIX 开启。"""
    if app.config.get("PROXY_FIX"):
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # type: ignore[method-assign]


def load_app_config(app: Flask) -> None:
    """
    根据指定配置环境自动加载对应环境变量和配置类到app config
    """
    env = os.environ.get("FLASK_ENV")
    if env not in VALID_ENVS:
        raise RuntimeError(f"FLASK_ENV 必须是 {VALID_ENVS} 之一，当前为 {env!r}；请在 .flaskenv 或环境变量中设置")
    # 读取 .env
    load_dotenv(os.path.join(basedir, f".{env}.env"))
    # 读取配置类
    app.config.from_object(f"app.config.{env}.{env.capitalize()}Config")
    secret = app.config.get("SECRET_KEY")
    if not secret or str(secret).lstrip().startswith("<run:"):
        raise RuntimeError(
            f"SECRET_KEY 未设置或仍是模板占位符：请编辑 .{env}.env 填入真实密钥"
            f"（生成：python -c 'import secrets; print(secrets.token_hex(32))'）"
        )
    if env == "production":
        uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if not uri:
            raise RuntimeError("生产环境必须显式配置 SQLALCHEMY_DATABASE_URI")
        if uri.startswith("sqlite"):
            logger.warning("生产环境正在使用 SQLite，仅建议开发/演示用途；生产请使用 MySQL/PostgreSQL")
        if str(app.config.get("RATELIMIT_STORAGE_URI", "")).startswith("memory"):
            logger.warning("生产环境限流使用内存存储：多 worker 下限额按进程各自计数，请配置 redis:// 共享存储")


def set_global_config(**kwargs: Any) -> None:
    from app.lin import global_config

    # 获取config_*参数对象并挂载到脱离上下文的global config
    for k, v in kwargs.items():
        if k.startswith("config_"):
            global_config[k[7:]] = v


def create_app(register_all: bool = True, **kwargs: Any) -> Flask:
    # 全局配置优先生效
    set_global_config(**kwargs)

    app = Flask(__name__, static_folder=os.path.join(basedir, "assets"))
    # http wsgi server托管启动需指定读取环境配置
    # Load .flaskenv file
    flaskenv_path = os.path.join(basedir, ".flaskenv")
    if os.path.exists(flaskenv_path):
        load_dotenv(flaskenv_path)
    else:
        print(f"Warning: {flaskenv_path} not found")
    load_app_config(app)
    if register_all:
        from app.lin import Lin

        register_blueprints(app)
        register_api(app)
        apply_cors(app)
        apply_rate_limit(app)
        apply_proxy_fix(app)
        Lin(app, **kwargs)
        register_migrate(app)
        register_cli(app)
    return app
