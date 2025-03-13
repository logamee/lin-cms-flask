"""
:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

import os

banner = """
\"""
    :copyright: © 2020 by the Lin team.
    :license: MIT, see LICENSE for more details.
\"""
"""

controller = """
from app.lin import Redprint

{0}_api = Redprint("{0}")


@{0}_api.route("/")
def test():
    return "hi, guy!"
"""

init = """
from .controller import {0}_api
"""

info = """
__name__ = "{0}"
__version__ = "0.1.0"
__author__ = "Team Lin"
"""

readme = """# {0}"""


def create_plugin(name: str):
    cmd = os.getcwd()
    plugins_path = os.path.join(cmd, "app/plugin")
    plugindir = os.path.join(plugins_path, name)
    os.mkdir(plugindir)

    open(os.path.join(plugindir, "config.py"), mode="x", encoding="utf-8")
    open(os.path.join(plugindir, "requirements.txt"), mode="x", encoding="utf-8")

    with open(os.path.join(plugindir, "info.py"), mode="x", encoding="utf-8") as f:
        f.write(banner + info.format(name))

    with open(os.path.join(plugindir, "README.md"), mode="x", encoding="utf-8") as f:
        f.write(readme.format(name))

    appdir = os.path.join(plugindir, "app")
    os.mkdir(appdir)

    with open(os.path.join(appdir, "__init__.py"), mode="x", encoding="utf-8") as f:
        f.write(banner + init.format(name))

    with open(os.path.join(appdir, "controller.py"), mode="x", encoding="utf-8") as f:
        f.write(banner + controller.format(name))

    open(os.path.join(appdir, "model.py"), mode="x", encoding="utf-8")


def generate():
    plugin_name = input("请输入要创建的插件名:\n")
    create_plugin(plugin_name)
