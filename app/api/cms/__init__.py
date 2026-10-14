"""
register api to admin blueprint
~~~~~~~~~
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from flask import Blueprint


def register_jwt_blocklist() -> None:
    """已吊销令牌查询：flask-jwt-extended 每次校验令牌时回调。"""
    from app.api.cms.model.token_blocklist import TokenBlocklist
    from app.lin.jwt import jwt as jwt_manager

    @jwt_manager.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header: dict, jwt_payload: dict) -> bool:
        jti = jwt_payload.get("jti") or ""
        return bool(jti) and TokenBlocklist.is_revoked(jti)


def create_cms() -> Blueprint:
    cms = Blueprint("cms", __name__)
    from app.api.cms.admin import admin_api
    from app.api.cms.file import file_api
    from app.api.cms.log import log_api
    from app.api.cms.user import user_api

    register_jwt_blocklist()
    cms.register_blueprint(admin_api, url_prefix="/admin")
    cms.register_blueprint(user_api, url_prefix="/user")
    cms.register_blueprint(log_api, url_prefix="/log")
    cms.register_blueprint(file_api, url_prefix="/file")
    return cms
