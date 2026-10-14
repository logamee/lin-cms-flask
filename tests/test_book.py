"""
图书 CRUD 全流程:创建(需登录)、公开查询/搜索、更新、删除(挂载权限)。
用例内部自闭环,不依赖执行顺序。
"""

from tests.conftest import BOOK_PAYLOAD


def test_book_crud_flow(client, root_headers, guest_headers):
    # 创建
    rv = client.post("/v1/book", headers=root_headers, json=BOOK_PAYLOAD)
    assert rv.status_code == 200
    assert rv.get_json()["code"] == 12

    # 列表与详情(公开接口)
    rv = client.get("/v1/book")
    assert rv.status_code == 200
    book = next(b for b in rv.get_json() if b["title"] == BOOK_PAYLOAD["title"])
    bid = book["id"]

    rv = client.get(f"/v1/book/{bid}")
    assert rv.status_code == 200
    assert rv.get_json()["author"] == BOOK_PAYLOAD["author"]

    # 搜索
    rv = client.get("/v1/book/search", query_string={"q": "测试驱动"})
    assert rv.status_code == 200
    assert any(b["id"] == bid for b in rv.get_json())

    # 更新
    rv = client.put(f"/v1/book/{bid}", headers=root_headers, json={**BOOK_PAYLOAD, "title": "重构"})
    assert rv.status_code == 200
    assert client.get(f"/v1/book/{bid}").get_json()["title"] == "重构"

    # 删除是挂载权限:未授权分组(guest)被拒;超级管理员旁路直接删除
    rv = client.delete(f"/v1/book/{bid}", headers=guest_headers)
    assert rv.status_code == 401

    rv = client.delete(f"/v1/book/{bid}", headers=root_headers)
    assert rv.status_code == 200

    rv = client.get(f"/v1/book/{bid}")
    assert rv.status_code == 404


def test_book_create_requires_login(client):
    rv = client.post("/v1/book", json=BOOK_PAYLOAD)
    assert rv.status_code == 401


def test_book_missing_404(client):
    rv = client.get("/v1/book/99999")
    assert rv.status_code == 404
