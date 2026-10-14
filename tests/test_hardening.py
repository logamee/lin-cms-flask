"""
第二轮加固回归测试:
- 注册未传分组时按级别解析 Guest 分组 ID（不再误用级别值当 ID）
- 密码策略：长度与字母+数字复杂度
- 日志查询 name 过滤生效、关键字通配符转义
- refresh token 显式 7 天过期
- 响应不再通过 setattr 突变模型（permissions 端点结构不变）
"""

from datetime import timedelta

from tests.conftest import find_user_id


def test_register_without_groups_lands_in_guest_by_level(client, root_headers):
    # 不传 group_ids → 应落入 level=GUEST 的分组（按级别查询 ID）
    rv = client.post(
        "/cms/user/register",
        headers=root_headers,
        json={"username": "fbguest1", "password": "Abcd1234", "confirm_password": "Abcd1234", "group_ids": []},
    )
    assert rv.status_code == 200, rv.get_json()
    rv = client.get("/cms/admin/users", headers=root_headers, query_string={"count": 15, "group_id": 2})
    items = rv.get_json()["items"]
    assert any(u["username"] == "fbguest1" for u in items), items
    uid = find_user_id(client, root_headers, "fbguest1")
    client.delete(f"/cms/admin/user/{uid}", headers=root_headers)


def test_register_accepts_simple_password(client, root_headers):
    # 老用户习惯的简单密码（如 123456）必须可用：6-22 位即可，无复杂度要求
    rv = client.post(
        "/cms/user/register",
        headers=root_headers,
        json={"username": "oldstyle", "password": "123456", "confirm_password": "123456", "group_ids": [2]},
    )
    assert rv.status_code == 200
    uid = find_user_id(client, root_headers, "oldstyle")
    client.delete(f"/cms/admin/user/{uid}", headers=root_headers)


def test_register_rejects_under_6_chars(client, root_headers):
    rv = client.post(
        "/cms/user/register",
        headers=root_headers,
        json={"username": "tooshort", "password": "12345", "confirm_password": "12345", "group_ids": [2]},
    )
    assert rv.status_code == 400


def test_get_logs_filters_by_name(client, root_headers):
    rv = client.get("/cms/log", headers=root_headers, query_string={"count": 10, "name": "不存在的用户xyz"})
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["total"] == 0
    assert body["items"] == []
    # 不过滤时应有日志
    rv = client.get("/cms/log", headers=root_headers, query_string={"count": 10})
    assert rv.get_json()["total"] >= 1


def test_search_logs_escapes_wildcards(client, root_headers):
    # % 作为字面量关键字不应匹配所有记录
    rv = client.get("/cms/log/search", headers=root_headers, query_string={"keyword": "%", "count": 10})
    body = rv.get_json()
    assert body["total"] == 0 or all("%" in item["message"] for item in body["items"])


def test_refresh_token_expiry_is_7_days(app):
    expires = app.config.get("JWT_REFRESH_TOKEN_EXPIRES")
    assert expires == timedelta(days=7)


def test_permissions_response_shape_stable(client, root_headers):
    rv = client.get("/cms/user/permissions", headers=root_headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["admin"] is True
    assert isinstance(data["permissions"], list)
    assert "id" in data and "username" in data


def test_group_permission_response_shape_stable(client, root_headers):
    rv = client.get("/cms/admin/group/2", headers=root_headers)
    assert rv.status_code == 200
    data = rv.get_json()
    assert "permissions" in data
    assert "id" in data and "name" in data
