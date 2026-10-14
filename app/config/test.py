from .base import BaseConfig


class TestConfig(BaseConfig):
    """
    测试环境配置:内存数据库,不落盘日志
    """

    # 测试专用固定密钥,不用于任何真实环境；≥32 字节以满足 PyJWT 对 HS256 的密钥长度建议
    SECRET_KEY = "lin-cms-test-only-secret-key-0123456789abcdef"

    SQLALCHEMY_DATABASE_URI = "sqlite://"

    SQLALCHEMY_ENGINE_OPTIONS = {}

    # 测试中关闭限流，避免用例触发 429
    RATELIMIT_ENABLED = False

    LOG = {
        "LEVEL": "WARNING",
        "DIR": "logs",
        "SIZE_LIMIT": 1024 * 1024 * 5,
        "REQUEST_LOG": False,
        "FILE": False,
    }
