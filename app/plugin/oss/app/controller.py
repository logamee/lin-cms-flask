import os

import oss2
from flask import jsonify, request

from app.lin import Failed, ParameterError, Redprint, Success, db, get_random_str, lin_config

from .model import OSS

api = Redprint("oss")


@api.route("/upload_to_local", methods=["POST"])
def upload():
    image = request.files.get("image", None)
    if not image:
        raise ParameterError("没有找到图片")
    if image and allowed_file(image.filename):
        path = os.path.join(lin_config.get_config("oss.upload_folder"), image.filename)
        image.save(path)
    else:
        raise ParameterError("图片类型不允许或图片key不合法")
    raise Success()


@api.route("/upload_to_ali", methods=["POST"])
def upload_to_ali():
    image = request.files.get("image", None)
    if not image:
        raise ParameterError("没有找到图片")
    if image and allowed_file(image.filename):
        url = upload_image_bytes(image.filename, image)
        if url:
            res = {"url": url}
            with db.auto_commit():
                exist = OSS.get(url=url)
                if not exist:
                    data = {"url": url}
                    one = OSS.create(**data)
                    db.session.flush()
                    res["id"] = one.id
                else:
                    res["id"] = exist.id
            return jsonify(res)
    return Failed("上传图片失败，请检查图片路径")


@api.route("/upload_multiple", methods=["POST"])
def upload_multiple_to_ali():
    imgs = []
    for item in request.files:
        img = request.files.get(item, None)
        if not img:
            raise ParameterError("没接收到图片，请检查图片路径")
        if img and allowed_file(img.filename):
            url = upload_image_bytes(img.filename, img)
            if url:
                # 每上传成功一次图片需记录到数据库
                with db.auto_commit():
                    exist = OSS.get(url=url)
                    if not exist:
                        data = {"url": url}
                        res = OSS.create(**data)
                        db.session.flush()
                        imgs.append({"key": item, "url": url, "id": res.id})
                    else:
                        imgs.append({"key": item, "url": url, "id": exist.id})
    return jsonify(imgs)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1] in lin_config.get_config("oss.allowed_extensions", [])


def upload_image_bytes(name: str, data: bytes):
    access_key_id = lin_config.get_config("oss.access_key_id")
    access_key_secret = lin_config.get_config("oss.access_key_secret")
    auth = oss2.Auth(access_key_id, access_key_secret)
    bucket = oss2.Bucket(
        auth,
        lin_config.get_config("oss.endpoint"),
        lin_config.get_config("oss.bucket_name"),
    )
    suffix = name.split(".")[-1]
    rand_name = get_random_str(15) + "." + suffix
    res = bucket.put_object(rand_name, data)
    if res.resp.status == 200:
        return res.resp.response.url
    return None
