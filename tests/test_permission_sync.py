"""权限同步回归：代码中的 @permission_meta 声明必须完整落入 lin_permission 表。

历史坑：flask-limiter 的 @limiter.limit 会包装函数并改变其身份（__hash__），
若它叠在 @permission_meta 外层，Lin.mount 按「函数名+身份」匹配元信息会落空，
该权限声明即成死信（不入库，存量行还会被当作过期数据删除）。
规则：@permission_meta 必须紧贴路由装饰器、位于一切包装型装饰器之上。
"""

from app.lin import db


def _manager(app):
    return app.extensions["manager"]


def test_all_declared_permissions_synced_to_db(app):
    with app.app_context():
        permission_model = _manager(app).permission_model
        db_rows = {(p.name, p.module, p.mount) for p in permission_model.get(one=False)}
        code_metas = set(_manager(app).ep_meta.values())
    assert db_rows == code_metas, "代码声明的权限与数据库权限表不一致"
    # 三个业务模块 + 用户模块的最小规模，防止装饰器被静默打飞
    assert len(code_metas) >= 23


def test_decorator_order_victims_present(app):
    """曾被 @limiter.limit 叠错层打死的两条声明必须在场。"""
    with app.app_context():
        code_metas = set(_manager(app).ep_meta.values())
    assert ("注册", "用户", False) in code_metas
    assert ("刷新令牌", "用户", False) in code_metas


def test_sync_is_idempotent(app):
    """重复同步不产生重复行（(name, module) 唯一）。"""
    with app.app_context():
        mgr = _manager(app)
        mgr.sync_permissions()
        rows = [(p.name, p.module) for p in mgr.permission_model.get(one=False)]

    assert len(rows) == len(set(rows))
