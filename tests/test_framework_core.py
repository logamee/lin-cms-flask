"""
框架核心单元测试（补盲区）:
- Uploader 校验链：扩展名白名单、单文件超限、数量超限、无文件
- LinRotatingFileHandler 滚动切割
- CaptchaTool 生成与解码
- camel2line / get_random_str
"""

import logging
import os
from typing import cast

import pytest
from werkzeug.datastructures import FileStorage

from app.lin.file import Uploader
from app.lin.syslogger import LinRotatingFileHandler
from app.lin.utils import camel2line, get_random_str
from app.util.captcha import CaptchaTool

FILE_CONFIG = {
    "STORE_DIR": "assets",
    "SINGLE_LIMIT": 1024 * 100,  # 100KB
    "TOTAL_LIMIT": 1024 * 1024,
    "NUMS": 2,
    "INCLUDE": {"jpg", "png"},
    "EXCLUDE": set(),
}


def _storage(name: str, size: int = 10) -> FileStorage:
    from io import BytesIO

    return FileStorage(stream=BytesIO(b"x" * size), filename=name)


def _uploader(files, config=None) -> Uploader:
    """绕过 __init__ 的配置读取，仅测校验链。"""
    up = cast(Uploader, object.__new__(Uploader))
    cfg = config or FILE_CONFIG
    up._include = cfg["INCLUDE"]  # type: ignore[attr-defined,assignment]
    up._exclude = cfg["EXCLUDE"]  # type: ignore[attr-defined,assignment]
    up._single_limit = cfg["SINGLE_LIMIT"]  # type: ignore[attr-defined,assignment]
    up._total_limit = cfg["TOTAL_LIMIT"]  # type: ignore[attr-defined,assignment]
    up._nums = cfg["NUMS"]  # type: ignore[attr-defined,assignment]
    up._store_dir = cfg["STORE_DIR"]  # type: ignore[attr-defined,assignment]
    up._file_storage = files  # type: ignore[attr-defined,assignment]
    return up


def _verify(files):
    """触发名称改写的私有校验方法 __verify。"""
    return _uploader(files)._Uploader__verify()  # type: ignore[attr-defined]


def test_uploader_rejects_bad_extension():
    from app.lin.exception import FileExtensionError

    with pytest.raises(FileExtensionError):
        _verify([_storage("evil.php")])


def test_uploader_rejects_no_extension():
    from app.lin.exception import FileExtensionError

    with pytest.raises(FileExtensionError):
        _verify([_storage("noext")])


def test_uploader_accepts_whitelisted():
    _verify([_storage("ok.jpg")])


def test_uploader_rejects_oversize_single():
    from app.lin.exception import FileTooLarge

    with pytest.raises(FileTooLarge):
        _verify([_storage("big.jpg", size=1024 * 101)])


def test_uploader_rejects_too_many():
    from app.lin.exception import FileTooMany

    with pytest.raises(FileTooMany):
        _verify([_storage("a.jpg"), _storage("b.jpg"), _storage("c.jpg")])


def test_uploader_rejects_empty():
    from app.lin.exception import ParameterError

    with pytest.raises(ParameterError):
        _verify([])


def test_rotating_handler_rollover(tmp_path):
    handler = LinRotatingFileHandler(log_dir=str(tmp_path), max_bytes=200)
    logger = logging.getLogger("test-rollover")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    try:
        for i in range(30):
            logger.info("line-%03d %s", i, "z" * 20)
        handler.stream.flush()  # type: ignore[union-attr]
    finally:
        logger.removeHandler(handler)
        handler.close()
    files = [os.path.join(root, f) for root, _, fs in os.walk(tmp_path) for f in fs if f.endswith(".log")]
    assert len(files) >= 2, f"应产生滚动文件: {os.listdir(tmp_path)}"


def test_captcha_roundtrip(app):
    tool = CaptchaTool()
    img, code = tool.get_verify_code()
    assert img.startswith(b"data:image/png;base64,")
    assert len(code) == 4 and code.isdigit()
    # tag 生成逻辑同 user.py：JWT 内嵌 code
    import jwt as pyjwt
    from flask import current_app

    with app.test_request_context():
        tag = pyjwt.encode({"code": code}, current_app.config["SECRET_KEY"], algorithm="HS256")
        payload = pyjwt.decode(tag, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    assert payload["code"] == code


def test_camel2line():
    assert camel2line("CamelCase") == "camel_case"
    assert camel2line("already_line") == "already_line"


def test_get_random_str():
    s = get_random_str(16)
    assert len(s) == 16
    assert s.isalnum()
