"""
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import os

from dotenv import load_dotenv
from flask import Flask

from app.util.common import basedir


def register_blueprints(app):
    from app.api.cms import create_cms
    from app.api.v1 import create_v1

    app.register_blueprint(create_v1(), url_prefix="/v1")
    app.register_blueprint(create_cms(), url_prefix="/cms")


def register_cli(app):
    from app.cli import db_cli, plugin_cli

    app.cli.add_command(db_cli)
    app.cli.add_command(plugin_cli)


def register_api(app):
    from app.api import api

    api.register(app)


def apply_cors(app):
    from flask_cors import CORS

    CORS(app)


def load_app_config(app):
    """
    根据指定配置环境自动加载对应环境变量和配置类到app config
    """
    # 根据传入环境加载对应配置
    env = os.environ.get("FLASK_ENV")
    # 读取 .env
    load_dotenv(os.path.join(basedir, ".{env}.env").format(env=env))
    # 读取配置类
    app.config.from_object("app.config.{env}.{Env}Config".format(env=env, Env=env.capitalize()))


def set_global_config(**kwargs):
    from app.lin import global_config

    # 获取config_*参数对象并挂载到脱离上下文的global config
    for k, v in kwargs.items():
        if k.startswith("config_"):
            global_config[k[7:]] = v


def create_app(register_all=True, **kwargs):
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
        Lin(app, **kwargs)
        register_cli(app)
    return app
