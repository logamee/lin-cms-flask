"""
register api to admin blueprint
~~~~~~~~~
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from flask import Blueprint


def create_cms():
    cms = Blueprint("cms", __name__)
    from app.api.cms.admin import admin_api
    from app.api.cms.file import file_api
    from app.api.cms.log import log_api
    from app.api.cms.user import user_api

    cms.register_blueprint(admin_api, url_prefix="/admin")
    cms.register_blueprint(user_api, url_prefix="/user")
    cms.register_blueprint(log_api, url_prefix="/log")
    cms.register_blueprint(file_api, url_prefix="/file")
    return cms
