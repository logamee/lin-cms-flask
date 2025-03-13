from flask import request
from werkzeug.local import LocalProxy

from app.api import AuthorizationBearerSecurity, api
from app.lin import DocResponse, Failed, ParameterError, Redprint, db, lin_config, login_required

from .exception import ImageNotFound
from .model import COS
from .schema import CosOutSchema, CosOutSchemaList

client = LocalProxy(lambda: get_cos_client())

cos_api = Redprint("cos")


@cos_api.route("/<int:_id>")
@login_required
@api.validate(
    resp=DocResponse(ImageNotFound, r=CosOutSchema),
    tags=["cos"],
    security=[AuthorizationBearerSecurity],
)
def get_cos_image(_id):
    """
    获取指定 id 的 cos
    """
    cos = COS.get(id=_id)
    if cos:
        bucket = lin_config.get_config("cos.bucket_name")
        if lin_config.get_config("cos.need_return_url"):
            # 返回永久链接
            url = cos.url if cos.url else COS.get_url(client, bucket, cos.file_key)
        else:
            # 返回临时链接
            url = COS.get_presigned_url(client, bucket, cos.file_key)
        return {"id": cos.id, "url": url, "file_name": cos.file_name, "file_key": cos.file_key}
    raise ImageNotFound


@cos_api.route("/upload_one", methods=["POST"])
@login_required
@api.validate(
    resp=DocResponse(r=CosOutSchema),
    tags=["cos"],
    security=[AuthorizationBearerSecurity],
)
def upload_one():
    image = request.files.get("image", None)
    if not image:
        raise ParameterError("没有找到图片")
    if image and allowed_file(image.filename):
        return upload_image_and_create_cos(image.filename, image.read())
    return Failed("上传图片失败，请检查图片路径")


@cos_api.route("/upload_multiple", methods=["POST"])
@login_required
@api.validate(
    resp=DocResponse(r=CosOutSchemaList),
    tags=["cos"],
    security=[AuthorizationBearerSecurity],
)
def upload_multiple():
    images = []
    for item in request.files:
        image = request.files.get(item, None)
        if not image:
            raise ParameterError("没接收到图片，请检查图片路径")
        if image and allowed_file(image.filename):
            images.append(upload_image_and_create_cos(image.filename, image.read()))
    return images


def upload_image_and_create_cos(name: str, data: bytes) -> dict:
    bucket = lin_config.get_config("cos.bucket_name")
    file_md5 = COS.generate_md5(data)
    exist = COS.get(file_name=name, file_md5=file_md5)
    if exist:
        file_url = COS.get_presigned_url(client, bucket, exist.file_key)
        res = {"id": exist.id, "url": file_url, "file_name": exist.file_name, "file_key": exist.file_key}
        return res

    file_key = COS.generate_key(name)
    client.put_object(Bucket=bucket, Body=data, Key=file_key, StorageClass="STANDARD")
    res = {"file_name": name, "file_key": file_key}
    url = COS.get_url(client, bucket, file_key)
    if lin_config.get_config("cos.need_return_url"):
        # 返回永久链接
        res["url"] = url
    else:
        # 返回临时链接
        res["url"] = COS.get_presigned_url(client, bucket, file_key)
    file_size = COS.get_size(client, bucket, file_key)
    with db.auto_commit():
        cos_data = {
            "file_name": name,
            "file_key": file_key,
            "file_md5": file_md5,
            "file_size": file_size,
            "status": "UPLOADED",
            "commit": True,
        }
        if lin_config.get_config("cos.need_save_url"):
            cos_data["url"] = url
        one = COS.create(**cos_data)
        res["id"] = one.id
    return res


def get_cos_client():
    from qcloud_cos import CosConfig, CosS3Client

    token, proxies, endpoint, domain = None, None, None, None
    secret_id = lin_config.get_config("cos.access_key_id")
    secret_key = lin_config.get_config("cos.access_key_secret")
    region = lin_config.get_config("cos.region")
    scheme = lin_config.get_config("cos.scheme")
    if lin_config.get_config("cos.token"):
        token = lin_config.get_config("cos.token")
    if lin_config.get_config("cos.proxies"):
        proxies = lin_config.get_config("cos.proxies")
    if lin_config.get_config("cos.endpoint"):
        endpoint = lin_config.get_config("cos.endpoint")
    if lin_config.get_config("cos.domain"):
        domain = lin_config.get_config("cos.domain")

    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Scheme=scheme)
    if token:
        config._token = token
    if proxies:
        config._proxies = proxies
    if endpoint:
        config._endpoint = endpoint
    if domain:
        config._domain = domain
    return CosS3Client(config)


def allowed_file(filename):
    return "." in filename and (filename.rsplit(".", 1)[1]).lower() in lin_config.get_config(
        "cos.allowed_extensions", []
    )
