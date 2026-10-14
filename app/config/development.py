import os

from .base import BaseConfig

# 开发环境默认放行本地前端 dev server；可用环境变量 CORS_ORIGINS 覆盖（逗号分隔）
DEV_CORS_DEFAULTS = "http://localhost:5173,http://127.0.0.1:5173"


class DevelopmentConfig(BaseConfig):
    """
    开发环境配置:默认放行本地前端开发服务器跨域访问，无需任何配置
    """

    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", DEV_CORS_DEFAULTS).split(",") if o.strip()]
