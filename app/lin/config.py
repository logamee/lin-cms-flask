"""
config class of Lin
~~~~~~~~~

This module implements a config class

:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from collections import defaultdict
from typing import Any, Dict, Optional, Union


class Config(defaultdict[str, Any]):
    def add_plugin_config(self, plugin_name: str, obj: Dict[str, Any]) -> None:
        if type(obj) is dict:
            if self.get(plugin_name, None) is None:
                self[plugin_name] = {}
            for k, v in obj.items():
                self[plugin_name][k] = v

    def add_plugin_config_item(self, plugin_name: str, key: str, value: Any) -> None:
        if self.get(plugin_name, None) is None:
            self[plugin_name] = {}
        self[plugin_name][key] = value

    def get_plugin_config(self, plugin_name: str, default: Optional[Any] = None) -> Any:
        return self.get(plugin_name, default)

    def get_plugin_config_item(self, plugin_name: str, key: str, default: Optional[Any] = None) -> Any:
        plugin_conf = self.get(plugin_name)
        if plugin_conf is None:
            return default
        return plugin_conf.get(key, default)

    def get_config(self, key: str, default: Optional[Any] = None) -> Any:
        """plugin_name.key"""
        if "." not in key:
            return self.get(key, default)
        index = key.rindex(".")
        plugin_name = key[:index]
        plugin_key = key[index + 1 :]
        plugin_conf = self.get(plugin_name)
        if plugin_conf is None:
            return default
        return plugin_conf.get(plugin_key, default)


lin_config: Config = Config()

global_config: Dict[str, Any] = dict()
