"""
Redprint of Lin
~~~~~~~~~
Redprint make blueprint more fine-grained
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple


class Redprint:
    def __init__(self, name: str, with_prefix: bool = True) -> None:
        """
        初始化 Redprint 实例

        :param name: Redprint 的名称
        :param with_prefix: 是否使用前缀
        """
        self.name: str = name
        self.with_prefix: bool = with_prefix
        self.mound: List[Tuple[Callable[..., Any], str, Dict[str, Any]]] = []

    def route(self, rule: str, **options: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        添加路由规则

        :param rule: 路由规则
        :param options: 其他选项
        :return: 装饰器函数
        """

        def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
            self.mound.append((f, rule, options))
            return f

        return decorator

    def register(self, bp: Any, url_prefix: Optional[str] = None) -> None:
        """
        注册路由到蓝图

        :param bp: 蓝图对象
        :param url_prefix: URL 前缀
        """
        if url_prefix is None and self.with_prefix:
            url_prefix = "/" + self.name
        else:
            url_prefix = "" + str(url_prefix) + "/" + self.name
        for f, rule, options in self.mound:
            endpoint = self.name + "+" + options.pop("endpoint", f.__name__)
            if rule:
                url = url_prefix + rule
                bp.add_url_rule(url, endpoint, f, **options)
            else:
                bp.add_url_rule(url_prefix, endpoint, f, **options)
