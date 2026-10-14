#!/bin/sh
# 容器入口：生产环境启动脚本
set -e

# 幂等写入环境标识（用 > 覆盖，避免每次启动追加一行）
echo "FLASK_ENV=production" > .flaskenv

# 数据库迁移：alembic 按 alembic_version 表天然幂等；
# 空库会自动完成建表 + 种子（root/Guest/权限），存量库只执行增量
flask db upgrade

# gunicorn server
exec gunicorn -c gunicorn.conf.py starter:app
