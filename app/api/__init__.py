"""
:copyright: © 2021 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from typing import Dict

from spectree import SecurityScheme

from app.lin import SpecTree

api = SpecTree(
    backend_name="flask",
    title="Lin-CMS-Flask",
    mode="strict",
    version="0.5.0",
    # OpenAPI对所有接口描述默认返回一个参数错误, http_status_code为400。
    validation_error_status=400,
    annotations=True,
    security_schemes=[
        SecurityScheme(
            name="AuthorizationBearer",
            data={
                "type": "http",
                "scheme": "bearer",
            },
        ),
    ],
    # swaggerUI中所有接口默认允许传递Headers的AuthorizationToken字段
    # 不需要在每个api.validate(security=...)中指定它
    # 但所有接口都会显示一把小锁
    # SECURITY={"AuthorizationBearer": []},
)

AuthorizationBearerSecurity: Dict = {"AuthorizationBearer": []}
