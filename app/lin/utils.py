"""
utils of Lin
~~~~~~~~~

:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import random
import re
import string
from collections import namedtuple
from typing import Any, Callable, Dict

__all__ = ["camel2line", "get_random_str", "permission_meta", "Meta", "permission_meta_infos"]


def camel2line(camel: str) -> str:
    """
    将驼峰命名字符串转换为下划线命名的字符串。
    """
    p = re.compile(r"([a-z]|\d)([A-Z])")
    line = re.sub(p, r"\1_\2", camel).lower()
    return line


def get_random_str(length: int) -> str:
    """
    生成指定长度的随机字符串。
    """
    sa = [random.choice(string.ascii_letters + string.digits) for _ in range(length)]
    return "".join(sa)


Meta = namedtuple("Meta", ["name", "module", "mount"])

permission_meta_infos: Dict[str, Meta] = {}


def permission_meta(name: str, module: str = "common", mount: bool = True):
    """
    权限装饰器：为视图函数标记权限元信息，启动时同步进权限表。
    注意：必须原样返回 func（不能包装），Lin.mount 依赖函数身份（__hash__）匹配元信息。
    """

    def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        func_name = func.__name__ + str(func.__hash__())
        existed_meta = permission_meta_infos.get(func_name, None)
        existed = existed_meta is not None and existed_meta.module == module
        if existed:
            raise Exception("函数名在同一模块中不能重复")
        permission_meta_infos.setdefault(func_name, Meta(name, module, mount))
        return func

    return wrapper
