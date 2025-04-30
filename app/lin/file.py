"""uploader of Lin
~~~~~~~~~

uploader 模块，使用策略模式实现的上传文件接口

:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import hashlib
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import current_app
from werkzeug.datastructures import FileStorage

from .exception import FileExtensionError, FileTooLarge, FileTooMany, ParameterError


class Uploader(object):
    def __init__(self, files: Union[List[FileStorage], FileStorage], config: Dict[str, Any] = {}):
        #: the list of allowed files
        #: 被允许的文件类型列表
        self._include: List[str] = []
        #: the list of not allowed files
        #: 不被允许的文件类型列表
        self._exclude: List[str] = []
        #: the max bytes of single file
        #: 单个文件的最大字节数
        self._single_limit: int = 0
        #: the max bytes of multiple files
        #: 多个文件的最大字节数
        self._total_limit: int = 0
        #: the max nums of files
        #: 文件上传的最大数量
        self._nums: int = 0
        #: the directory of file storage
        #: 文件存贮目录
        self._store_dir: str = ""
        #: the FileStorage Object
        #: 文件存贮对象
        self._file_storage: List[FileStorage] = self.__parse_files(files)
        self.__load_config(config)
        self.__verify()

    def upload(self, **kwargs) -> Dict[str, Any]:
        """
        文件上传抽象方法，一定要被子类所实现
        """
        raise NotImplementedError()

    @staticmethod
    def _generate_uuid() -> str:
        import uuid

        return str(uuid.uuid1())

    @staticmethod
    def _get_ext(filename: str) -> str:
        """
        得到文件的扩展名
        :param filename: 原始文件名
        :return: string 文件的扩展名
        """
        return "." + filename.lower().split(".")[-1]

    @staticmethod
    def _generate_md5(data: bytes) -> str:
        md5_obj = hashlib.md5()
        md5_obj.update(data)
        ret = md5_obj.hexdigest()
        return ret

    @staticmethod
    def _get_size(file_obj: FileStorage) -> int:
        """
        得到文件大小（字节）
        :param file_obj: 文件对象
        :return: 文件的字节数
        """
        file_obj.seek(0, os.SEEK_END)
        size = file_obj.tell()
        file_obj.seek(0)  # 将文件指针重置
        return size

    @staticmethod
    def _generate_name(filename: str) -> str:
        return Uploader._generate_uuid() + Uploader._get_ext(filename)

    def __load_config(self, custom_config: Dict[str, Any]) -> None:
        """
        加载文件配置，如果用户不传 config 参数，则加载默认配置
        :param custom_config: 用户自定义配置参数
        :return: None
        """
        default_config = current_app.config.get("FILE")
        self._include = custom_config["INCLUDE"] if "INCLUDE" in custom_config else default_config["INCLUDE"]
        self._exclude = custom_config["EXCLUDE"] if "EXCLUDE" in custom_config else default_config["EXCLUDE"]
        self._single_limit = (
            custom_config["SINGLE_LIMIT"] if "SINGLE_LIMIT" in custom_config else default_config["SINGLE_LIMIT"]
        )
        self._total_limit = (
            custom_config["TOTAL_LIMIT"] if "TOTAL_LIMIT" in custom_config else default_config["TOTAL_LIMIT"]
        )
        self._nums = custom_config["NUMS"] if "NUMS" in custom_config else default_config["NUMS"]
        self._store_dir = custom_config["STORE_DIR"] if "STORE_DIR" in custom_config else default_config["STORE_DIR"]

    @staticmethod
    def __parse_files(files: Union[List[FileStorage], FileStorage]) -> List[FileStorage]:
        ret: List[FileStorage] = []
        for key, value in files.items():
            ret += files.getlist(key)
        return ret

    def __verify(self) -> None:
        """
        验证文件是否合法
        """
        if not self._file_storage:
            raise ParameterError("未找到符合条件的文件资源")
        self.__allowed_file()
        self.__allowed_file_size()

    def _get_store_path(self, filename: str) -> Tuple[str, str, str]:
        uuid_filename = self._generate_name(filename)
        format_day = self.__get_format_day()
        store_dir = self._store_dir
        return (
            os.path.join(store_dir, uuid_filename),
            format_day + os.path.sep + uuid_filename,
            uuid_filename,
        )

    def mkdir_if_not_exists(self) -> None:
        if not os.path.isabs(self._store_dir):
            self._store_dir = os.path.abspath(self._store_dir)
        # mkdir by YYYY/MM/DD
        self._store_dir += os.path.sep + self.__get_format_day()
        if not os.path.exists(self._store_dir):
            os.makedirs(self._store_dir)

    @staticmethod
    def __get_format_day() -> str:
        import time

        return str(time.strftime("%Y/%m/%d"))

    def __allowed_file(self) -> bool:
        """
        验证扩展名是否合法
        """
        if (self._include and self._exclude) or self._include:
            for single in self._file_storage:
                if "." not in single.filename or single.filename.lower().rsplit(".", 1)[1] not in self._include:
                    raise FileExtensionError()
            return True
        elif self._exclude and not self._include:
            for single in self._file_storage:
                if "." not in single.filename or single.filename.lower().rsplit(".", 1)[1] in self._exclude:
                    raise FileExtensionError()
            return True
        return False

    def __allowed_file_size(self) -> None:
        """
        验证文件大小是否合法
        """
        file_count = len(self._file_storage)
        if file_count > 1:
            if file_count > self._nums:
                raise FileTooMany()
            total_size = 0
            for single in self._file_storage:
                if self._get_size(single) > self._single_limit:
                    raise FileTooLarge(single.filename + "大小不能超过" + str(self._single_limit) + "字节")
                total_size += self._get_size(single)
            if total_size > self._total_limit:
                raise FileTooLarge()
        else:
            file_size = self._get_size(self._file_storage[0])
            if file_size > self._single_limit:
                raise FileTooLarge()
