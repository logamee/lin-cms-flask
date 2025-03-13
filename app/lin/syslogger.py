"""
syslogger of Lin
~~~~~~~~~

logger 模块，记录系统日志

:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import datetime
import logging
import os
import time
from logging.handlers import BaseRotatingHandler
from typing import Any, Optional

from flask import Flask, g, json, request

__all__ = ["SysLogger"]


class SysLogger:
    """
    运行日志
    """

    def __init__(self, app: Flask, fmt: Optional[str] = None, handler: Optional[logging.Handler] = None) -> None:
        """
        初始化 SysLogger 实例

        :param app: Flask 应用实例
        :param fmt: 日志格式
        :param handler: 日志处理器
        """
        self._app = app
        self._fmt = fmt
        self._handler = handler
        self._logger: Optional[logging.Logger] = None
        self._log_config = self._app.config.get("LOG")
        self.init_logger()
        self.set_logger()
        self.display_request()

    def register_before_request(self) -> None:
        """
        注册请求前的处理函数，记录请求开始时间
        """

        @self._app.before_request
        def request_cost_time() -> None:
            g.request_start_time = time.time()
            g.request_time = lambda: "%.5f" % (time.time() - g.request_start_time)

    def register_after_request(self) -> None:
        """
        注册请求后的处理函数，记录请求日志

        :param resp: 响应对象
        :return: 响应对象
        """

        @self._app.after_request
        def log_response(resp: Any) -> Any:
            log_config = self._app.config.get("LOG")
            if not log_config["REQUEST_LOG"]:
                return resp
            message = "[%s] -> [%s] from:%s costs:%.3f ms" % (
                request.method,
                request.path,
                request.remote_addr,
                float(g.request_time()) * 1000,
            )
            if log_config["LEVEL"] == "INFO":
                self._app.logger.info(message)
            elif log_config["LEVEL"] == "DEBUG":
                req_body = "{}"
                try:
                    req_body = request.get_json() if request.get_json() else {}
                except Exception:
                    pass
                message += " data:{\n\tparam: %s, \n\tbody: %s\n} " % (
                    json.dumps(request.args, ensure_ascii=False),
                    req_body,
                )
                self._app.logger.debug(message)
            return resp

    def display_request(self) -> None:
        """
        终端回显系统日志
        """
        self.register_before_request()
        self.register_after_request()

    def init_logger(self) -> None:
        """
        初始化日志记录器
        """
        if self._log_config["FILE"] and not self._app.debug:
            fmt = logging.Formatter(
                "%(asctime)s %(levelname)s %(process)d   ---  [%(threadName)s]" " - %(message)s"
                if not self._fmt
                else self._fmt
            )
            logging.basicConfig(level=logging.DEBUG)
            self._handler = LinRotatingFileHandler(
                log_dir=self._log_config["DIR"],
                max_bytes=self._log_config["SIZE_LIMIT"],
                encoding="UTF-8",
            )
            self._handler.setFormatter(fmt)
            self._handler.setLevel(level=logging.DEBUG)
            self._app.logger.addHandler(self._handler)
        else:
            return

    def set_logger(self) -> None:
        """
        设置日志记录器
        """
        self._logger = logging.getLogger(__name__)

    def get_logger(self) -> Optional[logging.Logger]:
        """
        获取日志记录器

        :return: 日志记录器
        """
        return self._logger


class LinRotatingFileHandler(BaseRotatingHandler):
    def __init__(
        self,
        log_dir: str = "logs",
        mode: str = "a",
        max_bytes: int = 0,
        encoding: Optional[str] = None,
        delay: bool = False,
    ) -> None:
        """
        初始化 LinRotatingFileHandler 实例

        :param log_dir: 日志目录
        :param mode: 文件打开模式
        :param max_bytes: 最大文件大小
        :param encoding: 文件编码
        :param delay: 是否延迟文件打开
        """
        if max_bytes > 0:
            mode = "a"
        self._log_dir = log_dir
        self._suffix = ".log"
        self._year_month = datetime.datetime.now().strftime("%Y-%m")
        self.store_dir = os.path.join(self._log_dir, self._year_month)
        self._create_new_stream_if_not_exists(self.store_dir, open_stream=False)
        self.filename = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(self.store_dir, self.filename) + self._suffix
        BaseRotatingHandler.__init__(self, filename, mode, encoding, delay)
        self.max_bytes = max_bytes

    def doRollover(self) -> None:
        """
        执行日志滚动
        """
        year_month = datetime.datetime.now().strftime("%Y-%m")
        filename = datetime.datetime.now().strftime("%Y-%m-%d")

        if self.stream:
            self.stream.close()
            self.stream = None

        if self.filename != filename or self._year_month != year_month:
            self.baseFilename = self.baseFilename.replace(
                os.path.join(self._year_month, self.filename),
                os.path.join(year_month, filename),
            )
            self.filename = filename
            self._year_month = year_month
        else:
            dfn = self.rotation_filename(
                self.baseFilename.replace(
                    self._suffix,
                    "-" + datetime.datetime.now().strftime("%H-%M-%S") + self._suffix,
                )
            )
            if os.path.exists(dfn):
                os.remove(dfn)
            self.rotate(self.baseFilename, dfn)
        if not self.delay:
            self.stream = self._open()

    def shouldRollover(self, record: logging.LogRecord) -> int:
        """
        判断是否需要滚动日志

        :param record: 日志记录
        :return: 是否需要滚动日志
        """
        year_month = datetime.datetime.now().strftime("%Y-%m")
        filename = datetime.datetime.now().strftime("%Y-%m-%d")
        self._create_new_stream_if_not_exists(os.path.join(self._log_dir, year_month))
        if self.stream is None:
            self.stream = self._open()
        if self._year_month != year_month or self.filename != filename:
            return 1
        if self.max_bytes > 0:
            msg = "%s\n" % self.format(record)
            self.stream.seek(0, 2)
            if self.stream.tell() + len(msg) >= self.max_bytes:
                return 1
        return 0

    def _create_new_stream_if_not_exists(self, store_dir: str, open_stream: bool = True) -> None:
        """
        创建新的日志流（如果不存在）

        :param store_dir: 存储目录
        :param open_stream: 是否打开流
        """
        if not os.path.exists(store_dir):
            os.makedirs(store_dir)
            if open_stream:
                self.stream = self._open()
