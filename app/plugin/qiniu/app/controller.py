"""
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from flask import request
from qiniu import Auth

from app.lin import FileExtensionError, Redprint, lin_config

from .model import Qiniu

qiniu_api = Redprint("qiniu")


@qiniu_api.route("/uptoken")
def up_token():
    """
    生成 token 给前端，前端直接上传
    """
    access_key = lin_config.get_config("qiniu.access_key")
    secret_key = lin_config.get_config("qiniu.secret_key")
    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 要上传的空间
    bucket_name = lin_config.get_config("qiniu.bucket_name")
    # 允许的文件类型
    allowed_extensions = lin_config.get_config("qiniu.allowed_extensions")
    # 上传后保存的文件名
    filename = request.args.get("filename", str())
    if filename.split(".")[-1] in allowed_extensions:
        # 生成上传 Token，可以指定过期时间等
        # 上传策略示例
        # https://developer.qiniu.com/kodo/manual/1206/put-policy
        policy = {
            # 'callbackUrl':'https://requestb.in/1c7q2d31',
            # 'callbackBody':'filename=$(fname)&filesize=$(fsize)'
            # 'persistentOps':'imageView2/1/w/200/h/200'
        }
        token = q.upload_token(
            bucket_name,
            filename,
            lin_config.get_config("qiniu.token_expire_time"),
            policy,
        )
        return {"token": token}
    else:
        raise FileExtensionError


@qiniu_api.route("/record", methods=["POST"])
def record():
    Qiniu.create(url=request.get_json().url, commit=True)
