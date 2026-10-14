"""
:copyright: © 2021 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from typing import Dict

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from spectree import SecurityScheme
from spectree.models import SecuritySchemeData

from app.lin import SpecTree

# 限流器：认证类接口在 user.py 中按路由单独加装饰器；默认不限流
# 存储后端由配置 RATELIMIT_STORAGE_URI 控制（生产多 worker 应配置 redis:// 等共享存储）
limiter = Limiter(key_func=get_remote_address, default_limits=[])
api = SpecTree(
    backend_name="flask",
    # OpenAPI对所有接口描述默认返回一个参数错误, http_status_code为400。
    validation_error_status=400,
    annotations=True,
    security_schemes=[
        SecurityScheme(
            name="AuthorizationBearer",
            data=SecuritySchemeData(type="http", scheme="bearer"),  # type: ignore[arg-type]
        ),
    ],
    # swaggerUI中所有接口默认允许传递Headers的AuthorizationToken字段
    # 不需要在每个api.validate(security=...)中指定它
    # 但所有接口都会显示一把小锁
    # SECURITY={"AuthorizationBearer": []},
)

AuthorizationBearerSecurity: Dict[str, list] = {"AuthorizationBearer": []}
