"""插件机制回归：PLUGIN_PATH → Loader → Lin.mount 全链路。

不执行 ``flask plugin init``（它会改写 app/config/base.py 并 pip 安装依赖），
而是以内存库构建最小应用，模拟"插件已初始化"的运行时状态，固化加载链路的行为。
"""

from flask import Flask

from app.config.test import TestConfig
from app.lin import Lin
from app.lin.config import lin_config

POEM_PLUGIN = {
    "poem": {"path": "app.plugin.poem", "enable": True, "version": "0.0.1"},
}


def _app_with_plugins(plugin_path: dict) -> Flask:
    app = Flask("plugin-probe")
    app.config.from_object(TestConfig)
    app.config["PLUGIN_PATH"] = plugin_path
    Lin(app, mount=True, sync_permissions=False)
    return app


def test_enabled_plugin_loads_models_and_controllers():
    app = _app_with_plugins(POEM_PLUGIN)
    manager = app.extensions["manager"]

    assert set(manager.plugins.keys()) == {"poem"}
    poem = manager.plugins["poem"]
    # 插件 __init__ 模块中的 Redprint 控制器与 db.Model 模型应被收集
    assert list(poem.controllers.keys()) == ["poem"]
    assert list(poem.models.keys()) == ["Poem"]


def test_enabled_plugin_mounts_routes():
    app = _app_with_plugins(POEM_PLUGIN)

    rules = {str(rule) for rule in app.url_map.iter_rules()}
    assert "/plugin/poem/all" in rules
    assert "/plugin/poem/authors" in rules
    assert "/plugin/poem/search" in rules


def test_plugin_default_config_merged_into_lin_config():
    _app_with_plugins(POEM_PLUGIN)

    conf = lin_config.get_plugin_config("poem", default=None)
    assert conf is not None
    # app/plugin/poem/config.py 中的默认配置项应可见
    assert conf.get("limit") == 20


def test_disabled_plugin_not_loaded():
    app = _app_with_plugins(
        {"poem": {"path": "app.plugin.poem", "enable": False, "version": "0.0.1"}},
    )
    manager = app.extensions["manager"]

    assert manager.plugins == {}
    rules = {str(rule) for rule in app.url_map.iter_rules()}
    assert not any(rule.startswith("/plugin/") for rule in rules)


def test_get_plugin_model():
    app = _app_with_plugins(POEM_PLUGIN)
    manager = app.extensions["manager"]

    from app.plugin.poem.app.model import Poem

    assert manager.get_model("Poem") is Poem
