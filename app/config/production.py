import os

from .base import BaseConfig


class ProductionConfig(BaseConfig):
    """
    生产环境配置:关闭调试,收紧日志级别
    """

    DEBUG = False

    LOG = {
        **BaseConfig.LOG,
        "LEVEL": "INFO",
    }

    # 登录验证码默认关闭（前端登录页未接入验证码）；暴力破解防护由限流承担
    LOGIN_CAPTCHA = False

    # 限流共享存储：多 worker 部署务必通过环境变量指向 redis:// 等共享存储
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
