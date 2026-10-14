import click
from flask.cli import AppGroup, with_appcontext

from .db import fake as _db_fake
from .plugin import generate as _plugin_generate
from .plugin import init as _plugin_init

plugin_cli = AppGroup("plugin")


@plugin_cli.command("init", with_appcontext=False)
def plugin_init():
    """
    init plugin
    """
    _plugin_init()


@plugin_cli.command("generate", with_appcontext=False)
def plugin_generate():
    """
    generate plugin
    """
    _plugin_generate()


# 命令挂进 flask-migrate 的 `flask db` 命令组（覆盖同名子命令，保持老用户习惯）：
# - init：建表 + 种子（语义与迁移体系前完全一致；alembic 原生 init 只用于创建迁移仓库，
#   而 migrations/ 已随仓库提交，本项目永远不需要再 scaffold，因此安全遮蔽）
# - fake：演示数据，按需手动执行，不随 upgrade 进入生产
from flask_migrate.cli import db as migrate_db_group  # noqa: E402


@migrate_db_group.command("init")
@click.option("--force", is_flag=True, help="Create after drop.")
@with_appcontext
def db_init(force):
    """
    initialize the database.
    """

    from flask_migrate import downgrade, upgrade

    if force:
        click.confirm("此操作将清空数据，是否继续?", abort=True)
        downgrade(revision="base")
    upgrade()
    click.echo("数据库初始化成功")


@migrate_db_group.command("fake")
@with_appcontext
def db_fake():
    """
    fake the db data.
    """
    _db_fake()
    click.echo("fake数据添加成功")
