import math

from flask import Blueprint
from sqlalchemy import text

from app.api import AuthorizationBearerSecurity, api
from app.api.cms.schema.log import LogPageSchema, LogQuerySearchSchema, UsernameListSchema
from app.lin import DocResponse, Log, db, group_required, permission_meta

log_api = Blueprint("log", __name__)


@log_api.route("")
@permission_meta(name="查询日志", module="日志")
@group_required
@api.validate(
    resp=DocResponse(r=LogPageSchema),
    security=[AuthorizationBearerSecurity],
    tags=["日志"],
)
def get_logs(query: LogQuerySearchSchema):
    """
    日志浏览查询（人员，时间, 关键字），分页展示
    """
    logs = Log.query.filter()
    total = logs.count()
    items = logs.order_by(text("create_time desc")).offset(query.offset).limit(query.count).all()
    total_page = math.ceil(total / query.count)

    return LogPageSchema(
        page=query.page,
        count=query.count,
        total=total,
        items=items,
        total_page=total_page,
    )


@log_api.route("/search")
@permission_meta(name="搜索日志", module="日志")
@group_required
@api.validate(
    resp=DocResponse(r=LogPageSchema),
    security=[AuthorizationBearerSecurity],
    tags=["日志"],
)
def search_logs(query: LogQuerySearchSchema):
    """
    日志搜索（人员，时间, 关键字），分页展示
    """
    if query.keyword:
        logs = Log.query.filter(Log.message.like(f"%{query.keyword}%"))
    else:
        logs = Log.query.filter()
    if query.name:
        logs = logs.filter(Log.username == query.name)
    if query.start and query.end:
        logs = logs.filter(Log.create_time.between(query.start, query.end))

    total = logs.count()
    items = logs.order_by(text("create_time desc")).offset(query.offset).limit(query.count).all()
    total_page = math.ceil(total / query.count)

    return LogPageSchema(
        page=query.page,
        count=query.count,
        total=total,
        items=items,
        total_page=total_page,
    )


@log_api.route("/users")
@permission_meta(name="查询日志记录的用户", module="日志")
@group_required
@api.validate(
    resp=DocResponse(r=UsernameListSchema),
    security=[AuthorizationBearerSecurity],
    tags=["日志"],
)
def get_users_for_log():
    """
    获取所有记录行为日志的用户名
    """
    usernames = (
        db.session.query(Log.username)
        .filter_by(soft=False)
        .group_by(text("username"))
        .having(text("count(username) > 0"))
        .all()
    )
    return UsernameListSchema(items=[u.username for u in usernames])
