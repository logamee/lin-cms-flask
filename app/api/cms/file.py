"""
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from flask import Blueprint, request

from app.api import AuthorizationBearerSecurity, api
from app.extension.file.local_uploader import LocalUploader
from app.lin import login_required

file_api = Blueprint("file", __name__)


@file_api.route("", methods=["POST"])
@login_required
@api.validate(
    tags=["文件"],
    security=[AuthorizationBearerSecurity],
)
def post_file():
    """
    上传文件
    """
    files = request.files
    uploader = LocalUploader(files)
    ret = uploader.upload()
    return ret
