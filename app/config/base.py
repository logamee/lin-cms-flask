"""
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import os
from datetime import timedelta


class BaseConfig(object):
    """
    基础配置
    """

    # 先读 env 环境变量中的配置

    # 指定加密KEY（必须通过环境变量或 .{env}.env 提供，禁止内置缺省值）
    SECRET_KEY = os.getenv("SECRET_KEY")

    # 指定访问api服务的url, 用于文件上传
    # SITE_DOMAIN="https://lincms.example.com"

    # 指定数据库
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:////" + os.getcwd() + os.path.sep + "lincms.db",
    )

    # 屏蔽 sql alchemy 的 FSADeprecationWarning
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # flask-sqlalchemy 引擎配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        # sqlite 不支持pool_size, 其他数据库按需配置
        # "pool_size": 10,
        # 每次请求前 pre-ping一下数据库, 防止db gone away
        "pool_pre_ping": True,
        # 小于等于数据库连接主动回收时间
        "pool_recycle": 600,
    }

    # 令牌配置
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    # 刷新令牌必须显式设置有效期（框架默认 30 天过长且无法吊销）
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # CORS 来源白名单；默认空=仅同源，开发环境在 DevelopmentConfig 中放开本地前端
    CORS_ORIGINS: list = []

    # 登录验证码
    LOGIN_CAPTCHA = False

    # 限流存储：开发默认内存；生产多 worker 部署必须配置 redis:// 等共享存储
    RATELIMIT_STORAGE_URI = "memory://"

    # 反向代理场景开启后，依据 X-Forwarded-For/Proto 还原真实客户端 IP（限流按真实 IP 计数）
    PROXY_FIX = False

    # 默认文件上传配置
    FILE = {
        "STORE_DIR": "assets",
        "SINGLE_LIMIT": 1024 * 1024 * 2,
        "TOTAL_LIMIT": 1024 * 1024 * 20,
        "NUMS": 10,
        "INCLUDE": set(["jpg", "png", "jpeg"]),
        "EXCLUDE": set([]),
    }

    # 运行日志
    LOG = {
        "LEVEL": "DEBUG",
        "DIR": "logs",
        "SIZE_LIMIT": 1024 * 1024 * 5,
        "REQUEST_LOG": True,
        "FILE": True,
    }

    # 分页配置
    COUNT_DEFAULT = 10
    PAGE_DEFAULT = 0

    # 兼容中文
    JSON_AS_ASCII = False
