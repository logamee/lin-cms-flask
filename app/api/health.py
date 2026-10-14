"""
存活探针（liveness probe）
~~~~~~~~

供容器编排、反向代理与监控轮询使用：不进入 OpenAPI 文档，不需要认证，
也不受业务接口限流影响（限流器默认无限流规则）。
"""

from importlib.metadata import PackageNotFoundError, version

from flask import Blueprint, jsonify

health_api = Blueprint("health", __name__)

try:
    _VERSION = version("app")
except PackageNotFoundError:  # 未以包形式安装（如直接以源码运行）时兜底
    _VERSION = "0.0.0+unknown"


@health_api.get("/health")
def health():
    return jsonify(status="ok", version=_VERSION)
