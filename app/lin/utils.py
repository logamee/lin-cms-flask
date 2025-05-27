"""
utils of Lin
~~~~~~~~~

util functions make Lin more easy.

:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import errno
import importlib.util
import os
import random
import re
import time
import types
from collections import namedtuple
from importlib import import_module
from typing import Any, Callable, Dict, Union


def get_timestamp(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    获取当前时间戳，并按指定格式返回。

    :param fmt: 时间戳的格式。
    :return: 格式化后的时间戳。
    """
    return time.strftime(fmt, time.localtime(time.time()))


def get_pyfile(path: str, module_name: str, silent: bool = False) -> Union[Dict[str, Any], bool]:
    """
    获取 Python 文件的所有属性。

    :param path: Python 文件的路径。
    :param module_name: 模块名称。
    :param silent: 是否静默处理错误。
    :return: Python 文件的所有属性，或在静默模式下返回 False。
    """
    d = types.ModuleType(module_name)
    d.__file__ = path
    try:
        with open(path, mode="rb") as config_file:
            exec(compile(config_file.read(), path, "exec"), d.__dict__)
    except IOError as e:
        if silent and e.errno in (errno.ENOENT, errno.EISDIR, errno.ENOTDIR):
            return False
        e.strerror = "无法加载配置文件 (%s)" % e.strerror
        raise
    return d.__dict__


def load_object(path: str) -> Any:
    """
    从模块中获取属性。

    :param path: 模块路径。
    :return: 模块中的对象。
    :raises ValueError: 如果路径不是完整路径。
    :raises NameError: 如果模块中未定义该对象。
    """
    try:
        dot = path.rindex(".")
    except ValueError:
        raise ValueError("加载对象 '%s' 出错：不是完整路径" % path)

    module, name = path[:dot], path[dot + 1 :]
    mod = import_module(module)

    try:
        obj = getattr(mod, name)
    except AttributeError:
        raise NameError("模块 '%s' 中未定义名为 '%s' 的对象" % (module, name))

    return obj


def import_module_abs(name: str, path: str) -> None:
    """
    使用绝对路径导入模块。

    :param name: 模块名称。
    :param path: 模块的绝对路径。
    """
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is not None and spec.loader is not None:
        foo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(foo)


def get_pwd() -> str:
    """
    获取当前工作目录的绝对路径。

    :return: 当前工作目录的绝对路径。
    """
    return os.path.abspath(os.getcwd())


def camel2line(camel: str) -> str:
    """
    将驼峰命名字符串转换为下划线命名字符串。

    :param camel: 驼峰命名字符串。
    :return: 下划线命名字符串。
    """
    p = re.compile(r"([a-z]|\d)([A-Z])")
    line = re.sub(p, r"\1_\2", camel).lower()
    return line


def get_random_str(length: int) -> str:
    """
    生成指定长度的随机字符串。

    :param length: 随机字符串的长度。
    :return: 随机字符串。
    """
    seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    sa = [random.choice(seed) for _ in range(length)]
    return "".join(sa)


Meta = namedtuple("Meta", ["name", "module", "mount"])

permission_meta_infos: Dict[str, Meta] = {}


def permission_meta(name: str, module: str = "common", mount: bool = True):
    """
    记录路由函数的信息。

    :param name: 权限名称。
    :param module: 函数所属模块。
    :param mount: 是否将函数挂载到权限。
    :return: 包装函数。
    """

    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        func_name = func.__name__ + str(func.__hash__())
        existed_meta = permission_meta_infos.get(func_name, None)
        existed = existed_meta is not None and existed_meta.module == module
        if existed:
            raise Exception("函数名在同一模块中不能重复")
        else:
            permission_meta_infos.setdefault(func_name, Meta(name, module, mount))

        return func

    return wrapper
