import math
from typing import Any, Optional

from flask import Blueprint
from sqlalchemy import text
from sqlalchemy.orm import Query as BaseQuery

from app.api import AuthorizationBearerSecurity, api
from app.api.cms.schema.log import LogPageSchema, LogQuerySearchSchema, UsernameListSchema
from app.lin import DocResponse, Log, db, group_required, permission_meta

log_api = Blueprint("log", __name__)


def _apply_log_filters(
    logs: BaseQuery,
    keyword: Optional[str] = None,
    name: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> BaseQuery:
    """按关键字（转义通配符）、用户名、时间范围过滤日志查询。"""
    if keyword:
        logs = logs.filter(Log.message.contains(keyword, autoescape=True))
    if name:
        logs = logs.filter(Log.username == name)
    if start and end:
        logs = logs.filter(Log.create_time.between(start, end))
    return logs


def _page_logs(query: LogQuerySearchSchema, **filters: Any) -> dict:
    logs = _apply_log_filters(Log.query.filter(), **filters)
    total = logs.count()
    items = logs.order_by(text("create_time desc")).offset(query.offset).limit(query.count).all()
    return {
        "page": query.page,
        "count": query.count,
        "total": total,
        "items": items,
        "total_page": math.ceil(total / query.count),
    }


@log_api.route("")
@permission_meta(name="查询日志", module="日志")
@group_required
@api.validate(
    resp=DocResponse(r=LogPageSchema),
    security=[AuthorizationBearerSecurity],
    tags=["日志"],
)
def get_logs(query: LogQuerySearchSchema) -> dict:
    """
    日志浏览查询（人员，时间），分页展示
    """
    return _page_logs(query, name=query.name, start=query.start, end=query.end)


@log_api.route("/search")
@permission_meta(name="搜索日志", module="日志")
@group_required
@api.validate(
    resp=DocResponse(r=LogPageSchema),
    security=[AuthorizationBearerSecurity],
    tags=["日志"],
)
def search_logs(query: LogQuerySearchSchema) -> dict:
    """
    日志搜索（人员，时间, 关键字），分页展示
    """
    return _page_logs(query, keyword=query.keyword, name=query.name, start=query.start, end=query.end)


@log_api.route("/users")
@permission_meta(name="查询日志记录的用户", module="日志")
@group_required
@api.validate(
    resp=DocResponse(r=UsernameListSchema),
    security=[AuthorizationBearerSecurity],
    tags=["日志"],
)
def get_users_for_log() -> dict:
    """
    获取所有记录行为日志的用户名
    """
    usernames: list = (
        db.session.query(Log.username)
        .filter_by(soft=False)
        .group_by(text("username"))
        .having(text("count(username) > 0"))
        .all()
    )
    return {"items": [u.username for u in usernames]}
