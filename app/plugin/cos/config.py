access_key_id = "not complete"
access_key_secret = "not complete"
bucket_name = "not complete"  # "bucket-appid"
region = "not complete"
scheme = "https"  # 指定使用 http/https 协议来访问 COS，默认为 https，可不填
token = None  # 如果使用永久密钥不需要填入token，如果使用临时密钥需要填入，临时密钥生成和使用指引参见https://cloud.tencent.com/document/product/436/14048
proxies = None  # 默认不需要，详细见腾讯云 cos 文档
endpoint = None  # 默认不需要，详细见腾讯云 cos 文档
domain = None  # 默认不需要，详细见腾讯云 cos 文档

upload_folder = None  # 指定 cos 存储桶里的文件夹目录名字，默认为空
allowed_extensions = ["jpg", "gif", "png", "bmp"]  # 允许上传的文件类型
expire_time = 60 * 60  # 临时链接过期时间，默认 1 小时
need_save_url = False  # 是否要保存 cos 生成的永久链接
need_return_url = False  # 是否让接口返回永久链接，默认返回临时链接
