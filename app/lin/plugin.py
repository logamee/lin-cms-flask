"""
plugin of Lin
~~~~~~~~~

Plugin Class of Lin, which you can access plugins in the manager.

:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""


class Plugin(object):
    def __init__(self, name=None):
        """
        :param name: plugin的名称
        """
        # container of plugin's controllers
        # 控制器容器
        self.controllers = {}
        # container of plugin's models
        # 模型层容器
        self.models = {}
        # plugin's services
        self.services = {}

        self.name = name

    def add_model(self, name, model):
        self.models[name] = model

    def get_model(self, name):
        return self.models.get(name)

    def add_controller(self, name, controller):
        self.controllers[name] = controller

    def add_service(self, name, service):
        self.services[name] = service

    def get_service(self, name):
        return self.services.get(name)
