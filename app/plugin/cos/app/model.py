import hashlib

from sqlalchemy import Column, Integer, String, text

from app.lin import BaseCrud, lin_config


class COS(BaseCrud):
    __tablename__ = "cos"

    id = Column(Integer, primary_key=True)
    file_name = Column(String(255), nullable=False)
    file_key = Column(String(255), nullable=False)
    file_md5 = Column(String(40), nullable=False)
    file_size = Column(Integer())
    url = Column(String(255), nullable=True, comment="存放文件永久访问链接")
    type = Column(
        String(10),
        nullable=False,
        server_default=text("'REMOTE'"),
        comment="LOCAL 本地，REMOTE 远程",
    )
    status = Column(
        String(10),
        nullable=False,
        server_default=text("'REQUEST'"),
        comment="REQUEST 请求上传，UPLOADED 已上传，ERROR 上传错误",
    )

    @staticmethod
    def generate_key(filename: str):
        dir_name = lin_config.get_config("cos.upload_folder")
        file_key = COS._generate_uuid() + COS._get_ext(filename)
        return dir_name + "/" + file_key if dir_name else file_key

    @staticmethod
    def generate_md5(data: bytes):
        md5_obj = hashlib.md5()
        md5_obj.update(data)
        ret = md5_obj.hexdigest()
        return ret

    @staticmethod
    def get_size(client, bucket, file_key) -> str:
        """
        得到文件大小（字节）
        :param client: cos 实例
        :param bucket: 存储桶
        :param file_key: 文件名
        :return: 文件的字节数
        """
        return client.head_object(Bucket=bucket, Key=file_key).get("Content-Length", None)

    @staticmethod
    def get_url(client, bucket, file_key) -> str:
        """
        得到文件永久访问链接
        :param client: cos 实例
        :param bucket: 存储桶
        :param file_key: 文件名
        :return: 文件的永久访问链接
        """
        return client.get_object_url(Bucket=bucket, Key=file_key)

    @staticmethod
    def get_presigned_url(client, bucket, file_key) -> str:
        """
        得到文件临时访问链接
        :param client: cos 实例
        :param bucket: 存储桶
        :param file_key: 文件名
        :return: 文件的临时访问链接
        """
        return client.get_presigned_url(
            Method="GET", Bucket=bucket, Key=file_key, Expired=lin_config.get_config("cos.expire_time")
        )

    @staticmethod
    def _generate_uuid():
        import uuid

        return str(uuid.uuid1())

    @staticmethod
    def _get_ext(filename: str):
        """
        得到文件的扩展名
        :param filename: 原始文件名
        :return: string 文件的扩展名
        """
        return "." + filename.lower().split(".")[-1]
