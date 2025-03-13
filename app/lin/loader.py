"""
loader of Lin
~~~~~~~~~

This module implements a plugin loader of Lin.

:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from importlib import import_module

from .config import lin_config
from .db import db
from .plugin import Plugin
from .redprint import Redprint


class Loader(object):
    plugin_path: dict = None

    def __init__(self, plugin_path):
        self.plugins = {}
        assert type(plugin_path) is dict, "plugin_path must be a dict"
        self.plugin_path = plugin_path
        self.load_plugins_config()
        self.load_plugins()

    def load_plugins(self):
        for name, conf in self.plugin_path.items():
            enable = conf.get("enable", None)
            if enable:
                path = conf.get("path")
                # load plugin
                path and self._load_plugin(f"{path}.app.__init__", name)

    def load_plugins_config(self):
        for name, conf in self.plugin_path.items():
            path = conf.get("path", None)
            # load config
            self._load_config(f"{path}.config", name, conf)

    def _load_plugin(self, path, name):
        mod = import_module(path)
        plugin = Plugin(name=name)
        dic = mod.__dict__
        for key in dic.keys():
            if not key.startswith("_") and key != "initial_data":
                attr = dic[key]
                if isinstance(attr, Redprint):
                    plugin.add_controller(attr.name, attr)
                elif issubclass(attr, db.Model):
                    plugin.add_model(attr.__name__, attr)
                # 暂时废弃加载service，用处不大
                # elif issubclass(attr, ServiceInterface):
                #     plugin.add_service(attr.__name__, attr)
        self.plugins[plugin.name] = plugin

    def _check_version(self, path, version, name):
        info_mod = import_module(path)
        info_dic = info_mod.__dict__
        assert info_dic["__version__"] == version, "the plugin " + name + " needs to be updated"

    def _load_config(self, config_path, name, conf):
        default_conf = {}
        try:
            if config_path:
                mod = import_module(config_path)
                dic = mod.__dict__
                for key in dic.keys():
                    if not key.startswith("_"):
                        default_conf[key] = dic[key]
        except ModuleNotFoundError:
            pass
        default_conf.update(**conf)
        lin_config.add_plugin_config(plugin_name=name, obj=default_conf)
