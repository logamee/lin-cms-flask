"""seed root guest permissions

空库种子：Root/Guest 分组、root 用户（密码 123456）、权限同步。
存量库通过 `flask db stamp head` 跳过；upgrade 内置幂等保护。

Revision ID: ba96e78c8dbb
Revises: 84684d65072f
Create Date: 2026-10-13 17:05:54.881210

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ba96e78c8dbb"
down_revision = "84684d65072f"
branch_labels = None
depends_on = None


def upgrade():
    # flask-migrate 的 env.py 在应用上下文中执行，可直接使用 ORM 与 manager
    from app.lin import GroupLevelEnum, db, manager

    bind = op.get_bind()
    if not sa.inspect(bind).has_table("lin_user"):
        return
    # 幂等：已有用户数据（如存量库被误升级）则跳过种子
    if bind.execute(sa.text("select count(*) from lin_user")).scalar():
        return

    with db.auto_commit():
        root_group = manager.group_model()
        root_group.name = "Root"
        root_group.info = "超级用户组"
        root_group.level = GroupLevelEnum.ROOT.value
        db.session.add(root_group)

        guest_group = manager.group_model()
        guest_group.name = "Guest"
        guest_group.info = "游客组"
        guest_group.level = GroupLevelEnum.GUEST.value
        db.session.add(guest_group)
        db.session.flush()

        root = manager.user_model()
        root.username = "root"
        db.session.add(root)
        db.session.flush()
        root.password = "123456"

        user_group = manager.user_group_model()
        user_group.user_id = root.id
        user_group.group_id = root_group.id
        db.session.add(user_group)

    # 权限数据同步（表结构来自 baseline，此时已就绪）
    manager.sync_permissions()


def downgrade():
    # 清空种子数据（--force 重建场景：downgrade base 后重新 upgrade）
    op.execute("delete from lin_user_group")
    op.execute("delete from lin_user_identity")
    op.execute("delete from lin_user")
    op.execute("delete from lin_group_permission")
    op.execute("delete from lin_permission")
    op.execute("delete from lin_group")
