"""
 mananger module of Lin.
 ~~~~~~~~~

 manager model

:copyright: © 2020 by the Lin team.
:license: MIT, see LICENSE for more details.
"""

from typing import Any, Dict, List, Optional, Type, Union

from flask import current_app
from werkzeug.local import LocalProxy

from .db import db

__all__ = ["Manager", "manager"]


class Manager(object):
    """manager for lin"""

    # 路由函数的meta信息的容器
    ep_meta: Dict[str, Any] = {}

    def __init__(
        self,
        plugin_path: Dict[str, Any],
        group_model: Type[Any],
        user_model: Type[Any],
        identity_model: Type[Any],
        permission_model: Type[Any],
        group_permission_model: Type[Any],
        user_group_model: Type[Any],
    ) -> None:
        self.group_model = group_model
        self.user_model = user_model
        self.permission_model = permission_model
        self.group_permission_model = group_permission_model
        self.user_group_model = user_group_model
        self.identity_model = identity_model
        from .loader import Loader

        self.loader: Loader = Loader(plugin_path)

    def find_user(self, **kwargs: Any) -> Optional[Any]:
        return self.user_model.query.filter_by(**kwargs).first()

    def verify_user(self, username: str, password: str) -> Any:
        return self.user_model.verify(username, password)

    def find_group(self, **kwargs: Any) -> Optional[Any]:
        return self.group_model.query.filter_by(**kwargs).first()

    def get_ep_infos(self) -> Dict[str, List[Any]]:
        """返回权限管理中的所有视图函数的信息，包含它所属module"""
        info_list = self.permission_model.query.filter_by(mount=True).all()
        infos: Dict[str, List[Any]] = {}
        for permission in info_list:
            module = infos.get(permission.module, None)
            if module:
                module.append(permission)
            else:
                infos.setdefault(permission.module, [permission])

        return infos

    def find_info_by_ep(self, ep: str) -> Optional[Any]:
        """通过请求的endpoint寻找路由函数的meta信息"""
        info = self.ep_meta.get(ep)
        return info if info is not None and info.mount else None

    def find_group_ids_by_user_id(self, user_id: int) -> List[int]:
        """
        根据用户ID，通过User-Group关联表，获取所属用户组的Id列表
        """
        query = (
            db.session.query(self.user_group_model.group_id)
            .join(
                self.user_model,
                self.user_model.id == self.user_group_model.user_id,
            )
            .filter(self.user_model.is_deleted == False, self.user_model.id == user_id)
        )
        result = (
            db.session.query(self.group_model.id)
            .filter(self.group_model.is_deleted == False)
            .filter(self.group_model.id.in_(query))
        )
        # [(1,),(2,),...] => [1,2,...]
        group_ids = [x[0] for x in result.all()]
        return group_ids

    def is_user_allowed(self, group_ids: List[int]) -> bool:
        """查看当前user有无权限访问该路由函数"""
        from flask import request

        from .db import db

        ep = request.endpoint
        if ep is None:
            return False
        # 根据 endpoint 查找 permission, 一定存在
        meta = self.ep_meta.get(ep)
        if meta is None:
            return False
        # 判断 用户组拥有的权限是否包含endpoint标记的权限
        # 传入用户组的 id 列表 和 权限模块名称 权限名称，根据 Group-Permission Model 判断对应权限是否存在
        query = db.session.query(self.group_permission_model.permission_id).filter(
            self.group_permission_model.group_id.in_(group_ids)
        )
        result = self.permission_model.query.filter_by(
            soft=True, module=meta.module, name=meta.name, mount=True
        ).filter(self.permission_model.id.in_(query))
        permission = result.first()
        return True if permission else False

    def find_permission_module(self, name: str) -> Optional[Any]:
        """通过权限寻找meta信息"""
        for _, meta in self.ep_meta.items():
            if meta.name == name:
                return meta
        return None

    @property
    def plugins(self) -> Dict[str, Any]:
        return self.loader.plugins

    def get_plugin(self, name: str) -> Optional[Any]:
        return self.loader.plugins.get(name)

    def get_model(self, name: str) -> Optional[Any]:
        # attention!!! if models have the same name,will return the first one
        # 注意！！！ 如果容器内有相同的model，则默认返回第一个
        for plugin in self.plugins.values():
            model = plugin.models.get(name)
            if model is not None:
                return model
        return None

    def get_service(self, name: str) -> Optional[Any]:
        # attention!!! if services have the same name,will return the first one
        # 注意！！！ 如果容器内有相同的service，则默认返回第一个
        for plugin in self.plugins.values():
            service = plugin.services.get(name)
            if service is not None:
                return service
        return None

    def sync_permissions(self) -> None:
        with db.auto_commit():
            db.create_all()
            permissions = self.permission_model.get(one=False)
            # 新增的权限记录
            new_added_permissions: set[Any] = set()
            deleted_ids = [permission.id for permission in permissions]
            # mount-> unmount
            unmounted_ids: List[int] = list()
            # unmount-> mount 的记录
            mounted_ids: List[int] = list()
            # 用代码中记录的权限比对数据库中的权限
            for _, meta in self.ep_meta.items():
                name, module, mount = meta
                # db_existed 判定 代码中的权限是否存在于权限表记录中
                db_existed = False
                for permission in permissions:
                    if permission.name == name and permission.module == module:
                        # 此条记录存在,从待删除列表中移除,不会被删除
                        if permission.id in deleted_ids:
                            deleted_ids.remove(permission.id)
                        # 此条记录存在，不需要添加到权限表
                        db_existed = True
                        # 判定mount的变动情况，将记录id添加到对应的列表中
                        if permission.mount != mount:
                            if mount:
                                mounted_ids.append(permission.id)
                            else:
                                unmounted_ids.append(permission.id)
                        break
                # 遍历结束，代码中的记录不存在于已有的权限表中，则将其添加到新增权限记录列表
                if not db_existed:
                    permission = self.permission_model()
                    permission.name = name
                    permission.module = module
                    permission.mount = mount
                    new_added_permissions.add(permission)
            _sync_permissions(self, new_added_permissions, unmounted_ids, mounted_ids, deleted_ids)


def _sync_permissions(
    manager: Manager,
    new_added_permissions: set[Any],
    unmounted_ids: List[int],
    mounted_ids: List[int],
    deleted_ids: List[int],
) -> None:
    if new_added_permissions:
        db.session.add_all(new_added_permissions)
    if unmounted_ids:
        manager.permission_model.query.filter(manager.permission_model.id.in_(unmounted_ids)).update(
            {"mount": False}, synchronize_session=False
        )
    if mounted_ids:
        manager.permission_model.query.filter(manager.permission_model.id.in_(mounted_ids)).update(
            {"mount": True}, synchronize_session=False
        )
    if deleted_ids:
        manager.permission_model.query.filter(manager.permission_model.id.in_(deleted_ids)).delete(
            synchronize_session=False
        )
        # 分组-权限关联表中的数据也要清理
        manager.group_permission_model.query.filter(
            manager.group_permission_model.permission_id.in_(deleted_ids)
        ).delete(synchronize_session=False)


def get_manager() -> Manager:
    _manager = current_app.extensions["manager"]
    if _manager:
        return _manager
    else:
        app = current_app._get_current_object()
        with app.app_context():
            return app.extensions["manager"]


# a proxy for manager instance
# attention, only used when context in  stack

# 获得manager实例
# 注意，仅仅在flask的上下文栈中才可获得
manager: Manager = LocalProxy(lambda: get_manager())
