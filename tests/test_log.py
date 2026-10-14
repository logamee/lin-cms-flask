"""
日志:分页浏览、关键字/用户名搜索、记录者清单。
日志为挂载权限,模块级固件先行把"日志"权限分发给 Root 组。
"""

import pytest

from tests.conftest import login, permission_ids_by_module


@pytest.fixture(scope="module", autouse=True)
def _grant_log_permission(app):
    # module 级固件不能依赖 function 级固件，此处自行登录获取一次性令牌
    with app.test_client() as c:
        auth = login(c, "root", "123456")
        headers = {"Authorization": "Bearer " + auth["access_token"]}
        permission_ids = permission_ids_by_module(c, headers, "日志")
        rv = c.post(
            "/cms/admin/permission/dispatch/batch",
            headers=headers,
            json={"group_id": 1, "permission_ids": permission_ids},
        )
        assert rv.status_code == 200


def test_get_logs_page(client, root_headers):
    rv = client.get("/cms/log", headers=root_headers, query_string={"count": 5, "page": 0})
    assert rv.status_code == 200
    data = rv.get_json()
    assert {"items", "count", "page", "total", "total_page"} <= set(data)
    assert data["count"] == 5
    # 登录固件已产生行为日志
    assert data["total"] >= 1
    assert {"message", "username", "method", "path"} <= set(data["items"][0])


def test_search_logs_by_keyword(client, root_headers):
    rv = client.get("/cms/log/search", headers=root_headers, query_string={"keyword": "登录"})
    assert rv.status_code == 200
    assert rv.get_json()["total"] >= 1


def test_search_logs_by_name(client, root_headers):
    rv = client.get("/cms/log/search", headers=root_headers, query_string={"name": "root"})
    assert rv.status_code == 200
    assert rv.get_json()["total"] >= 1
    assert all(item["username"] == "root" for item in rv.get_json()["items"])


def test_log_users(client, root_headers):
    rv = client.get("/cms/log/users", headers=root_headers)
    assert rv.status_code == 200
    usernames = rv.get_json()["items"]
    assert "root" in usernames
